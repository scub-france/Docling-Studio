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


async def insert(doc: Document) -> None:
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


async def find_all(*, limit: int = 200, offset: int = 0) -> list[Document]:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_document(r) for r in rows]


async def find_by_id(doc_id: str) -> Document | None:
    async with get_connection() as db:
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return _row_to_document(row) if row else None


async def update_page_count(doc_id: str, page_count: int) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE documents SET page_count = ? WHERE id = ?",
            (page_count, doc_id),
        )
        await db.commit()


async def delete(doc_id: str) -> bool:
    async with get_connection() as db:
        cursor = await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await db.commit()
        return cursor.rowcount > 0
