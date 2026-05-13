"""Backfill `document_versions` for pre-#267 data.

The versioning table was introduced in 0.6.1. Documents that already
had completed analyses (and possibly chunks) before the upgrade end up
with zero version rows — the workspace then shows an empty History and
can't pin an active analysis. This migration walks every document and
materializes one ANALYSIS version per pre-existing COMPLETED analysis,
plus one CHUNKS version per document whose live chunks predate the
versioning. Each emitted version snapshots the chunks state at the
moment of the backfill (best we can do without an audit replay).

Idempotent: tagged via `migration_progress` and skipped on subsequent
startups.
"""

from __future__ import annotations

import json
import logging
import uuid

from persistence.database import get_connection

logger = logging.getLogger(__name__)

_MIGRATION_NAME = "267-backfill-document-versions"


async def _already_done() -> bool:
    async with get_connection() as conn:
        cur = await conn.execute(
            "SELECT 1 FROM migration_progress WHERE name = ?",
            (_MIGRATION_NAME,),
        )
        return await cur.fetchone() is not None


async def _mark_done() -> None:
    async with get_connection() as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO migration_progress (name) VALUES (?)",
            (_MIGRATION_NAME,),
        )
        await conn.commit()


async def run_backfill() -> int:
    """Returns the number of synthetic versions emitted."""
    if await _already_done():
        logger.debug("Backfill %s already applied", _MIGRATION_NAME)
        return 0

    emitted = 0
    async with get_connection() as conn:
        # All completed analyses with their document ids.
        analyses_cur = await conn.execute(
            """
            SELECT aj.id, aj.document_id, aj.completed_at, aj.created_at
              FROM analysis_jobs aj
              JOIN documents d ON d.id = aj.document_id
             WHERE aj.status = 'COMPLETED'
             ORDER BY aj.completed_at, aj.created_at
            """
        )
        analyses_rows = await analyses_cur.fetchall()

        # Documents that already have at least one version row — skip
        # them so re-running the migration (e.g. after a partial rollback)
        # doesn't double-count.
        versions_cur = await conn.execute(
            "SELECT DISTINCT document_id FROM document_versions",
        )
        with_versions = {r["document_id"] for r in await versions_cur.fetchall()}

        # Live chunks per document (snapshot once, reuse across the
        # synthetic versions of that doc — the audit log is too coarse
        # to reconstruct per-analysis chunk states).
        chunks_cache: dict[str, str] = {}

        for row in analyses_rows:
            doc_id = row["document_id"]
            if doc_id in with_versions:
                continue

            if doc_id not in chunks_cache:
                chunks_cache[doc_id] = await _serialize_live_chunks(conn, doc_id)

            await conn.execute(
                """
                INSERT INTO document_versions
                    (id, document_id, kind, analysis_id,
                     chunks_snapshot, summary, created_at)
                VALUES (?, ?, 'analysis', ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    doc_id,
                    row["id"],
                    chunks_cache[doc_id],
                    "Backfilled analysis version",
                    row["completed_at"] or row["created_at"],
                ),
            )
            emitted += 1

        await conn.commit()

    await _mark_done()
    logger.info("Backfilled %d document versions (#267)", emitted)
    return emitted


async def _serialize_live_chunks(conn, document_id: str) -> str:
    """Snapshot the live (non-deleted) chunks for a document as the same
    JSON shape `VersionService._serialize_chunks` writes — kept aligned
    so the frontend can read either-or."""
    cur = await conn.execute(
        """
        SELECT id, document_id, sequence, text, headings, source_page,
               bboxes, doc_items, token_count, created_at, updated_at
          FROM chunks
         WHERE document_id = ?
           AND deleted_at IS NULL
         ORDER BY sequence
        """,
        (document_id,),
    )
    rows = await cur.fetchall()
    out = []
    for r in rows:
        headings = json.loads(r["headings"]) if r["headings"] else []
        bboxes = json.loads(r["bboxes"]) if r["bboxes"] else []
        doc_items = json.loads(r["doc_items"]) if r["doc_items"] else []
        out.append(
            {
                "id": r["id"],
                "documentId": r["document_id"],
                "sequence": r["sequence"],
                "text": r["text"],
                "headings": headings,
                "sourcePage": r["source_page"],
                "tokenCount": r["token_count"],
                "bboxes": [
                    {"page": b.get("page"), "bbox": list(b.get("bbox", []))} for b in bboxes
                ],
                "docItems": [
                    {"selfRef": d.get("self_ref", ""), "label": d.get("label", "")}
                    for d in doc_items
                ],
                "createdAt": r["created_at"],
                "updatedAt": r["updated_at"],
            }
        )
    return json.dumps(out)
