import io
import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from docling.document_converter import DocumentConverter
from pdf2image import convert_from_bytes
from PIL import Image

from bbox import to_topleft_list

logger = logging.getLogger(__name__)

app = FastAPI(title="Docling Studio - Document Parser")

converter = DocumentConverter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# --- Response models ---

class PageElement(BaseModel):
    type: str
    bbox: list[float]
    content: str


class PageDetail(BaseModel):
    page_number: int
    width: float
    height: float
    elements: list[PageElement]


class ParseResponse(BaseModel):
    filename: str
    page_count: int
    content_markdown: str
    content_html: str
    pages: list[PageDetail]


# --- Helpers ---

def extract_pages_detail(doc_result) -> list[PageDetail]:
    """Extract per-page element details with bounding boxes from Docling result.

    Uses Docling's iterate_items() API (preferred) or falls back to document.texts.
    Both provide a flat iteration over all content items, avoiding duplicates.
    """
    pages: dict[int, PageDetail] = {}
    document = doc_result.document

    # Get page dimensions from document pages
    if hasattr(document, 'pages') and document.pages:
        for page_key, page_obj in document.pages.items():
            page_no = int(page_key) if isinstance(page_key, str) else page_key
            width = page_obj.size.width if hasattr(page_obj, 'size') and page_obj.size else 612.0
            height = page_obj.size.height if hasattr(page_obj, 'size') and page_obj.size else 792.0
            pages[page_no] = PageDetail(
                page_number=page_no,
                width=width,
                height=height,
                elements=[]
            )

    # Use iterate_items() (Docling v2 API) — avoids duplicates
    if hasattr(document, 'iterate_items'):
        for item, _level in document.iterate_items():
            _process_content_item(item, pages)
    elif hasattr(document, 'texts'):
        for text_item in document.texts:
            _process_content_item(text_item, pages)

    # Sort by page number
    return sorted(pages.values(), key=lambda p: p.page_number)


def _process_content_item(item, pages: dict[int, PageDetail]):
    """Process a single content item and add it to the appropriate page.

    Silently skips items that lack provenance or fail to process,
    so one bad item doesn't break the whole extraction.
    """
    if not hasattr(item, 'prov') or not item.prov:
        return

    for prov in item.prov:
        try:
            page_no = prov.page_no if hasattr(prov, 'page_no') else 1

            if page_no not in pages:
                pages[page_no] = PageDetail(
                    page_number=page_no, width=612.0, height=792.0, elements=[]
                )

            page_height = pages[page_no].height

            bbox = [0, 0, 0, 0]
            if hasattr(prov, 'bbox') and prov.bbox:
                b = prov.bbox
                if hasattr(b, 'l'):
                    bbox = to_topleft_list(b, page_height)
                elif isinstance(b, (list, tuple)) and len(b) >= 4:
                    bbox = list(b[:4])

            element_type = _get_element_type(item)
            content = ""
            if hasattr(item, 'text'):
                content = item.text or ""

            pages[page_no].elements.append(PageElement(
                type=element_type,
                bbox=bbox,
                content=content[:500]
            ))
        except Exception:
            logger.warning("Skipping item %s: failed to process", type(item).__name__, exc_info=True)



def _get_element_type(item) -> str:
    """Determine the element type from a Docling document item."""
    type_name = type(item).__name__.lower()
    if 'table' in type_name:
        return 'table'
    if 'picture' in type_name or 'image' in type_name or 'figure' in type_name:
        return 'picture'
    if 'section' in type_name or 'heading' in type_name:
        return 'section_header'
    if 'list' in type_name:
        return 'list'
    if 'formula' in type_name or 'equation' in type_name:
        return 'formula'
    if 'caption' in type_name:
        return 'caption'
    if hasattr(item, 'label'):
        label = str(item.label).lower()
        if 'table' in label:
            return 'table'
        if 'picture' in label or 'figure' in label:
            return 'picture'
        if 'section' in label or 'head' in label:
            return 'section_header'
        if 'list' in label:
            return 'list'
        if 'formula' in label:
            return 'formula'
    return 'text'


# --- Endpoints ---

@app.post("/parse", response_model=ParseResponse)
async def parse(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    suffix = Path(file.filename).suffix
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = converter.convert(tmp_path)
        doc = result.document

        content_markdown = doc.export_to_markdown()
        content_html = doc.export_to_html() if hasattr(doc, 'export_to_html') else ""

        page_count = 0
        if hasattr(doc, 'pages') and doc.pages:
            page_count = len(doc.pages)

        pages_detail = extract_pages_detail(result)
        if not pages_detail and page_count > 0:
            pages_detail = [
                PageDetail(page_number=i + 1, width=612.0, height=792.0, elements=[])
                for i in range(page_count)
            ]

        return ParseResponse(
            filename=file.filename,
            page_count=page_count or len(pages_detail) or 1,
            content_markdown=content_markdown,
            content_html=content_html,
            pages=pages_detail,
        )

    except Exception as e:
        logger.exception("Failed to parse document: %s", file.filename)
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/preview")
async def preview(
    file: UploadFile,
    page: int = Query(1, ge=1),
    dpi: int = Query(150, ge=72, le=300),
):
    """Generate a PNG preview of a specific page."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    try:
        images = convert_from_bytes(content, first_page=page, last_page=page, dpi=dpi)
        if not images:
            raise HTTPException(status_code=404, detail=f"Page {page} not found")

        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to generate preview: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}
