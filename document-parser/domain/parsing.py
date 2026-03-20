"""Docling document extraction logic — pure domain, no HTTP concerns.

Wraps the Docling library to convert documents and extract structured
per-page elements with bounding boxes and hierarchy levels.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling_core.types.doc import (
    CodeItem,
    DocItem,
    FloatingItem,
    FormulaItem,
    GroupItem,
    ListItem,
    PictureItem,
    SectionHeaderItem,
    TableItem,
    TextItem,
    TitleItem,
)

from domain.bbox import to_topleft_list

logger = logging.getLogger(__name__)

# Thread lock — DocumentConverter is not thread-safe
_converter_lock = threading.Lock()

# Default converter (lazy-init on first request)
_default_converter: DocumentConverter | None = None


# ---------------------------------------------------------------------------
# Domain value objects
# ---------------------------------------------------------------------------

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
class ConversionResult:
    page_count: int
    content_markdown: str
    content_html: str
    pages: list[PageDetail]
    skipped_items: int = 0


# ---------------------------------------------------------------------------
# Element type detection
# ---------------------------------------------------------------------------

# Mapping from Docling type to element type string.
# Order matters: most specific types before their parents.
_ELEMENT_TYPE_MAP: list[tuple[type, str]] = [
    (TableItem, "table"),
    (PictureItem, "picture"),
    (TitleItem, "title"),
    (SectionHeaderItem, "section_header"),
    (ListItem, "list"),
    (FormulaItem, "formula"),
    (CodeItem, "code"),
    (FloatingItem, "floating"),
    (TextItem, "text"),
]


def _get_element_type(item: DocItem) -> str:
    """Determine element type via isinstance on Docling's type hierarchy."""
    for cls, type_name in _ELEMENT_TYPE_MAP:
        if isinstance(item, cls):
            return type_name
    return "text"


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def build_converter(
    do_ocr: bool = True,
    do_table_structure: bool = True,
    table_mode: str = "accurate",
    do_code_enrichment: bool = False,
    do_formula_enrichment: bool = False,
    do_picture_classification: bool = False,
    do_picture_description: bool = False,
    generate_picture_images: bool = False,
    generate_page_images: bool = False,
    images_scale: float = 1.0,
) -> DocumentConverter:
    """Build a DocumentConverter with the given pipeline options."""
    table_options = TableStructureOptions(
        do_cell_matching=True,
        mode=TableFormerMode.ACCURATE if table_mode == "accurate" else TableFormerMode.FAST,
    )

    pipeline_options = PdfPipelineOptions(
        do_ocr=do_ocr,
        do_table_structure=do_table_structure,
        table_structure_options=table_options,
        do_code_enrichment=do_code_enrichment,
        do_formula_enrichment=do_formula_enrichment,
        do_picture_classification=do_picture_classification,
        do_picture_description=do_picture_description,
        generate_page_images=generate_page_images,
        generate_picture_images=generate_picture_images,
        images_scale=images_scale,
    )

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def get_default_converter() -> DocumentConverter:
    global _default_converter
    if _default_converter is None:
        _default_converter = build_converter()
    return _default_converter


# ---------------------------------------------------------------------------
# Page extraction
# ---------------------------------------------------------------------------

def extract_pages_detail(doc_result) -> tuple[list[PageDetail], int]:
    """Extract per-page element details with bounding boxes from Docling result.

    Returns (pages, skipped_count) for transparent error reporting.
    """
    pages: dict[int, PageDetail] = {}
    document = doc_result.document
    skipped = 0

    for page_key, page_obj in document.pages.items():
        page_no = int(page_key) if isinstance(page_key, str) else page_key
        pages[page_no] = PageDetail(
            page_number=page_no,
            width=page_obj.size.width,
            height=page_obj.size.height,
        )

    for item, level in document.iterate_items():
        ok = _process_content_item(item, level, pages)
        if not ok:
            skipped += 1

    sorted_pages = sorted(pages.values(), key=lambda p: p.page_number)
    return sorted_pages, skipped


def _process_content_item(
    item: DocItem | GroupItem, level: int, pages: dict[int, PageDetail],
) -> bool:
    """Process a single content item and add it to the appropriate page."""
    if isinstance(item, GroupItem):
        return True

    if not isinstance(item, DocItem) or not item.prov:
        return False

    for prov in item.prov:
        try:
            page_no = prov.page_no
            if page_no not in pages:
                pages[page_no] = PageDetail(page_number=page_no, width=612.0, height=792.0)

            page_height = pages[page_no].height

            bbox = [0.0, 0.0, 0.0, 0.0]
            if prov.bbox:
                bbox = to_topleft_list(prov.bbox, page_height)

            element_type = _get_element_type(item)

            content = getattr(item, "text", "") or ""
            if isinstance(item, TableItem):
                try:
                    content = item.export_to_markdown()
                except Exception:
                    pass

            pages[page_no].elements.append(
                PageElement(type=element_type, bbox=bbox, content=content, level=level)
            )
        except Exception:
            logger.warning(
                "Skipping item %s on page %s",
                type(item).__name__,
                getattr(prov, "page_no", "?"),
                exc_info=True,
            )
            return False

    return True


# ---------------------------------------------------------------------------
# Main conversion entry point
# ---------------------------------------------------------------------------

def convert_document(
    file_path: str,
    *,
    do_ocr: bool = True,
    do_table_structure: bool = True,
    table_mode: str = "accurate",
    do_code_enrichment: bool = False,
    do_formula_enrichment: bool = False,
    do_picture_classification: bool = False,
    do_picture_description: bool = False,
    generate_picture_images: bool = False,
    generate_page_images: bool = False,
    images_scale: float = 1.0,
) -> ConversionResult:
    """Convert a document and return structured results.

    This is the main entry point for document parsing. Runs synchronously
    (caller should use asyncio.to_thread for non-blocking execution).
    """
    # Use cached default converter only when all options match defaults
    is_default = (
        do_ocr and do_table_structure and table_mode == "accurate"
        and not do_code_enrichment and not do_formula_enrichment
        and not do_picture_classification and not do_picture_description
        and not generate_picture_images and not generate_page_images
        and images_scale == 1.0
    )

    if is_default:
        conv = get_default_converter()
    else:
        conv = build_converter(
            do_ocr=do_ocr,
            do_table_structure=do_table_structure,
            table_mode=table_mode,
            do_code_enrichment=do_code_enrichment,
            do_formula_enrichment=do_formula_enrichment,
            do_picture_classification=do_picture_classification,
            do_picture_description=do_picture_description,
            generate_picture_images=generate_picture_images,
            generate_page_images=generate_page_images,
            images_scale=images_scale,
        )

    with _converter_lock:
        result = conv.convert(file_path)

    doc = result.document
    content_markdown = doc.export_to_markdown()
    content_html = doc.export_to_html()
    page_count = len(doc.pages)

    pages_detail, skipped = extract_pages_detail(result)

    if not pages_detail and page_count > 0:
        pages_detail = [
            PageDetail(
                page_number=i + 1,
                width=doc.pages[i + 1].size.width if (i + 1) in doc.pages else 612.0,
                height=doc.pages[i + 1].size.height if (i + 1) in doc.pages else 792.0,
            )
            for i in range(page_count)
        ]

    if skipped > 0:
        logger.info("Parsed: %d pages, %d items skipped", page_count, skipped)

    return ConversionResult(
        page_count=page_count or len(pages_detail) or 1,
        content_markdown=content_markdown,
        content_html=content_html,
        pages=pages_detail,
        skipped_items=skipped,
    )
