"""Document service — file upload, storage, and preview orchestration."""

from __future__ import annotations

import io
import logging
import os
import uuid

from pdf2image import convert_from_bytes, pdfinfo_from_bytes

from domain.models import Document
from infra.settings import settings
from persistence import analysis_repo, document_repo

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.upload_dir
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# PDF magic bytes: %PDF
_PDF_MAGIC = b"%PDF"


_UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB chunks for streaming writes


async def upload(filename: str, content_type: str, file_content: bytes) -> Document:
    """Save uploaded file to disk and persist metadata.

    Writes the file in fixed-size chunks to keep peak memory usage low.
    """
    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 50 MB)")

    if not file_content[:4].startswith(_PDF_MAGIC):
        raise ValueError("Invalid file: not a PDF document")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = ".pdf"  # Content already validated as PDF
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Write in chunks to avoid doubling memory usage for large files
    with open(file_path, "wb") as f:
        for offset in range(0, len(file_content), _UPLOAD_CHUNK_SIZE):
            f.write(file_content[offset : offset + _UPLOAD_CHUNK_SIZE])

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
    """Return all documents, newest first."""
    return await document_repo.find_all()


async def find_by_id(doc_id: str) -> Document | None:
    """Find a document by its ID, or return None."""
    return await document_repo.find_by_id(doc_id)


async def delete(doc_id: str) -> bool:
    """Delete document file, associated analyses, and database record."""
    doc = await document_repo.find_by_id(doc_id)
    if not doc:
        return False

    # Delete associated analyses first (cascade)
    await analysis_repo.delete_by_document(doc_id)

    # Delete file from disk (only if inside UPLOAD_DIR)
    try:
        real_path = os.path.realpath(doc.storage_path)
        real_upload_dir = os.path.realpath(UPLOAD_DIR)
        if real_path.startswith(real_upload_dir + os.sep) and os.path.exists(real_path):
            os.unlink(real_path)
        elif os.path.exists(doc.storage_path):
            logger.warning("Refused to delete file outside upload dir: %s", doc.storage_path)
    except FileNotFoundError:
        logger.info("File already removed: %s", doc.storage_path)
    except PermissionError:
        logger.error("Permission denied deleting file: %s", doc.storage_path)
    except OSError:
        logger.warning("Could not delete file: %s", doc.storage_path, exc_info=True)

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
    except (FileNotFoundError, OSError) as exc:
        logger.warning("Could not count pages: %s", exc)
        return None
    except Exception:
        logger.warning("Unexpected error counting pages", exc_info=True)
        return None
