"""Analysis service — async document parsing orchestration.

Uses an injected DocumentConverter (port) so the service is decoupled
from the conversion implementation (local Docling lib vs remote Docling Serve).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from domain.models import AnalysisJob
from domain.value_objects import ConversionOptions, ConversionResult

if TYPE_CHECKING:
    from domain.ports import DocumentConverter
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates document analysis using an injected converter."""

    def __init__(self, converter: DocumentConverter, conversion_timeout: int = 600):
        self._converter = converter
        self._conversion_timeout = conversion_timeout

    async def create(self, document_id: str, *, pipeline_options: dict | None = None) -> AnalysisJob:
        """Create a new analysis job and launch background processing."""
        doc = await document_repo.find_by_id(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        job = AnalysisJob(document_id=document_id)
        job.document_filename = doc.filename
        await analysis_repo.insert(job)

        task = asyncio.create_task(
            self._run_analysis(job.id, doc.storage_path, doc.filename, pipeline_options)
        )
        task.add_done_callback(_on_task_done)

        return job

    async def find_all(self) -> list[AnalysisJob]:
        return await analysis_repo.find_all()

    async def find_by_id(self, job_id: str) -> AnalysisJob | None:
        return await analysis_repo.find_by_id(job_id)

    async def delete(self, job_id: str) -> bool:
        return await analysis_repo.delete(job_id)

    async def _run_analysis(
        self, job_id: str, file_path: str, filename: str, pipeline_options: dict | None = None,
    ) -> None:
        """Background task: run conversion and update job status."""
        try:
            job = await analysis_repo.find_by_id(job_id)
            if not job:
                logger.error("Analysis job %s not found", job_id)
                return

            job.mark_running()
            await analysis_repo.update_status(job)
            logger.info("Analysis started: %s (file: %s)", job_id, filename)

            options = ConversionOptions(**(pipeline_options or {}))

            result: ConversionResult = await asyncio.wait_for(
                self._converter.convert(file_path, options),
                timeout=self._conversion_timeout,
            )

            pages_json = json.dumps([asdict(p) for p in result.pages])

            job.mark_completed(
                markdown=result.content_markdown,
                html=result.content_html,
                pages_json=pages_json,
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
            await _mark_failed(job_id, str(e))


def _on_task_done(task: asyncio.Task) -> None:
    """Log unhandled exceptions from background analysis tasks."""
    if task.cancelled():
        logger.warning("Analysis task was cancelled")
        return
    exc = task.exception()
    if exc:
        logger.error("Unhandled exception in analysis task: %s", exc, exc_info=True)


async def _mark_failed(job_id: str, error: str) -> None:
    """Safely mark a job as failed, handling DB errors gracefully."""
    try:
        job = await analysis_repo.find_by_id(job_id)
        if job:
            job.mark_failed(error)
            await analysis_repo.update_status(job)
    except Exception:
        logger.exception("Could not mark job %s as failed", job_id)
