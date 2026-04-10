"""Domain ports — abstract interfaces that infrastructure must implement.

These protocols define what the domain NEEDS, not how it's done.
Infrastructure adapters (local Docling, Docling Serve, etc.) implement these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from domain.models import AnalysisJob, Document
    from domain.value_objects import (
        ChunkingOptions,
        ChunkResult,
        ConversionOptions,
        ConversionResult,
    )
    from domain.vector_schema import IndexedChunk, SearchResult


class DocumentConverter(Protocol):
    """Port for document conversion.

    Any implementation (local Docling lib, remote Docling Serve, mock, etc.)
    must satisfy this contract.
    """

    async def convert(
        self,
        file_path: str,
        options: ConversionOptions,
        *,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult: ...


class DocumentChunker(Protocol):
    """Port for document chunking.

    Takes a serialized DoclingDocument (JSON) and returns chunks.
    """

    async def chunk(
        self,
        document_json: str,
        options: ChunkingOptions,
    ) -> list[ChunkResult]: ...


class DocumentRepository(Protocol):
    """Port for document persistence."""

    async def insert(self, doc: Document) -> None: ...

    async def find_all(self, *, limit: int = 200, offset: int = 0) -> list[Document]: ...

    async def find_by_id(self, doc_id: str) -> Document | None: ...

    async def update_page_count(self, doc_id: str, page_count: int) -> None: ...

    async def delete(self, doc_id: str) -> bool: ...


class AnalysisRepository(Protocol):
    """Port for analysis job persistence."""

    async def insert(self, job: AnalysisJob) -> None: ...

    async def find_all(self, *, limit: int = 200, offset: int = 0) -> list[AnalysisJob]: ...

    async def find_by_id(self, job_id: str) -> AnalysisJob | None: ...

    async def update_status(self, job: AnalysisJob) -> None: ...

    async def update_progress(self, job_id: str, current: int, total: int) -> None: ...

    async def update_chunks(self, job_id: str, chunks_json: str) -> bool: ...

    async def delete(self, job_id: str) -> bool: ...

    async def delete_by_document(self, document_id: str) -> int: ...


@runtime_checkable
class VectorStore(Protocol):
    """Port for vector storage and retrieval.

    Implementations (OpenSearch, pgvector, Qdrant, etc.) must satisfy this
    contract. The port uses domain types from vector_schema — no infrastructure
    details leak into the domain.
    """

    async def ensure_index(self, index_name: str, mapping: dict) -> None:
        """Create the index if it does not exist. No-op if it already exists."""
        ...

    async def index_chunks(self, index_name: str, chunks: list[IndexedChunk]) -> int:
        """Bulk-index a list of chunks. Returns the number of successfully indexed chunks."""
        ...

    async def search_similar(
        self,
        index_name: str,
        embedding: list[float],
        *,
        k: int = 10,
        doc_id: str | None = None,
    ) -> list[SearchResult]:
        """Find the k nearest chunks by embedding similarity.

        Args:
            index_name: Target index.
            embedding: Query vector.
            k: Number of results to return.
            doc_id: If provided, restrict search to chunks from this document.
        """
        ...

    async def get_chunks(
        self,
        index_name: str,
        doc_id: str,
        *,
        limit: int = 1000,
    ) -> list[SearchResult]:
        """Retrieve all indexed chunks for a given document, ordered by chunk_index."""
        ...

    async def delete_document(self, index_name: str, doc_id: str) -> int:
        """Delete all chunks for a document from the index. Returns count deleted."""
        ...
