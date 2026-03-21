"""Analysis service — async document parsing orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict

from domain.models import AnalysisJob
from domain.parsing import ConversionOptions, ConversionResult, convert_document
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)

# Maximum time (seconds) allowed for a single document conversion.
CONVERSION_TIMEOUT = int(__import__("os").environ.get("CONVERSION_TIMEOUT", "600"))


async def create(document_id: str, *, pipeline_options: dict | None = None) -> AnalysisJob:
    """Create a new analysis job and launch background processing."""
    doc = await document_repo.find_by_id(document_id)
    if not doc:
        raise ValueError(f"Document not found: {document_id}")

    job = AnalysisJob(document_id=document_id)
    job.document_filename = doc.filename
    await analysis_repo.insert(job)

    # Fire background task with error logging callback
    task = asyncio.create_task(
        _run_analysis(job.id, doc.storage_path, doc.filename, pipeline_options)
    )
    task.add_done_callback(_on_task_done)

    return job


def _on_task_done(task: asyncio.Task) -> None:
    """Log unhandled exceptions from background analysis tasks."""
    if task.cancelled():
        logger.warning("Analysis task was cancelled")
        return
    exc = task.exception()
    if exc:
        logger.error("Unhandled exception in analysis task: %s", exc, exc_info=True)


async def find_all() -> list[AnalysisJob]:
    return await analysis_repo.find_all()


async def find_by_id(job_id: str) -> AnalysisJob | None:
    return await analysis_repo.find_by_id(job_id)


async def delete(job_id: str) -> bool:
    return await analysis_repo.delete(job_id)


async def _run_analysis(
    job_id: str, file_path: str, filename: str, pipeline_options: dict | None = None,
) -> None:
    """Background task: run Docling conversion and update job status."""
    try:
        job = await analysis_repo.find_by_id(job_id)
        if not job:
            logger.error("Analysis job %s not found", job_id)
            return

        job.mark_running()
        await analysis_repo.update_status(job)
        logger.info("Analysis started: %s (file: %s)", job_id, filename)

        # Build conversion options from pipeline dict
        options = ConversionOptions(**(pipeline_options or {}))

        # Run blocking Docling conversion in a thread with timeout
        result: ConversionResult = await asyncio.wait_for(
            asyncio.to_thread(convert_document, file_path, options),
            timeout=CONVERSION_TIMEOUT,
        )

        pages_json = json.dumps([asdict(p) for p in result.pages])

        job.mark_completed(
            markdown=result.content_markdown,
            html=result.content_html,
            pages_json=pages_json,
        )
        await analysis_repo.update_status(job)

        # Update document page count if available
        if result.page_count:
            await document_repo.update_page_count(job.document_id, result.page_count)

        logger.info("Analysis completed: %s (%d pages)", job_id, result.page_count)

    except asyncio.TimeoutError:
        logger.error("Analysis timed out after %ds: %s", CONVERSION_TIMEOUT, job_id)
        await _mark_failed(job_id, f"Conversion timed out after {CONVERSION_TIMEOUT}s")

    except Exception as e:
        logger.exception("Analysis failed: %s", job_id)
        await _mark_failed(job_id, str(e))


async def _mark_failed(job_id: str, error: str) -> None:
    """Safely mark a job as failed, handling DB errors gracefully."""
    try:
        job = await analysis_repo.find_by_id(job_id)
        if job:
            job.mark_failed(error)
            await analysis_repo.update_status(job)
    except Exception:
        logger.exception("Could not mark job %s as failed", job_id)
