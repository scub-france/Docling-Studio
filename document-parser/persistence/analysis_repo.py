"""Analysis job repository — SQLite CRUD for analysis_jobs table."""

from __future__ import annotations

from datetime import datetime

from domain.models import AnalysisJob, AnalysisStatus
from persistence.database import get_connection


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO-format datetime string back into a datetime object."""
    if not value:
        return None
    return datetime.fromisoformat(value)


def _row_to_job(row) -> AnalysisJob:
    keys = row.keys()
    return AnalysisJob(
        id=row["id"],
        document_id=row["document_id"],
        status=AnalysisStatus(row["status"]),
        content_markdown=row["content_markdown"],
        content_html=row["content_html"],
        pages_json=row["pages_json"],
        document_json=row["document_json"] if "document_json" in keys else None,
        chunks_json=row["chunks_json"] if "chunks_json" in keys else None,
        error_message=row["error_message"],
        started_at=_parse_dt(row["started_at"]),
        completed_at=_parse_dt(row["completed_at"]),
        created_at=_parse_dt(row["created_at"]) or datetime.now(),
        document_filename=row["filename"] if "filename" in keys else None,
    )


_SELECT_WITH_DOC = """
    SELECT aj.*, d.filename
    FROM analysis_jobs aj
    JOIN documents d ON d.id = aj.document_id
"""


async def insert(job: AnalysisJob) -> None:
    async with get_connection() as db:
        await db.execute(
            """INSERT INTO analysis_jobs (id, document_id, status, created_at)
               VALUES (?, ?, ?, ?)""",
            (job.id, job.document_id, job.status.value, str(job.created_at)),
        )
        await db.commit()


async def find_all(*, limit: int = 200, offset: int = 0) -> list[AnalysisJob]:
    async with get_connection() as db:
        cursor = await db.execute(
            f"{_SELECT_WITH_DOC} ORDER BY aj.created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_job(r) for r in rows]


async def find_by_id(job_id: str) -> AnalysisJob | None:
    async with get_connection() as db:
        cursor = await db.execute(f"{_SELECT_WITH_DOC} WHERE aj.id = ?", (job_id,))
        row = await cursor.fetchone()
        return _row_to_job(row) if row else None


async def update_status(job: AnalysisJob) -> None:
    async with get_connection() as db:
        await db.execute(
            """UPDATE analysis_jobs
               SET status = ?, content_markdown = ?, content_html = ?,
                   pages_json = ?, document_json = ?, chunks_json = ?,
                   error_message = ?, started_at = ?, completed_at = ?
               WHERE id = ?""",
            (
                job.status.value,
                job.content_markdown,
                job.content_html,
                job.pages_json,
                job.document_json,
                job.chunks_json,
                job.error_message,
                str(job.started_at) if job.started_at else None,
                str(job.completed_at) if job.completed_at else None,
                job.id,
            ),
        )
        await db.commit()


async def update_chunks(job_id: str, chunks_json: str) -> bool:
    """Update only the chunks_json column for a completed analysis."""
    async with get_connection() as db:
        cursor = await db.execute(
            "UPDATE analysis_jobs SET chunks_json = ? WHERE id = ?",
            (chunks_json, job_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete(job_id: str) -> bool:
    async with get_connection() as db:
        cursor = await db.execute("DELETE FROM analysis_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return cursor.rowcount > 0


async def delete_by_document(document_id: str) -> int:
    """Delete all analysis jobs for a given document. Returns count deleted."""
    async with get_connection() as db:
        cursor = await db.execute("DELETE FROM analysis_jobs WHERE document_id = ?", (document_id,))
        await db.commit()
        return cursor.rowcount
