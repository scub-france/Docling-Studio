"""Ingestion API — REST endpoints for the embedding → OpenSearch pipeline.

Routes:
    POST   /api/ingestion/{job_id}   — Trigger ingestion for a completed analysis
    DELETE /api/ingestion/{doc_id}   — Remove indexed chunks for a document
    GET    /api/ingestion/status     — Check whether the ingestion pipeline is available
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class IngestionResponse(BaseModel):
    doc_id: str
    chunks_indexed: int
    embedding_dimension: int

    model_config = {"populate_by_name": True}


class IngestionStatusResponse(BaseModel):
    available: bool
    reason: str = ""


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_ingestion_service(request: Request):
    svc = getattr(request.app.state, "ingestion_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion pipeline not available (OpenSearch or embedding service not configured).",
        )
    return svc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(request: Request) -> IngestionStatusResponse:
    """Return whether the ingestion pipeline (OpenSearch + embedding) is available."""
    svc = getattr(request.app.state, "ingestion_service", None)
    if svc is None:
        return IngestionStatusResponse(
            available=False,
            reason="OpenSearch or embedding service not configured",
        )
    return IngestionStatusResponse(available=True)


@router.post("/{job_id}", response_model=IngestionResponse, status_code=status.HTTP_200_OK)
async def ingest_analysis(job_id: str, request: Request) -> IngestionResponse:
    """Run the full ingestion pipeline for a completed analysis job.

    Chains: loaded chunks → embedding → OpenSearch indexing.
    Idempotent: re-ingesting a document replaces existing indexed chunks.
    """
    svc = _get_ingestion_service(request)
    try:
        from services.ingestion_service import IngestionError

        result = await svc.ingest(job_id)
    except IngestionError as exc:
        logger.warning("Ingestion failed for job %s: %s", job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during ingestion of job %s", job_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion error: {exc}",
        ) from exc

    return IngestionResponse(
        doc_id=result.doc_id,
        chunks_indexed=result.chunks_indexed,
        embedding_dimension=result.embedding_dimension,
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingested(doc_id: str, request: Request) -> None:
    """Remove all indexed chunks for a document from OpenSearch."""
    svc = _get_ingestion_service(request)
    try:
        from services.ingestion_service import IngestionError

        await svc.delete(doc_id)
    except IngestionError as exc:
        logger.warning("Delete failed for document %s: %s", doc_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error deleting chunks for document %s", doc_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete error: {exc}",
        ) from exc
