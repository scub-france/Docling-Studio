"""Analysis service — async document parsing orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict

from domain.models import AnalysisJob
from domain.parsing import ConversionResult, convert_document
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)


async def create(document_id: str, *, pipeline_options: dict | None = None) -> AnalysisJob:
    """Create a new analysis job and launch background processing."""
    doc = await document_repo.find_by_id(document_id)
    if not doc:
        raise ValueError(f"Document not found: {document_id}")

    job = AnalysisJob(document_id=document_id)
    job.document_filename = doc.filename
    await analysis_repo.insert(job)

    # Fire-and-forget background task
    asyncio.create_task(_run_analysis(job.id, doc.storage_path, doc.filename, pipeline_options))

    return job


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
    job = await analysis_repo.find_by_id(job_id)
    if not job:
        logger.error("Analysis job %s not found", job_id)
        return

    job.mark_running()
    await analysis_repo.update_status(job)
    logger.info("Analysis started: %s (file: %s)", job_id, filename)

    try:
        # Build kwargs from pipeline options
        convert_kwargs = pipeline_options or {}

        # Run blocking Docling conversion in a thread
        result: ConversionResult = await asyncio.to_thread(
            convert_document, file_path, **convert_kwargs,
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

    except Exception as e:
        logger.exception("Analysis failed: %s", job_id)
        job.mark_failed(str(e))
        await analysis_repo.update_status(job)
