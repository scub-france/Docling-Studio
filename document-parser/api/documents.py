"""Document API router — upload, list, get, delete, preview."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import Response

from api.schemas import DocumentResponse
from services import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


def _to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        content_type=doc.content_type,
        file_size=doc.file_size,
        page_count=doc.page_count,
        created_at=str(doc.created_at),
    )


@router.post("/upload", response_model=DocumentResponse)
async def upload(file: UploadFile):
    """Upload a PDF document."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()

    try:
        doc = await document_service.upload(
            filename=file.filename,
            content_type=file.content_type or "application/pdf",
            file_content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    return _to_response(doc)


@router.get("", response_model=list[DocumentResponse])
async def list_documents():
    """List all documents."""
    docs = await document_service.find_all()
    return [_to_response(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get a single document."""
    doc = await document_service.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_response(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str):
    """Delete a document and its file."""
    deleted = await document_service.delete(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{doc_id}/preview")
async def preview(
    doc_id: str,
    page: int = Query(1, ge=1),
    dpi: int = Query(150, ge=72, le=300),
):
    """Generate a PNG preview of a specific PDF page."""
    doc = await document_service.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        with open(doc.storage_path, "rb") as f:
            file_content = f.read()
        png_bytes = document_service.generate_preview(file_content, page=page, dpi=dpi)
        return Response(content=png_bytes, media_type="image/png")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to generate preview")
        raise HTTPException(status_code=422, detail="Failed to generate preview")
