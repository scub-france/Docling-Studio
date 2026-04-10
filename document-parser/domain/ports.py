"""Domain ports — abstract interfaces that infrastructure must implement.

These protocols define what the domain NEEDS, not how it's done.
Infrastructure adapters (local Docling, Docling Serve, etc.) implement these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domain.models import AnalysisJob, Document
    from domain.value_objects import (
        ChunkingOptions,
        ChunkResult,
        ConversionOptions,
        ConversionResult,
    )


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
