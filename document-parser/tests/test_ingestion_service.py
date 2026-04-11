"""Tests for the ingestion service (services.ingestion_service)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from services.ingestion_service import IngestionConfig, IngestionService


def _make_chunks_json(count: int = 3, *, with_deleted: bool = False) -> str:
    chunks = []
    for i in range(count):
        chunk = {
            "text": f"chunk text {i}",
            "headings": [f"Heading {i}"],
            "sourcePage": i + 1,
            "tokenCount": 10,
            "bboxes": [{"page": i + 1, "bbox": [0.0, 0.0, 100.0, 50.0]}],
        }
        if with_deleted and i == count - 1:
            chunk["deleted"] = True
        chunks.append(chunk)
    return json.dumps(chunks)


@pytest.fixture
def mock_embedding() -> AsyncMock:
    svc = AsyncMock()
    svc.embed.return_value = [[0.1, 0.2, 0.3]] * 3
    return svc


@pytest.fixture
def mock_vector_store() -> AsyncMock:
    store = AsyncMock()
    store.ensure_index.return_value = None
    store.delete_document.return_value = 0
    store.index_chunks.return_value = 3
    return store


@pytest.fixture
def service(mock_embedding: AsyncMock, mock_vector_store: AsyncMock) -> IngestionService:
    return IngestionService(
        embedding_service=mock_embedding,
        vector_store=mock_vector_store,
        config=IngestionConfig(index_name="test-idx", embedding_dimension=3),
    )


class TestIngest:
    async def test_full_pipeline(
        self, service: IngestionService, mock_embedding: AsyncMock, mock_vector_store: AsyncMock
    ) -> None:
        result = await service.ingest("doc-1", "test.pdf", _make_chunks_json(3))

        assert result.doc_id == "doc-1"
        assert result.chunks_indexed == 3
        mock_embedding.embed.assert_awaited_once()
        texts = mock_embedding.embed.call_args[0][0]
        assert len(texts) == 3
        mock_vector_store.ensure_index.assert_awaited_once()
        mock_vector_store.delete_document.assert_awaited_once_with("test-idx", "doc-1")
        mock_vector_store.index_chunks.assert_awaited_once()
        indexed = mock_vector_store.index_chunks.call_args[0][1]
        assert len(indexed) == 3
        assert indexed[0].doc_id == "doc-1"
        assert indexed[0].filename == "test.pdf"
        assert indexed[0].embedding == [0.1, 0.2, 0.3]

    async def test_skips_deleted_chunks(
        self, service: IngestionService, mock_embedding: AsyncMock, mock_vector_store: AsyncMock
    ) -> None:
        mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]] * 2
        mock_vector_store.index_chunks.return_value = 2
        result = await service.ingest("doc-1", "test.pdf", _make_chunks_json(3, with_deleted=True))

        assert result.chunks_indexed == 2
        texts = mock_embedding.embed.call_args[0][0]
        assert len(texts) == 2

    async def test_empty_chunks(
        self, service: IngestionService, mock_embedding: AsyncMock, mock_vector_store: AsyncMock
    ) -> None:
        result = await service.ingest("doc-1", "test.pdf", json.dumps([]))
        assert result.chunks_indexed == 0
        mock_embedding.embed.assert_not_awaited()

    async def test_idempotent_deletes_old(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store.delete_document.return_value = 5
        await service.ingest("doc-1", "test.pdf", _make_chunks_json(3))
        mock_vector_store.delete_document.assert_awaited_once_with("test-idx", "doc-1")

    async def test_bbox_conversion(
        self, service: IngestionService, mock_embedding: AsyncMock, mock_vector_store: AsyncMock
    ) -> None:
        mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]]
        mock_vector_store.index_chunks.return_value = 1
        await service.ingest("doc-1", "test.pdf", _make_chunks_json(1))
        indexed = mock_vector_store.index_chunks.call_args[0][1]
        bbox = indexed[0].bboxes[0]
        assert bbox.x == 0.0
        assert bbox.y == 0.0
        assert bbox.w == 100.0
        assert bbox.h == 50.0

    async def test_with_binary_hash(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_embedding = service._embedding
        mock_embedding.embed.return_value = [[0.1]] * 1
        await service.ingest("doc-1", "test.pdf", _make_chunks_json(1), binary_hash="abc123")
        indexed = mock_vector_store.index_chunks.call_args[0][1]
        assert indexed[0].origin is not None
        assert indexed[0].origin.binary_hash == "abc123"


class TestDeleteDocument:
    async def test_delegates_to_vector_store(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store.delete_document.return_value = 3
        result = await service.delete_document("doc-1")
        assert result == 3


class TestSearch:
    async def test_embeds_and_searches(
        self, service: IngestionService, mock_embedding: AsyncMock, mock_vector_store: AsyncMock
    ) -> None:
        mock_embedding.embed.return_value = [[0.5, 0.6, 0.7]]
        mock_vector_store.search_similar.return_value = []
        await service.search("test query", k=5)
        mock_embedding.embed.assert_awaited_once_with(["test query"])
        mock_vector_store.search_similar.assert_awaited_once()


class TestSearchFulltext:
    async def test_delegates_to_vector_store(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store.search_fulltext.return_value = []
        await service.search_fulltext("hello world", k=5)
        mock_vector_store.search_fulltext.assert_awaited_once_with(
            "test-idx", "hello world", k=5, doc_id=None
        )

    async def test_filters_by_doc_id(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store.search_fulltext.return_value = []
        await service.search_fulltext("hello", doc_id="doc-1")
        mock_vector_store.search_fulltext.assert_awaited_once_with(
            "test-idx", "hello", k=20, doc_id="doc-1"
        )


class TestPing:
    async def test_ping_success(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store._client = AsyncMock()
        mock_vector_store._client.info.return_value = {"cluster_name": "test"}
        result = await service.ping()
        assert result is True

    async def test_ping_failure(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        mock_vector_store._client = AsyncMock()
        mock_vector_store._client.info.side_effect = ConnectionError("down")
        result = await service.ping()
        assert result is False


class TestEnsureIndex:
    async def test_calls_vector_store(
        self, service: IngestionService, mock_vector_store: AsyncMock
    ) -> None:
        await service.ensure_index()
        mock_vector_store.ensure_index.assert_awaited_once()
        call_args = mock_vector_store.ensure_index.call_args
        assert call_args[0][0] == "test-idx"
