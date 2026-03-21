"""Document service — file upload, storage, and preview orchestration."""

from __future__ import annotations

import io
import logging
import os
import uuid

from pdf2image import convert_from_bytes, pdfinfo_from_bytes

from domain.models import Document
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# PDF magic bytes: %PDF
_PDF_MAGIC = b"%PDF"


async def upload(filename: str, content_type: str, file_content: bytes) -> Document:
    """Save uploaded file to disk and persist metadata."""
    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 50 MB)")

    if not file_content[:4].startswith(_PDF_MAGIC):
        raise ValueError("Invalid file: not a PDF document")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(filename)[1] or ".pdf"
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    # Count PDF pages
    page_count = _count_pages(file_content)

    doc = Document(
        filename=filename,
        content_type=content_type,
        file_size=len(file_content),
        page_count=page_count,
        storage_path=os.path.abspath(file_path),
    )
    await document_repo.insert(doc)
    return doc


async def find_all() -> list[Document]:
    return await document_repo.find_all()


async def find_by_id(doc_id: str) -> Document | None:
    return await document_repo.find_by_id(doc_id)


async def delete(doc_id: str) -> bool:
    """Delete document file, associated analyses, and database record."""
    doc = await document_repo.find_by_id(doc_id)
    if not doc:
        return False

    # Delete associated analyses first (cascade)
    await analysis_repo.delete_by_document(doc_id)

    # Delete file from disk
    try:
        if os.path.exists(doc.storage_path):
            os.unlink(doc.storage_path)
    except OSError:
        logger.warning("Could not delete file: %s", doc.storage_path)

    return await document_repo.delete(doc_id)


def generate_preview(file_content: bytes, page: int = 1, dpi: int = 150) -> bytes:
    """Generate a PNG preview of a specific PDF page."""
    images = convert_from_bytes(file_content, first_page=page, last_page=page, dpi=dpi)
    if not images:
        raise ValueError(f"Page {page} not found")

    buf = io.BytesIO()
    images[0].save(buf, format="PNG")
    return buf.getvalue()


def _count_pages(file_content: bytes) -> int | None:
    """Count PDF pages using poppler via pdf2image."""
    try:
        info = pdfinfo_from_bytes(file_content)
        return info.get("Pages")
    except Exception:
        logger.warning("Could not count pages", exc_info=True)
        return None
