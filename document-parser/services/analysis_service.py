"""Analysis service — async document parsing orchestration.

Uses an injected DocumentConverter (port) so the service is decoupled
from the conversion implementation (local Docling lib vs remote Docling Serve).
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import math
import re
from dataclasses import asdict
from typing import TYPE_CHECKING

import pypdfium2 as pdfium

from domain.models import AnalysisJob, AnalysisStatus
from domain.value_objects import (
    ChunkingOptions,
    ChunkResult,
    ConversionOptions,
    ConversionResult,
    PageDetail,
)
from infra.settings import settings

if TYPE_CHECKING:
    from domain.ports import DocumentChunker, DocumentConverter
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)


def _chunk_to_dict(c: ChunkResult) -> dict:
    """Serialize ChunkResult to a camelCase dict matching the frontend API contract."""
    return {
        "text": c.text,
        "headings": c.headings,
        "sourcePage": c.source_page,
        "tokenCount": c.token_count,
        "bboxes": [{"page": b.page, "bbox": b.bbox} for b in c.bboxes],
    }


# Maximum number of concurrent analysis jobs to prevent resource exhaustion.
_DEFAULT_MAX_CONCURRENT = 3

# Regex to extract <body> content from Docling's well-formed HTML output.
_BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL | re.IGNORECASE)


def _count_pdf_pages(file_path: str) -> int:
    """Count pages in a PDF. Returns 0 if the file is not a valid PDF."""
    try:
        pdf = pdfium.PdfDocument(file_path)
        count = len(pdf)
        pdf.close()
        return count
    except Exception:
        logger.debug("Cannot open %s as PDF, batching disabled", file_path)
        return 0


def _extract_html_body(html: str) -> str:
    """Extract content between <body> tags.

    Docling produces well-formed HTML — regex is safe for this controlled output.
    Returns raw html as fallback if no <body> tag is found.
    """
    match = _BODY_RE.search(html)
    return match.group(1).strip() if match else html


def _merge_results(results: list[ConversionResult]) -> ConversionResult:
    """Merge multiple batch ConversionResults into a single consolidated result.

    document_json is intentionally set to None: merging DoclingDocument's internal
    tree structure across batches is error-prone. Re-chunking is disabled for
    batched conversions (robustness decision for 0.3.1).
    """
    if not results:
        return ConversionResult(page_count=0, content_markdown="", content_html="", pages=[])

    all_pages: list[PageDetail] = []
    all_md: list[str] = []
    html_bodies: list[str] = []
    total_skipped = 0

    for r in results:
        all_pages.extend(r.pages)
        all_md.append(r.content_markdown)
        html_bodies.append(_extract_html_body(r.content_html))
        total_skipped += r.skipped_items

    merged_body = "\n".join(html_bodies)
    merged_html = (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{merged_body}</body></html>'
    )

    return ConversionResult(
        page_count=sum(r.page_count for r in results),
        content_markdown="\n\n".join(all_md),
        content_html=merged_html,
        pages=all_pages,
        skipped_items=total_skipped,
        document_json=None,
    )


class AnalysisService:
    """Orchestrates document analysis using an injected converter."""

    def __init__(
        self,
        converter: DocumentConverter,
        chunker: DocumentChunker | None = None,
        conversion_timeout: int = 600,
        max_concurrent: int = _DEFAULT_MAX_CONCURRENT,
    ):
        self._converter = converter
        self._chunker = chunker
        self._conversion_timeout = conversion_timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: dict[str, asyncio.Task] = {}

    async def create(
        self,
        document_id: str,
        *,
        pipeline_options: dict | None = None,
        chunking_options: dict | None = None,
    ) -> AnalysisJob:
        """Create a new analysis job and launch background processing."""
        doc = await document_repo.find_by_id(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        job = AnalysisJob(document_id=document_id)
        job.document_filename = doc.filename
        await analysis_repo.insert(job)

        task = asyncio.create_task(
            self._run_analysis(
                job.id,
                doc.storage_path,
                doc.filename,
                pipeline_options,
                chunking_options,
            )
        )
        self._running_tasks[job.id] = task
        task.add_done_callback(functools.partial(self._on_task_done, job_id=job.id))

        return job

    async def find_all(self) -> list[AnalysisJob]:
        """Return all analysis jobs, newest first."""
        return await analysis_repo.find_all()

    async def find_by_id(self, job_id: str) -> AnalysisJob | None:
        """Find an analysis job by ID, or return None."""
        return await analysis_repo.find_by_id(job_id)

    async def delete(self, job_id: str) -> bool:
        """Delete an analysis job, cancelling any running task. Returns True if it existed."""
        task = self._running_tasks.pop(job_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled running task for job %s", job_id)
        return await analysis_repo.delete(job_id)

    async def rechunk(self, job_id: str, chunking_options: dict) -> list[ChunkResult]:
        """Re-chunk an existing completed analysis with new options."""
        job = await analysis_repo.find_by_id(job_id)
        if not job:
            raise ValueError(f"Analysis not found: {job_id}")
        if job.status != AnalysisStatus.COMPLETED:
            raise ValueError(f"Analysis is not completed: {job_id}")
        if not job.document_json:
            raise ValueError(f"No document data available for re-chunking: {job_id}")
        if not self._chunker:
            raise ValueError("Chunking is not available")

        options = ChunkingOptions(**chunking_options)
        chunks = await self._chunker.chunk(job.document_json, options)

        chunks_json = json.dumps([_chunk_to_dict(c) for c in chunks])
        await analysis_repo.update_chunks(job_id, chunks_json)

        return chunks

    async def _run_batched_conversion(
        self,
        job_id: str,
        file_path: str,
        options: ConversionOptions,
        total_pages: int,
        batch_size: int,
    ) -> ConversionResult | None:
        """Convert a document in batches using page_range.

        Returns None if the job was deleted mid-batch (caller should abort).
        Raises on batch failure (fail-fast: entire job fails).
        """
        num_batches = math.ceil(total_pages / batch_size)
        await analysis_repo.update_progress(job_id, 0, total_pages)
        logger.info(
            "Batched conversion: %d pages in %d batches of %d for job %s",
            total_pages,
            num_batches,
            batch_size,
            job_id,
        )

        results: list[ConversionResult] = []
        for batch_idx in range(num_batches):
            start = batch_idx * batch_size + 1
            end = min(start + batch_size - 1, total_pages)

            if not await analysis_repo.find_by_id(job_id):
                logger.info(
                    "Job %s deleted during batch %d/%d, aborting",
                    job_id,
                    batch_idx + 1,
                    num_batches,
                )
                return None

            try:
                batch_result = await asyncio.wait_for(
                    self._converter.convert(file_path, options, page_range=(start, end)),
                    timeout=self._conversion_timeout,
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Batch {batch_idx + 1}/{num_batches} (pages {start}-{end}) failed: {exc}"
                ) from exc

            results.append(batch_result)
            await analysis_repo.update_progress(job_id, end, total_pages)
            logger.info(
                "Batch %d/%d done (pages %d-%d) for job %s",
                batch_idx + 1,
                num_batches,
                start,
                end,
                job_id,
            )

        return _merge_results(results)

    def _on_task_done(self, task: asyncio.Task, *, job_id: str) -> None:
        """Cleanup running tasks and delegate to module-level handler."""
        self._running_tasks.pop(job_id, None)
        _on_task_done(task, job_id=job_id)

    async def _run_analysis(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        pipeline_options: dict | None = None,
        chunking_options: dict | None = None,
    ) -> None:
        """Background task: run conversion and optionally chunk.

        Acquires the concurrency semaphore to limit parallel conversions
        and prevent CPU/memory exhaustion on modest hardware.
        """
        async with self._semaphore:
            await self._run_analysis_inner(
                job_id, file_path, filename, pipeline_options, chunking_options
            )

    async def _run_analysis_inner(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        pipeline_options: dict | None = None,
        chunking_options: dict | None = None,
    ) -> None:
        """Inner analysis logic — called under the concurrency semaphore."""
        try:
            job = await analysis_repo.find_by_id(job_id)
            if not job:
                logger.error("Analysis job %s not found", job_id)
                return

            job.mark_running()
            await analysis_repo.update_status(job)
            logger.info("Analysis started: %s (file: %s)", job_id, filename)

            opts_dict = pipeline_options or {}
            if "table_mode" not in opts_dict:
                opts_dict = {**opts_dict, "table_mode": settings.default_table_mode}
            options = ConversionOptions(**opts_dict)

            total_pages = _count_pdf_pages(file_path)
            batch_size = settings.batch_page_size

            if batch_size > 0 and total_pages > batch_size:
                result = await self._run_batched_conversion(
                    job_id,
                    file_path,
                    options,
                    total_pages,
                    batch_size,
                )
                if result is None:
                    return  # job was deleted mid-batch
            else:
                result = await asyncio.wait_for(
                    self._converter.convert(file_path, options),
                    timeout=self._conversion_timeout,
                )

            pages_json = json.dumps([asdict(p) for p in result.pages])

            chunks_json = None
            if chunking_options and self._chunker and result.document_json:
                chunk_opts = ChunkingOptions(**chunking_options)
                chunks = await self._chunker.chunk(result.document_json, chunk_opts)
                chunks_json = json.dumps([_chunk_to_dict(c) for c in chunks])
                logger.info("Chunking produced %d chunks for job %s", len(chunks), job_id)

            # Re-read the job so we don't lose progress_current/progress_total
            # written to the DB during batched conversion.
            job = await analysis_repo.find_by_id(job_id) or job
            job.mark_completed(
                markdown=result.content_markdown,
                html=result.content_html,
                pages_json=pages_json,
                document_json=result.document_json,
                chunks_json=chunks_json,
            )
            await analysis_repo.update_status(job)

            if result.page_count:
                await document_repo.update_page_count(job.document_id, result.page_count)

            logger.info("Analysis completed: %s (%d pages)", job_id, result.page_count)

        except TimeoutError:
            logger.error("Analysis timed out after %ds: %s", self._conversion_timeout, job_id)
            await _mark_failed(job_id, f"Conversion timed out after {self._conversion_timeout}s")

        except Exception as e:
            logger.exception("Analysis failed: %s", job_id)
            await _mark_failed(job_id, _classify_error(e))


def _classify_error(exc: Exception) -> str:
    """Return a user-friendly error message based on the exception type/content."""
    msg = str(exc).lower()

    if "invalidcxxcompiler" in msg or "no working c++ compiler" in msg:
        return "Missing C++ compiler — set TORCHDYNAMO_DISABLE=1 to work around this"

    if "out of memory" in msg or "oom" in msg:
        return "Out of memory — try a smaller document or disable table structure analysis"

    if "could not acquire converter lock" in msg:
        return "Server busy — a previous conversion is still running. Please retry later"

    if "pipeline" in msg and "failed" in msg:
        return "Document processing failed — the document may be corrupted or unsupported"

    if "timeout" in msg:
        return "Processing took too long — try with fewer pages or simpler options"

    # Fallback: truncate raw error to something reasonable
    raw = str(exc)
    if len(raw) > 200:
        raw = raw[:200] + "…"
    return raw


_background_tasks: set[asyncio.Task] = set()


def _on_task_done(task: asyncio.Task, *, job_id: str) -> None:
    """Log unhandled exceptions from background analysis tasks and mark job as FAILED."""
    if task.cancelled():
        logger.warning("Analysis task was cancelled: %s", job_id)
        _schedule_mark_failed(job_id, "Task was cancelled")
        return
    exc = task.exception()
    if exc:
        logger.error("Unhandled exception in analysis task %s: %s", job_id, exc, exc_info=True)
        _schedule_mark_failed(job_id, _classify_error(exc))


# Keep the module-level function as the default, but AnalysisService uses its own method.


def _schedule_mark_failed(job_id: str, error: str) -> None:
    """Schedule _mark_failed as a tracked background task."""
    t = asyncio.ensure_future(_mark_failed(job_id, error))
    _background_tasks.add(t)
    t.add_done_callback(_background_tasks.discard)


async def _mark_failed(job_id: str, error: str) -> None:
    """Safely mark a job as failed, handling DB errors gracefully."""
    try:
        job = await analysis_repo.find_by_id(job_id)
        if job:
            job.mark_failed(error)
            await analysis_repo.update_status(job)
    except OSError:
        logger.exception("Database I/O error marking job %s as failed", job_id)
    except Exception:
        logger.exception("Unexpected error marking job %s as failed", job_id)
