"""Document edit repository — append-only command log for document_json edits."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from domain.models import DocumentEdit
from domain.value_objects import DocumentEditAction, DocumentEditStatus
from persistence.database import get_connection


def _parse_iso(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _row_to_edit(row) -> DocumentEdit:
    return DocumentEdit(
        id=row["id"],
        document_id=row["document_id"],
        analysis_id=row["analysis_id"],
        action=DocumentEditAction(row["action"]),
        target_ref=row["target_ref"],
        payload=json.loads(row["payload_json"]) if row["payload_json"] else {},
        actor=row["actor"],
        at=_parse_iso(row["at"]) or datetime.now(UTC),
        status=DocumentEditStatus(row["status"]),
    )


class SqliteDocumentEditRepository:
    async def insert(self, edit: DocumentEdit) -> None:
        async with get_connection() as db:
            await db.execute(
                """INSERT INTO document_edits
                   (id, document_id, analysis_id, action, target_ref,
                    payload_json, actor, at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    edit.id,
                    edit.document_id,
                    edit.analysis_id,
                    edit.action.value,
                    edit.target_ref,
                    json.dumps(edit.payload),
                    edit.actor,
                    str(edit.at),
                    edit.status.value,
                ),
            )
            await db.commit()

    async def find_pending_for_document(self, document_id: str) -> list[DocumentEdit]:
        async with get_connection() as db:
            cursor = await db.execute(
                """SELECT * FROM document_edits
                   WHERE document_id = ? AND status = 'pending'
                   ORDER BY at ASC""",
                (document_id,),
            )
            rows = await cursor.fetchall()
            return [_row_to_edit(row) for row in rows]

    async def mark_committed(self, edit_ids: list[str]) -> int:
        if not edit_ids:
            return 0
        placeholders = ", ".join("?" for _ in edit_ids)
        async with get_connection() as db:
            cursor = await db.execute(
                f"UPDATE document_edits SET status = 'committed' WHERE id IN ({placeholders})",
                tuple(edit_ids),
            )
            await db.commit()
            return cursor.rowcount

    async def clear_pending_for_document(self, document_id: str) -> int:
        async with get_connection() as db:
            cursor = await db.execute(
                "DELETE FROM document_edits WHERE document_id = ? AND status = 'pending'",
                (document_id,),
            )
            await db.commit()
            return cursor.rowcount
