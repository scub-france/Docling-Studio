"""Tests for the 0.6.0 migration script (#206)."""

from __future__ import annotations

import json

import pytest

from domain.value_objects import DocumentLifecycleState, DocumentStoreLinkState
from persistence.chunk_repo import SqliteChunkRepository
from persistence.database import get_connection, init_db
from persistence.document_repo import SqliteDocumentRepository
from persistence.document_store_link_repo import SqliteDocumentStoreLinkRepository
from tools.migrate_06 import _DocFacts, _infer_lifecycle, run


@pytest.fixture(autouse=True)
async def setup_db(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("persistence.database.DB_PATH", db_path)
    await init_db()
    yield


# ---------------------------------------------------------------------------
# Inference rule unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("has_completed", "has_failed", "has_chunks_json", "expected"),
    [
        (False, False, False, DocumentLifecycleState.UPLOADED),
        (False, True, False, DocumentLifecycleState.FAILED),
        (True, False, False, DocumentLifecycleState.PARSED),
        (True, False, True, DocumentLifecycleState.CHUNKED),
        (True, True, True, DocumentLifecycleState.CHUNKED),  # any completed wins
    ],
)
def test_infer_lifecycle(
    has_completed: bool,
    has_failed: bool,
    has_chunks_json: bool,
    expected: DocumentLifecycleState,
) -> None:
    facts = _DocFacts(
        document_id="doc",
        has_completed=has_completed,
        has_failed=has_failed,
        has_chunks_json=has_chunks_json,
    )
    assert _infer_lifecycle(facts) == expected


# ---------------------------------------------------------------------------
# Integration: end-to-end migration on a hand-built pre-state
# ---------------------------------------------------------------------------


async def _seed_pre_06_state() -> None:
    """Seed a tenant snapshot with three documents covering the three
    main inference cases:

      doc-uploaded — only an `Uploaded` doc row, nothing else
      doc-parsed   — completed analysis, no chunks
      doc-chunked  — completed analysis with chunks_json
    """
    repo = SqliteDocumentRepository()
    async with get_connection() as db:
        await db.execute(
            "INSERT INTO documents (id, filename, storage_path, created_at) "
            "VALUES ('doc-uploaded', 'a.pdf', '/tmp/a.pdf', datetime('now'))"
        )
        await db.execute(
            "INSERT INTO documents (id, filename, storage_path, created_at) "
            "VALUES ('doc-parsed', 'b.pdf', '/tmp/b.pdf', datetime('now'))"
        )
        await db.execute(
            "INSERT INTO documents (id, filename, storage_path, created_at) "
            "VALUES ('doc-chunked', 'c.pdf', '/tmp/c.pdf', datetime('now'))"
        )
        await db.execute(
            "INSERT INTO analysis_jobs (id, document_id, status) "
            "VALUES ('a-parsed', 'doc-parsed', 'COMPLETED')"
        )
        chunks_json = json.dumps(
            [
                {"text": "Intro paragraph.", "headings": ["Intro"], "sourcePage": 1},
                {"text": "Body of section A.", "headings": ["A"], "sourcePage": 2},
            ]
        )
        await db.execute(
            "INSERT INTO analysis_jobs (id, document_id, status, chunks_json) "
            "VALUES ('a-chunked', 'doc-chunked', 'COMPLETED', ?)",
            (chunks_json,),
        )
        await db.commit()
    # Touch the document repo so the type checker is satisfied.
    assert await repo.find_by_id("doc-chunked") is not None


async def test_full_migration_writes_expected_state() -> None:
    await _seed_pre_06_state()

    results = await run(dry_run=False)
    by_step = {r.name: r for r in results}
    assert by_step["backfill_lifecycle"].written >= 2  # parsed + chunked transition
    assert by_step["materialize_chunks"].written == 2  # two chunks
    assert by_step["backfill_links"].written == 1  # only doc-chunked has chunks

    repo = SqliteDocumentRepository()
    chunks_repo = SqliteChunkRepository()
    link_repo = SqliteDocumentStoreLinkRepository()

    uploaded = await repo.find_by_id("doc-uploaded")
    assert uploaded is not None
    assert uploaded.lifecycle_state == DocumentLifecycleState.UPLOADED

    parsed = await repo.find_by_id("doc-parsed")
    assert parsed is not None
    assert parsed.lifecycle_state == DocumentLifecycleState.PARSED

    chunked = await repo.find_by_id("doc-chunked")
    assert chunked is not None
    # After link backfill + reaggregation, doc-chunked is Ingested in default store.
    assert chunked.lifecycle_state == DocumentLifecycleState.INGESTED

    chunks = await chunks_repo.find_for_document("doc-chunked")
    assert len(chunks) == 2
    assert chunks[0].text == "Intro paragraph."
    assert chunks[0].sequence == 0

    links = await link_repo.find_for_document("doc-chunked")
    assert len(links) == 1
    assert links[0].store_id == "default"
    assert links[0].state == DocumentStoreLinkState.INGESTED
    assert links[0].chunkset_hash is not None


async def test_migration_is_idempotent() -> None:
    await _seed_pre_06_state()

    first = await run(dry_run=False)
    second = await run(dry_run=False)
    # Second run sees every step as already-done.
    assert all(r.skipped for r in second)
    assert all(not r.skipped for r in first)


async def test_dry_run_writes_nothing() -> None:
    await _seed_pre_06_state()

    repo = SqliteDocumentRepository()
    chunks_repo = SqliteChunkRepository()

    await run(dry_run=True)

    # No state changed.
    parsed = await repo.find_by_id("doc-parsed")
    assert parsed is not None
    assert parsed.lifecycle_state == DocumentLifecycleState.UPLOADED  # unchanged
    chunked_chunks = await chunks_repo.find_for_document("doc-chunked")
    assert chunked_chunks == []


async def test_chunk_ids_are_deterministic_across_runs() -> None:
    """Stable id derivation lets a re-run after a manual reset land on
    the same chunk ids — important for the link-table foreign keys."""
    await _seed_pre_06_state()

    chunks_repo = SqliteChunkRepository()

    await run(dry_run=False, only_step="materialize_chunks")
    first_ids = sorted(c.id for c in await chunks_repo.find_for_document("doc-chunked"))

    # Wipe progress + chunks, run again — same ids.
    async with get_connection() as db:
        await db.execute("DELETE FROM migration_progress WHERE name = 'materialize_chunks'")
        await db.execute("DELETE FROM chunks WHERE document_id = 'doc-chunked'")
        await db.commit()

    await run(dry_run=False, only_step="materialize_chunks")
    second_ids = sorted(c.id for c in await chunks_repo.find_for_document("doc-chunked"))

    assert first_ids == second_ids
