"""Domain value objects — pure data structures for document conversion.

These types define the contract between the domain and infrastructure layers.
They have ZERO external dependencies (no docling, no HTTP, no DB).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PageElement:
    type: str
    bbox: list[float]
    content: str
    level: int = 0


@dataclass
class PageDetail:
    page_number: int
    width: float
    height: float
    elements: list[PageElement] = field(default_factory=list)


@dataclass
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
        return self == ConversionOptions()


@dataclass
class ConversionResult:
    page_count: int
    content_markdown: str
    content_html: str
    pages: list[PageDetail]
    skipped_items: int = 0
    document_json: str | None = None


@dataclass
class ChunkingOptions:
    chunker_type: str = "hybrid"  # "hybrid", "hierarchical", "page"
    max_tokens: int = 512
    merge_peers: bool = True
    repeat_table_header: bool = True

    def is_default(self) -> bool:
        return self == ChunkingOptions()


@dataclass
class ChunkResult:
    text: str
    headings: list[str] = field(default_factory=list)
    source_page: int | None = None
    token_count: int = 0
