"""Domain value objects — pure data structures for document conversion.

These types define the contract between the domain and infrastructure layers.
They have ZERO external dependencies (no docling, no HTTP, no DB).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# US Letter page dimensions (points) — fallback when page size is unknown
DEFAULT_PAGE_WIDTH: float = 612.0
DEFAULT_PAGE_HEIGHT: float = 792.0


@dataclass(frozen=True)
class PageElement:
    type: str
    bbox: list[float]
    content: str
    level: int = 0


@dataclass(frozen=True)
class PageDetail:
    page_number: int
    width: float
    height: float
    elements: list[PageElement] = field(default_factory=list)


@dataclass(frozen=True)
class ConversionOptions:
    do_ocr: bool = True
    do_table_structure: bool = True
    table_mode: str = "accurate"
    do_code_enrichment: bool = False
    do_formula_enrichment: bool = False
    do_picture_classification: bool = False
    do_picture_description: bool = False
    generate_picture_images: bool = False
    generate_page_images: bool = False
    images_scale: float = 1.0

    def is_default(self) -> bool:
        """Return True if all options match their defaults."""
        return self == ConversionOptions()


@dataclass(frozen=True)
class ConversionResult:
    page_count: int
    content_markdown: str
    content_html: str
    pages: list[PageDetail]
    skipped_items: int = 0
    document_json: str | None = None


@dataclass(frozen=True)
class ChunkingOptions:
    chunker_type: str = "hybrid"  # "hybrid", "hierarchical", "page"
    max_tokens: int = 512
    merge_peers: bool = True
    repeat_table_header: bool = True

    def is_default(self) -> bool:
        """Return True if all options match their defaults."""
        return self == ChunkingOptions()


@dataclass(frozen=True)
class ChunkBbox:
    page: int
    bbox: list[float]  # [left, top, right, bottom] in TOPLEFT origin


@dataclass(frozen=True)
class ChunkDocItem:
    """Source element referenced by a chunk. Enables Neo4j DERIVED_FROM edges."""

    self_ref: str
    label: str


@dataclass(frozen=True)
class ChunkResult:
    text: str
    headings: list[str] = field(default_factory=list)
    source_page: int | None = None
    token_count: int = 0
    bboxes: list[ChunkBbox] = field(default_factory=list)
    doc_items: list[ChunkDocItem] = field(default_factory=list)
