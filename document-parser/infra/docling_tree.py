"""Pure helpers over a serialized `DoclingDocument` dict.

No I/O, no Neo4j. Shared between:
- `infra.neo4j.tree_writer` — persists the tree into Neo4j during the Maintain
  step (IngestionPipeline).
- `infra.docling_graph` — builds an in-memory `GraphPayload` from the SQLite
  `document_json` blob for the reasoning-trace viewer.

Keep this module the single source of truth for how we read Docling's own
structure, so the two consumers can't drift.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

# Docling label -> specific Neo4j/Cytoscape label. Every element carries the
# generic :Element tag too. Kept 1:1 with docling-core's label taxonomy so the
# projection is a faithful mirror of the DoclingDocument.
LABEL_MAP: dict[str, str] = {
    "section_header": "SectionHeader",
    "title": "SectionHeader",
    "paragraph": "Paragraph",
    "text": "Paragraph",
    "list_item": "ListItem",
    "list": "List",  # distinct from :ListItem — a list is a container
    "table": "Table",
    "picture": "Figure",
    "formula": "Formula",
    "code": "Code",
    "caption": "Caption",
    "footnote": "Footnote",
    "page_header": "PageHeader",
    "page_footer": "PageFooter",
    "key_value_area": "KeyValueArea",
    "form_area": "FormArea",
    "document_index": "DocumentIndex",
}
DEFAULT_LABEL = "TextElement"


def element_label(docling_label: str) -> str:
    return LABEL_MAP.get(docling_label.lower(), DEFAULT_LABEL)


def iter_items(doc_data: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield every item from texts/tables/pictures/groups with its source list key."""
    for key in ("texts", "tables", "pictures", "groups"):
        for item in doc_data.get(key, []) or []:
            yield key, item


def parent_ref(item: dict[str, Any]) -> str | None:
    parent = item.get("parent")
    if isinstance(parent, dict):
        return parent.get("$ref") or parent.get("cref")
    return None


def iter_provs(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a Docling item's `prov[]` into a list of dict rows.

    A single item may have multiple provs when it spans page breaks or appears
    more than once in the layout. The returned dicts carry the original index
    under `order` so sequence is preserved.
    """
    provs = item.get("prov") or []
    rows: list[dict[str, Any]] = []
    for idx, p in enumerate(provs):
        bbox = p.get("bbox")
        l_, t_, r_, b_ = 0.0, 0.0, 0.0, 0.0
        if isinstance(bbox, dict):
            l_ = float(bbox.get("l", 0.0) or 0.0)
            t_ = float(bbox.get("t", 0.0) or 0.0)
            r_ = float(bbox.get("r", 0.0) or 0.0)
            b_ = float(bbox.get("b", 0.0) or 0.0)
        elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            l_, t_, r_, b_ = (float(x) for x in bbox[:4])
        coord_origin = (bbox.get("coord_origin") if isinstance(bbox, dict) else None) or "TOPLEFT"
        charspan = p.get("charspan") or []
        rows.append(
            {
                "order": idx,
                "page_no": p.get("page_no"),
                "bbox_l": l_,
                "bbox_t": t_,
                "bbox_r": r_,
                "bbox_b": b_,
                "coord_origin": coord_origin,
                "charspan_start": int(charspan[0]) if len(charspan) >= 1 else None,
                "charspan_end": int(charspan[1]) if len(charspan) >= 2 else None,
            }
        )
    return rows


def dfs_order(doc_data: dict[str, Any]) -> list[str]:
    """Return `self_ref`s in reading order (DFS pre-order from body)."""
    by_ref: dict[str, dict[str, Any]] = {}
    for _, item in iter_items(doc_data):
        ref = item.get("self_ref")
        if ref:
            by_ref[ref] = item
    body = doc_data.get("body") or {}
    order: list[str] = []

    def walk(children: list[dict[str, Any]] | None) -> None:
        if not children:
            return
        for ch in children:
            ref = ch.get("$ref") or ch.get("cref")
            if not ref:
                continue
            order.append(ref)
            child = by_ref.get(ref)
            if child:
                walk(child.get("children"))

    walk(body.get("children"))
    return order


def iter_pages(doc_data: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield page dicts with `page_no`, `width`, `height` from the `pages` map."""
    for page_no_str, page_obj in (doc_data.get("pages") or {}).items():
        try:
            page_no = int(page_no_str)
        except (TypeError, ValueError):
            continue
        size = (page_obj or {}).get("size") or {}
        yield {
            "page_no": page_no,
            "width": size.get("width"),
            "height": size.get("height"),
        }
