"""Analysis API router — create, list, get, delete analysis jobs."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from api.schemas import AnalysisResponse, CreateAnalysisRequest
from services import analysis_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def _to_response(job) -> AnalysisResponse:
    return AnalysisResponse(
        id=job.id,
        document_id=job.document_id,
        document_filename=job.document_filename,
        status=job.status.value,
        content_markdown=job.content_markdown,
        content_html=job.content_html,
        pages_json=job.pages_json,
        error_message=job.error_message,
        started_at=str(job.started_at) if job.started_at else None,
        completed_at=str(job.completed_at) if job.completed_at else None,
        created_at=str(job.created_at),
    )


@router.post("", response_model=AnalysisResponse)
async def create_analysis(body: CreateAnalysisRequest):
    """Create a new analysis job for a document."""
    if not body.documentId or not body.documentId.strip():
        raise HTTPException(status_code=400, detail="documentId is required")

    pipeline_opts = None
    if body.pipelineOptions:
        pipeline_opts = body.pipelineOptions.model_dump()

    try:
        job = await analysis_service.create(body.documentId, pipeline_options=pipeline_opts)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _to_response(job)


@router.get("", response_model=list[AnalysisResponse])
async def list_analyses():
    """List all analysis jobs."""
    jobs = await analysis_service.find_all()
    return [_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=AnalysisResponse)
async def get_analysis(job_id: str):
    """Get a single analysis job."""
    job = await analysis_service.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_response(job)


@router.delete("/{job_id}", status_code=204)
async def delete_analysis(job_id: str):
    """Delete an analysis job."""
    deleted = await analysis_service.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
