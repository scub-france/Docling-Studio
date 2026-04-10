"""Document repository — SQLite CRUD for documents table."""

from __future__ import annotations

from datetime import UTC, datetime

from domain.models import Document
from persistence.database import get_connection


def _row_to_document(row) -> Document:
    created = row["created_at"]
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return Document(
        id=row["id"],
        filename=row["filename"],
        content_type=row["content_type"],
        file_size=row["file_size"],
        page_count=row["page_count"],
        storage_path=row["storage_path"],
        created_at=created,
    )


class SqliteDocumentRepository:
    """SQLite implementation of the DocumentRepository port."""

    async def insert(self, doc: Document) -> None:
        """Persist a new document record."""
        async with get_connection() as db:
            await db.execute(
                """INSERT INTO documents (id, filename, content_type, file_size, page_count, storage_path, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc.id,
                    doc.filename,
                    doc.content_type,
                    doc.file_size,
                    doc.page_count,
                    doc.storage_path,
                    str(doc.created_at),
                ),
            )
            await db.commit()

    async def find_all(self, *, limit: int = 200, offset: int = 0) -> list[Document]:
        """Return documents ordered by creation date (newest first)."""
        async with get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = await cursor.fetchall()
            return [_row_to_document(r) for r in rows]

    async def find_by_id(self, doc_id: str) -> Document | None:
        """Find a document by its ID, or return None."""
        async with get_connection() as db:
            cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = await cursor.fetchone()
            return _row_to_document(row) if row else None

    async def update_page_count(self, doc_id: str, page_count: int) -> None:
        """Update the page count after conversion has determined it."""
        async with get_connection() as db:
            await db.execute(
                "UPDATE documents SET page_count = ? WHERE id = ?",
                (page_count, doc_id),
            )
            await db.commit()

    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID. Returns True if a row was removed."""
        async with get_connection() as db:
            cursor = await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            await db.commit()
            return cursor.rowcount > 0
