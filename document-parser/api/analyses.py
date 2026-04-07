"""Analysis API router — create, list, get, delete analysis jobs."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import (
    AnalysisResponse,
    ChunkBboxResponse,
    ChunkResponse,
    CreateAnalysisRequest,
    RechunkRequest,
)
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def _get_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service


ServiceDep = Annotated[AnalysisService, Depends(_get_service)]


def _to_response(job) -> AnalysisResponse:
    return AnalysisResponse(
        id=job.id,
        document_id=job.document_id,
        document_filename=job.document_filename,
        status=job.status.value,
        content_markdown=job.content_markdown,
        content_html=job.content_html,
        pages_json=job.pages_json,
        chunks_json=job.chunks_json,
        has_document_json=job.document_json is not None,
        error_message=job.error_message,
        started_at=str(job.started_at) if job.started_at else None,
        completed_at=str(job.completed_at) if job.completed_at else None,
        created_at=str(job.created_at),
    )


@router.post("", response_model=AnalysisResponse)
async def create_analysis(body: CreateAnalysisRequest, service: ServiceDep) -> AnalysisResponse:
    """Create a new analysis job for a document."""
    if not body.documentId or not body.documentId.strip():
        raise HTTPException(status_code=400, detail="documentId is required")

    pipeline_opts = None
    if body.pipelineOptions:
        pipeline_opts = body.pipelineOptions.model_dump()

    chunking_opts = None
    if body.chunkingOptions:
        chunking_opts = body.chunkingOptions.model_dump()

    try:
        job = await service.create(
            body.documentId,
            pipeline_options=pipeline_opts,
            chunking_options=chunking_opts,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return _to_response(job)


@router.get("", response_model=list[AnalysisResponse])
async def list_analyses(service: ServiceDep) -> list[AnalysisResponse]:
    """List all analysis jobs."""
    jobs = await service.find_all()
    return [_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=AnalysisResponse)
async def get_analysis(job_id: str, service: ServiceDep) -> AnalysisResponse:
    """Get a single analysis job."""
    job = await service.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_response(job)


@router.post("/{job_id}/rechunk", response_model=list[ChunkResponse])
async def rechunk_analysis(
    job_id: str, body: RechunkRequest, service: ServiceDep
) -> list[ChunkResponse]:
    """Re-chunk a completed analysis with new chunking options."""
    try:
        chunks = await service.rechunk(job_id, body.chunkingOptions.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return [
        ChunkResponse(
            text=c.text,
            headings=c.headings,
            source_page=c.source_page,
            token_count=c.token_count,
            bboxes=[ChunkBboxResponse(page=b.page, bbox=b.bbox) for b in c.bboxes],
        )
        for c in chunks
    ]


@router.delete("/{job_id}", status_code=204)
async def delete_analysis(job_id: str, service: ServiceDep) -> None:
    """Delete an analysis job."""
    deleted = await service.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
