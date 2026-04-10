"""Tests for vector index schema — value objects and OpenSearch mapping."""

from __future__ import annotations

import pytest

from domain.vector_schema import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_INDEX_NAME,
    ChunkBboxEntry,
    ChunkOrigin,
    DocItemRef,
    IndexedChunk,
    build_index_mapping,
)


class TestChunkBboxEntry:
    def test_construction(self):
        bbox = ChunkBboxEntry(page=1, x=10.0, y=20.0, w=100.0, h=50.0)
        assert bbox.page == 1
        assert bbox.x == 10.0
        assert bbox.w == 100.0

    def test_frozen(self):
        bbox = ChunkBboxEntry(page=1, x=0, y=0, w=10, h=10)
        with pytest.raises(AttributeError):
            bbox.page = 2  # type: ignore[misc]


class TestDocItemRef:
    def test_construction(self):
        ref = DocItemRef(self_ref="#/texts/0", label="text")
        assert ref.self_ref == "#/texts/0"
        assert ref.label == "text"


class TestChunkOrigin:
    def test_construction(self):
        origin = ChunkOrigin(binary_hash="abc123", filename="doc.pdf")
        assert origin.binary_hash == "abc123"
        assert origin.filename == "doc.pdf"


class TestIndexedChunk:
    def _make_chunk(self, **overrides) -> IndexedChunk:
        defaults = {
            "doc_id": "doc-1",
            "filename": "test.pdf",
            "content": "Hello world",
            "embedding": [0.1] * 384,
            "chunk_index": 0,
            "chunk_type": "text",
            "page_number": 1,
        }
        defaults.update(overrides)
        return IndexedChunk(**defaults)

    def test_minimal_chunk(self):
        chunk = self._make_chunk()
        assert chunk.doc_id == "doc-1"
        assert chunk.content == "Hello world"
        assert chunk.bboxes == []
        assert chunk.headings == []
        assert chunk.doc_items == []
        assert chunk.origin is None

    def test_full_chunk(self):
        chunk = self._make_chunk(
            bboxes=[ChunkBboxEntry(page=1, x=10, y=20, w=100, h=50)],
            headings=["Chapter 1", "Section A"],
            doc_items=[DocItemRef(self_ref="#/texts/0", label="text")],
            origin=ChunkOrigin(binary_hash="abc", filename="test.pdf"),
        )
        assert len(chunk.bboxes) == 1
        assert chunk.headings == ["Chapter 1", "Section A"]
        assert chunk.doc_items[0].label == "text"
        assert chunk.origin.binary_hash == "abc"

    def test_to_dict_minimal(self):
        chunk = self._make_chunk()
        d = chunk.to_dict()
        assert d["doc_id"] == "doc-1"
        assert d["filename"] == "test.pdf"
        assert d["content"] == "Hello world"
        assert d["embedding"] == [0.1] * 384
        assert d["chunk_index"] == 0
        assert d["chunk_type"] == "text"
        assert d["page_number"] == 1
        assert d["bboxes"] == []
        assert d["headings"] == []
        assert d["doc_items"] == []
        assert "origin" not in d

    def test_to_dict_full(self):
        chunk = self._make_chunk(
            bboxes=[ChunkBboxEntry(page=1, x=10.5, y=20.0, w=100.0, h=50.0)],
            headings=["H1"],
            doc_items=[DocItemRef(self_ref="#/texts/0", label="text")],
            origin=ChunkOrigin(binary_hash="abc", filename="test.pdf"),
        )
        d = chunk.to_dict()
        assert d["bboxes"] == [{"page": 1, "x": 10.5, "y": 20.0, "w": 100.0, "h": 50.0}]
        assert d["headings"] == ["H1"]
        assert d["doc_items"] == [{"self_ref": "#/texts/0", "label": "text"}]
        assert d["origin"] == {"binary_hash": "abc", "filename": "test.pdf"}

    def test_frozen(self):
        chunk = self._make_chunk()
        with pytest.raises(AttributeError):
            chunk.content = "modified"  # type: ignore[misc]


class TestBuildIndexMapping:
    def test_default_dimension(self):
        mapping = build_index_mapping()
        props = mapping["mappings"]["properties"]
        assert props["embedding"]["dimension"] == 384
        assert props["embedding"]["type"] == "knn_vector"
        assert props["embedding"]["method"]["engine"] == "faiss"
        assert props["embedding"]["method"]["name"] == "hnsw"

    def test_custom_dimension(self):
        mapping = build_index_mapping(embedding_dimension=768)
        assert mapping["mappings"]["properties"]["embedding"]["dimension"] == 768

    def test_knn_enabled(self):
        mapping = build_index_mapping()
        assert mapping["settings"]["index"]["knn"] is True

    def test_all_fields_present(self):
        mapping = build_index_mapping()
        props = mapping["mappings"]["properties"]
        expected_fields = {
            "doc_id",
            "filename",
            "content",
            "embedding",
            "chunk_index",
            "chunk_type",
            "page_number",
            "bboxes",
            "headings",
            "doc_items",
            "origin",
        }
        assert set(props.keys()) == expected_fields

    def test_bboxes_nested_type(self):
        mapping = build_index_mapping()
        bboxes = mapping["mappings"]["properties"]["bboxes"]
        assert bboxes["type"] == "nested"
        assert "page" in bboxes["properties"]
        assert "x" in bboxes["properties"]
        assert "y" in bboxes["properties"]
        assert "w" in bboxes["properties"]
        assert "h" in bboxes["properties"]

    def test_doc_items_nested_type(self):
        mapping = build_index_mapping()
        doc_items = mapping["mappings"]["properties"]["doc_items"]
        assert doc_items["type"] == "nested"
        assert "self_ref" in doc_items["properties"]
        assert "label" in doc_items["properties"]

    def test_origin_object_type(self):
        mapping = build_index_mapping()
        origin = mapping["mappings"]["properties"]["origin"]
        assert origin["type"] == "object"
        assert "binary_hash" in origin["properties"]
        assert "filename" in origin["properties"]

    def test_content_uses_standard_analyzer(self):
        mapping = build_index_mapping()
        content = mapping["mappings"]["properties"]["content"]
        assert content["type"] == "text"
        assert content["analyzer"] == "standard"

    def test_keyword_fields(self):
        mapping = build_index_mapping()
        props = mapping["mappings"]["properties"]
        for field_name in ("doc_id", "filename", "chunk_type"):
            assert props[field_name]["type"] == "keyword", f"{field_name} should be keyword"

    def test_integer_fields(self):
        mapping = build_index_mapping()
        props = mapping["mappings"]["properties"]
        for field_name in ("chunk_index", "page_number"):
            assert props[field_name]["type"] == "integer", f"{field_name} should be integer"


class TestConstants:
    def test_default_embedding_dimension(self):
        assert DEFAULT_EMBEDDING_DIMENSION == 384

    def test_default_index_name(self):
        assert DEFAULT_INDEX_NAME == "docling-studio-chunks"
