"""Tests for IngestionService — orchestrated pipeline."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.models import AnalysisJob, AnalysisStatus, Document
from domain.vector_schema import IndexedChunk
from services.ingestion_service import IngestionError, IngestionService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_doc(doc_id: str = "doc-1", filename: str = "test.pdf") -> Document:
    return Document(id=doc_id, filename=filename)


def _make_job(
    job_id: str = "job-1",
    doc_id: str = "doc-1",
    status: AnalysisStatus = AnalysisStatus.COMPLETED,
    chunks_json: str | None = None,
) -> AnalysisJob:
    if chunks_json is None:
        chunks_json = json.dumps(
            [
                {
                    "text": "Hello world",
                    "headings": ["Introduction"],
                    "sourcePage": 1,
                    "bboxes": [{"page": 1, "bbox": [10.0, 20.0, 100.0, 50.0]}],
                },
                {
                    "text": "Second chunk",
                    "headings": [],
                    "sourcePage": 2,
                    "bboxes": [],
                },
            ]
        )
    job = AnalysisJob(id=job_id, document_id=doc_id, status=status)
    job.chunks_json = chunks_json
    return job


def _make_service(
    *,
    job: AnalysisJob | None = None,
    doc: Document | None = None,
    embeddings: list[list[float]] | None = None,
    indexed_count: int = 2,
) -> IngestionService:
    if job is None:
        job = _make_job()
    if doc is None:
        doc = _make_doc()
    if embeddings is None:
        embeddings = [[0.1] * 384, [0.2] * 384]

    analysis_repo = MagicMock()
    analysis_repo.find_by_id = AsyncMock(return_value=job)

    document_repo = MagicMock()
    document_repo.find_by_id = AsyncMock(return_value=doc)

    embedding_svc = MagicMock()
    embedding_svc.embed = AsyncMock(return_value=embeddings)

    vector_store = MagicMock()
    vector_store.ensure_index = AsyncMock()
    vector_store.delete_document = AsyncMock(return_value=0)
    vector_store.index_chunks = AsyncMock(return_value=indexed_count)

    return (
        IngestionService(
            analysis_repo=analysis_repo,
            document_repo=document_repo,
            embedding_svc=embedding_svc,
            vector_store=vector_store,
        ),
        analysis_repo,
        document_repo,
        embedding_svc,
        vector_store,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_ingest_success():
    svc, _, _, embedding_svc, vector_store = _make_service()
    result = await svc.ingest("job-1")

    assert result.doc_id == "doc-1"
    assert result.chunks_indexed == 2
    assert result.embedding_dimension == 384

    # embedding called with 2 texts
    embedding_svc.embed.assert_awaited_once()
    texts = embedding_svc.embed.call_args[0][0]
    assert texts == ["Hello world", "Second chunk"]

    # ensure_index called
    vector_store.ensure_index.assert_awaited_once()

    # delete_document called for idempotency
    vector_store.delete_document.assert_awaited_once_with("docling-studio-chunks", "doc-1")

    # index_chunks called with IndexedChunk list
    vector_store.index_chunks.assert_awaited_once()
    chunks_arg = vector_store.index_chunks.call_args[0][1]
    assert len(chunks_arg) == 2
    assert all(isinstance(c, IndexedChunk) for c in chunks_arg)
    assert chunks_arg[0].content == "Hello world"
    assert chunks_arg[0].chunk_index == 0
    assert chunks_arg[1].chunk_index == 1


async def test_ingest_preserves_bboxes():
    # Rebuild to inspect chunks
    svc2, _, _, _, vector_store = _make_service()
    await svc2.ingest("job-1")
    chunks_arg = vector_store.index_chunks.call_args[0][1]
    first_chunk = chunks_arg[0]
    assert len(first_chunk.bboxes) == 1
    bbox = first_chunk.bboxes[0]
    assert bbox.page == 1
    assert bbox.x == 10.0
    assert bbox.y == 20.0
    assert bbox.w == 90.0  # right - left = 100 - 10
    assert bbox.h == 30.0  # bottom - top = 50 - 20


async def test_ingest_preserves_headings():
    svc, _, _, _, vector_store = _make_service()
    await svc.ingest("job-1")
    chunks = vector_store.index_chunks.call_args[0][1]
    assert chunks[0].headings == ["Introduction"]
    assert chunks[1].headings == []


async def test_ingest_idempotent_deletes_first():
    svc, _, _, _, vector_store = _make_service()
    vector_store.delete_document = AsyncMock(return_value=5)

    result = await svc.ingest("job-1")
    vector_store.delete_document.assert_awaited_once()
    assert result.chunks_indexed == 2


async def test_ingest_detects_embedding_dimension():
    embeddings = [[0.1] * 768, [0.2] * 768]
    svc, *_ = _make_service(embeddings=embeddings)
    result = await svc.ingest("job-1")
    assert result.embedding_dimension == 768


# ---------------------------------------------------------------------------
# Error cases — job not found
# ---------------------------------------------------------------------------


async def test_ingest_job_not_found():
    svc, analysis_repo, *_ = _make_service()
    analysis_repo.find_by_id = AsyncMock(return_value=None)

    with pytest.raises(IngestionError, match="not found"):
        await svc.ingest("missing-job")


async def test_ingest_job_not_completed():
    job = _make_job(status=AnalysisStatus.RUNNING)
    svc, *_ = _make_service(job=job)

    with pytest.raises(IngestionError, match="not COMPLETED"):
        await svc.ingest("job-1")


async def test_ingest_job_no_chunks():
    job = _make_job(chunks_json=None)
    job.chunks_json = None
    svc, *_ = _make_service(job=job)

    with pytest.raises(IngestionError, match="no chunks"):
        await svc.ingest("job-1")


async def test_ingest_job_empty_chunks():
    job = _make_job(chunks_json="[]")
    svc, *_ = _make_service(job=job)

    with pytest.raises(IngestionError, match="empty"):
        await svc.ingest("job-1")


async def test_ingest_doc_not_found():
    svc, _, document_repo, *_ = _make_service()
    document_repo.find_by_id = AsyncMock(return_value=None)

    with pytest.raises(IngestionError, match="Document not found"):
        await svc.ingest("job-1")


# ---------------------------------------------------------------------------
# Error cases — pipeline failures
# ---------------------------------------------------------------------------


async def test_ingest_embedding_failure():
    svc, _, _, embedding_svc, _ = _make_service()
    embedding_svc.embed = AsyncMock(side_effect=ConnectionError("embedding service down"))

    with pytest.raises(IngestionError, match="Embedding generation failed"):
        await svc.ingest("job-1")


async def test_ingest_index_failure():
    svc, _, _, _, vector_store = _make_service()
    vector_store.ensure_index = AsyncMock(side_effect=RuntimeError("opensearch down"))

    with pytest.raises(IngestionError, match="Failed to ensure index"):
        await svc.ingest("job-1")


async def test_ingest_bulk_index_failure():
    svc, _, _, _, vector_store = _make_service()
    vector_store.index_chunks = AsyncMock(side_effect=RuntimeError("bulk failed"))

    with pytest.raises(IngestionError, match="Bulk indexing failed"):
        await svc.ingest("job-1")


async def test_ingest_embedding_count_mismatch():
    svc, _, _, embedding_svc, _ = _make_service()
    embedding_svc.embed = AsyncMock(return_value=[[0.1] * 384])  # only 1 instead of 2

    with pytest.raises(IngestionError, match="mismatch"):
        await svc.ingest("job-1")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_delete_calls_vector_store():
    svc, _, _, _, vector_store = _make_service()
    vector_store.delete_document = AsyncMock(return_value=7)

    count = await svc.delete("doc-1")
    assert count == 7
    vector_store.delete_document.assert_awaited_once_with("docling-studio-chunks", "doc-1")


async def test_delete_raises_ingestion_error_on_failure():
    svc, _, _, _, vector_store = _make_service()
    vector_store.delete_document = AsyncMock(side_effect=RuntimeError("opensearch down"))

    with pytest.raises(IngestionError, match="Failed to delete"):
        await svc.delete("doc-1")
