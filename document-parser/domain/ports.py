"""Domain ports — abstract interfaces that infrastructure must implement.

These protocols define what the domain NEEDS, not how it's done.
Infrastructure adapters (local Docling, Docling Serve, etc.) implement these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
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
