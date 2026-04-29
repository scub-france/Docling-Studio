"""0.6.0 migration — backfill the doc-centric data model.

Run after deploying the 0.6.0 release code, before sending traffic. The
script is idempotent and resumable — re-running on an already-migrated
database is a no-op. Each step records itself in `migration_progress`.

Inference rules for `documents.lifecycle_state`:

    has any FAILED analysis_jobs row, no completed       → Failed
    has any COMPLETED analysis_jobs row + chunks_json    → Chunked
    has any COMPLETED analysis_jobs row, no chunks_json  → Parsed
    else                                                 → Uploaded

After chunks are materialized into the new `chunks` table and links are
backfilled (one per existing default-store ingestion), the document
state is recomputed using the standard #203 aggregation rule. This
covers Stale / Ingested upgrades where applicable.

Usage:

    python -m tools.migrate_06 [--dry-run] [--only-step <name>]

The CLI is intentionally minimal — see docs/design/206-lifecycle-state-migration.md
for the full set of flags considered.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.hashing import chunkset_hash

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    import aiosqlite
from domain.lifecycle_aggregation import aggregate_lifecycle
from domain.models import Chunk, DocumentStoreLink
from domain.value_objects import (
    ChunkBbox,
    ChunkDocItem,
    ChunkResult,
    DocumentLifecycleState,
    DocumentStoreLinkState,
)
from persistence.chunk_repo import SqliteChunkRepository
from persistence.database import get_connection, init_db
from persistence.document_store_link_repo import SqliteDocumentStoreLinkRepository
from persistence.store_repo import SqliteStoreRepository

logger = logging.getLogger("migrate_06")


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------


async def _is_done(db: aiosqlite.Connection, name: str) -> bool:
    cursor = await db.execute("SELECT 1 FROM migration_progress WHERE name = ?", (name,))
    return await cursor.fetchone() is not None


async def _mark_done(db: aiosqlite.Connection, name: str) -> None:
    await db.execute(
        "INSERT OR IGNORE INTO migration_progress (name) VALUES (?)",
        (name,),
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Step: backfill_document_lifecycle_state
# ---------------------------------------------------------------------------


@dataclass
class _DocFacts:
    document_id: str
    has_completed: bool
    has_failed: bool
    has_chunks_json: bool


async def _gather_document_facts(db: aiosqlite.Connection) -> list[_DocFacts]:
    """One row per document with the analysis-state booleans we care about."""
    cursor = await db.execute(
        """SELECT d.id AS document_id,
                  MAX(CASE WHEN a.status = 'COMPLETED' THEN 1 ELSE 0 END) AS has_completed,
                  MAX(CASE WHEN a.status = 'FAILED'    THEN 1 ELSE 0 END) AS has_failed,
                  MAX(CASE WHEN a.chunks_json IS NOT NULL AND a.chunks_json != ''
                           THEN 1 ELSE 0 END) AS has_chunks_json
           FROM documents d
           LEFT JOIN analysis_jobs a ON a.document_id = d.id
           GROUP BY d.id"""
    )
    rows = await cursor.fetchall()
    return [
        _DocFacts(
            document_id=r["document_id"],
            has_completed=bool(r["has_completed"]),
            has_failed=bool(r["has_failed"]),
            has_chunks_json=bool(r["has_chunks_json"]),
        )
        for r in rows
    ]


def _infer_lifecycle(facts: _DocFacts) -> DocumentLifecycleState:
    if facts.has_completed and facts.has_chunks_json:
        return DocumentLifecycleState.CHUNKED
    if facts.has_completed:
        return DocumentLifecycleState.PARSED
    if facts.has_failed:
        return DocumentLifecycleState.FAILED
    return DocumentLifecycleState.UPLOADED


async def _step_backfill_lifecycle(db: aiosqlite.Connection, *, dry_run: bool) -> int:
    facts = await _gather_document_facts(db)
    written = 0
    for f in facts:
        target = _infer_lifecycle(f)
        cursor = await db.execute(
            "SELECT lifecycle_state FROM documents WHERE id = ?",
            (f.document_id,),
        )
        row = await cursor.fetchone()
        if row and row["lifecycle_state"] == target.value:
            continue
        logger.info(
            "lifecycle: doc=%s -> %s",
            f.document_id,
            target.value,
        )
        if not dry_run:
            await db.execute(
                "UPDATE documents SET lifecycle_state = ?, "
                "lifecycle_state_at = datetime('now') WHERE id = ?",
                (target.value, f.document_id),
            )
        written += 1
    if not dry_run:
        await db.commit()
    return written


# ---------------------------------------------------------------------------
# Step: materialize_chunks_from_chunks_json
# ---------------------------------------------------------------------------


def _stable_chunk_id(document_id: str, sequence: int, text: str) -> str:
    """Deterministic id so re-running the migration doesn't duplicate rows."""
    seed = f"{document_id}|{sequence}|{text}"
    return uuid.uuid5(uuid.NAMESPACE_OID, seed).hex


def _chunk_dicts_for_doc(
    db: aiosqlite.Connection,
) -> Callable[[str], asyncio.Future[list[dict]]]:
    """Return an async-compatible accessor over the latest chunks_json
    for a document. Returns an empty list when no chunks_json is available.
    """

    async def _read(document_id: str) -> list[dict]:
        cursor = await db.execute(
            """SELECT chunks_json FROM analysis_jobs
               WHERE document_id = ? AND chunks_json IS NOT NULL AND chunks_json != ''
               ORDER BY completed_at DESC, created_at DESC
               LIMIT 1""",
            (document_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return []
        try:
            return list(json.loads(row["chunks_json"]))
        except (TypeError, ValueError):
            logger.warning("Invalid chunks_json for doc %s — skipping", document_id)
            return []

    return _read


def _chunk_dict_to_chunk(d: dict, *, document_id: str, sequence: int) -> Chunk:
    text = d.get("text", "")
    return Chunk(
        id=_stable_chunk_id(document_id, sequence, text),
        document_id=document_id,
        sequence=sequence,
        text=text,
        headings=list(d.get("headings", [])),
        source_page=d.get("sourcePage"),
        bboxes=[
            ChunkBbox(page=b.get("page", 0), bbox=list(b.get("bbox", [])))
            for b in d.get("bboxes", [])
        ],
        doc_items=[
            ChunkDocItem(
                self_ref=di.get("selfRef", ""),
                label=di.get("label", ""),
            )
            for di in d.get("docItems", [])
        ],
        token_count=d.get("tokenCount"),
    )


async def _step_materialize_chunks(db: aiosqlite.Connection, *, dry_run: bool) -> int:
    """For each document with chunks_json, insert chunk rows if absent."""
    chunks_repo = SqliteChunkRepository()
    cursor = await db.execute("SELECT id FROM documents")
    doc_rows = await cursor.fetchall()
    written = 0
    read = _chunk_dicts_for_doc(db)
    for doc_row in doc_rows:
        document_id = doc_row["id"]
        existing = await chunks_repo.find_for_document(document_id, include_deleted=True)
        if existing:
            continue  # already materialized
        chunk_dicts = await read(document_id)
        if not chunk_dicts:
            continue
        chunks = [
            _chunk_dict_to_chunk(d, document_id=document_id, sequence=i)
            for i, d in enumerate(chunk_dicts)
        ]
        logger.info("chunks: doc=%s materializing %d", document_id, len(chunks))
        if not dry_run:
            await chunks_repo.insert_many(chunks)
        written += len(chunks)
    return written


# ---------------------------------------------------------------------------
# Step: backfill_default_store_links
# ---------------------------------------------------------------------------


def _chunks_to_results(chunks: Iterable[Chunk]) -> list[ChunkResult]:
    return [
        ChunkResult(
            text=c.text,
            headings=list(c.headings),
            source_page=c.source_page,
            bboxes=[ChunkBbox(page=b.page, bbox=list(b.bbox)) for b in c.bboxes],
            doc_items=[ChunkDocItem(self_ref=d.self_ref, label=d.label) for d in c.doc_items],
        )
        for c in chunks
    ]


async def _step_backfill_links(db: aiosqlite.Connection, *, dry_run: bool) -> int:
    """For each doc that already has chunks materialized, create a
    `default`-store link in `Ingested` state with a freshly-computed
    chunkset hash. This treats "chunks exist" as a proxy for "the
    document has been ingested into the default store" — which is true
    for tenants with the legacy single-index deployment that 0.6.0
    formalises into the `default` store.

    This step does NOT call OpenSearch. Operators with non-trivial
    OpenSearch state should run a separate reindex / verification
    after this script (see runbook).
    """
    store_repo = SqliteStoreRepository()
    chunks_repo = SqliteChunkRepository()
    link_repo = SqliteDocumentStoreLinkRepository()

    default_store = await store_repo.get_default()
    if default_store is None:
        logger.warning(
            "No default store — skipping link backfill (run init_db first)",
        )
        return 0

    cursor = await db.execute("SELECT id FROM documents")
    doc_rows = await cursor.fetchall()
    written = 0
    for doc_row in doc_rows:
        document_id = doc_row["id"]
        existing = await link_repo.find_one(document_id, default_store.id)
        if existing is not None:
            continue
        chunks = await chunks_repo.find_for_document(document_id)
        if not chunks:
            continue
        h = chunkset_hash(_chunks_to_results(chunks))
        link = DocumentStoreLink(
            document_id=document_id,
            store_id=default_store.id,
            state=DocumentStoreLinkState.INGESTED,
            chunkset_hash=h,
        )
        logger.info(
            "links: doc=%s -> store=%s ingested (hash=%s…)",
            document_id,
            default_store.id,
            h[:8],
        )
        if not dry_run:
            await link_repo.upsert(link)
        written += 1
    return written


# ---------------------------------------------------------------------------
# Step: reaggregate_document_lifecycle
# ---------------------------------------------------------------------------


async def _step_reaggregate(db: aiosqlite.Connection, *, dry_run: bool) -> int:
    """Recompute the doc lifecycle state from per-store links + the
    fallback inferred in step 1."""
    link_repo = SqliteDocumentStoreLinkRepository()
    cursor = await db.execute("SELECT id, lifecycle_state FROM documents")
    rows = await cursor.fetchall()
    written = 0
    for row in rows:
        doc_id = row["id"]
        current = DocumentLifecycleState(row["lifecycle_state"])
        links = await link_repo.find_for_document(doc_id)
        target = aggregate_lifecycle(links, fallback=current)
        if target == current:
            continue
        logger.info(
            "reaggregate: doc=%s %s -> %s",
            doc_id,
            current.value,
            target.value,
        )
        if not dry_run:
            await db.execute(
                "UPDATE documents SET lifecycle_state = ?, "
                "lifecycle_state_at = datetime('now') WHERE id = ?",
                (target.value, doc_id),
            )
        written += 1
    if not dry_run:
        await db.commit()
    return written


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


_STEPS = [
    ("backfill_lifecycle", _step_backfill_lifecycle),
    ("materialize_chunks", _step_materialize_chunks),
    ("backfill_links", _step_backfill_links),
    ("reaggregate", _step_reaggregate),
]


@dataclass
class StepResult:
    name: str
    skipped: bool
    written: int


async def run(
    *,
    dry_run: bool = False,
    only_step: str | None = None,
) -> list[StepResult]:
    """Run the migration. Returns one StepResult per step (skipped or not)."""
    await init_db()  # ensures the schema and migration_progress table exist
    results: list[StepResult] = []
    async with get_connection() as db:
        for name, step in _STEPS:
            if only_step and only_step != name:
                continue
            if await _is_done(db, name):
                results.append(StepResult(name=name, skipped=True, written=0))
                logger.info("step %s: already done — skipping", name)
                continue
            logger.info("step %s: running (dry_run=%s)", name, dry_run)
            written = await step(db, dry_run=dry_run)
            if not dry_run:
                await _mark_done(db, name)
            results.append(StepResult(name=name, skipped=False, written=written))
    return results


def _print_summary(results: list[StepResult], *, dry_run: bool) -> None:
    print()
    print(f"{'step':35s} {'wrote':>10s}  {'skipped':>10s}")
    print("-" * 60)
    total_written = 0
    for r in results:
        print(f"{r.name:35s} {r.written:>10d}  {'yes' if r.skipped else 'no':>10s}")
        total_written += r.written
    print("-" * 60)
    print(f"{'total':35s} {total_written:>10d}")
    print()
    print(f"dry_run={dry_run}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(prog="migrate_06")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without writing.",
    )
    parser.add_argument(
        "--only-step",
        choices=[name for name, _ in _STEPS],
        help="Run a single named step (useful when re-doing one phase).",
    )
    args = parser.parse_args(argv)

    results = asyncio.run(run(dry_run=args.dry_run, only_step=args.only_step))
    _print_summary(results, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
