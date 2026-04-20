"""TreeWriter — persist a DoclingDocument as a graph in Neo4j.

v0.5.0 strategy: replace-on-write. For a given doc_id, all existing
Document/Element/Page/Chunk nodes are wiped before re-ingestion. The full
serialized `DoclingDocument` JSON is stored as a property on the Document
node so that `TreeReader` can round-trip it verbatim — reconstruction from
graph nodes is deferred to v0.6 (see docs/design/neo4j-integration.md §2).
"""

from __future__ import annotations

import contextlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infra.neo4j.driver import Neo4jDriver

logger = logging.getLogger(__name__)


# Docling label → specific Neo4j label. Every node also carries :Element.
_LABEL_MAP: dict[str, str] = {
    "section_header": "SectionHeader",
    "title": "SectionHeader",
    "paragraph": "Paragraph",
    "text": "Paragraph",
    "list_item": "ListItem",
    "list": "ListItem",
    "table": "Table",
    "picture": "Figure",
    "formula": "Formula",
    "code": "Code",
    "caption": "Caption",
    "footnote": "Footnote",
    "page_header": "PageHeader",
    "page_footer": "PageFooter",
}
_DEFAULT_LABEL = "TextElement"


def _element_label(docling_label: str) -> str:
    return _LABEL_MAP.get(docling_label.lower(), _DEFAULT_LABEL)


@dataclass
class TreeWriteResult:
    doc_id: str
    elements_written: int
    pages_written: int


def _iter_items(doc_data: dict[str, Any]):
    """Yield every item from texts/tables/pictures/groups with its source list."""
    for key in ("texts", "tables", "pictures", "groups"):
        for item in doc_data.get(key, []) or []:
            yield key, item


def _first_prov(item: dict[str, Any]) -> tuple[int | None, list[float] | None]:
    prov = item.get("prov") or []
    if not prov:
        return None, None
    p0 = prov[0]
    bbox = p0.get("bbox")
    bbox_list: list[float] | None = None
    if isinstance(bbox, dict):
        bbox_list = [bbox.get("l", 0.0), bbox.get("t", 0.0), bbox.get("r", 0.0), bbox.get("b", 0.0)]
    elif isinstance(bbox, list):
        bbox_list = list(bbox)
    return p0.get("page_no"), bbox_list


def _parent_ref(item: dict[str, Any]) -> str | None:
    parent = item.get("parent")
    if isinstance(parent, dict):
        return parent.get("$ref") or parent.get("cref")
    return None


def _element_props(item: dict[str, Any], doc_id: str) -> dict[str, Any]:
    page, bbox = _first_prov(item)
    props: dict[str, Any] = {
        "doc_id": doc_id,
        "self_ref": item.get("self_ref") or "",
        "docling_label": (item.get("label") or "").lower(),
        "text": item.get("text") or "",
        "prov_page": page,
        "prov_bbox": bbox,
    }
    # Type-specific extras.
    if "level" in item:
        props["level"] = item.get("level")
    if "caption" in item and isinstance(item.get("caption"), str):
        props["caption"] = item.get("caption")
    if item.get("data") and isinstance(item["data"], dict):
        # Tables carry cell layout under data; stringify to keep the schema flat.
        with contextlib.suppress(TypeError, ValueError):
            props["cells_json"] = json.dumps(item["data"])
    return props


def _dfs_order(doc_data: dict[str, Any]) -> list[str]:
    """Return self_refs in reading order (DFS pre-order from body)."""
    by_ref: dict[str, dict[str, Any]] = {}
    for _, item in _iter_items(doc_data):
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


async def write_document(
    neo: Neo4jDriver,
    *,
    doc_id: str,
    filename: str,
    document_json: str,
    tenant_id: str = "default",
    source_uri: str | None = None,
    docling_version: str | None = None,
) -> TreeWriteResult:
    """Persist the full DoclingDocument tree to Neo4j.

    Idempotent: wipes any existing graph for doc_id before writing.
    Fails fast (exception propagates) if Neo4j is unavailable — per design §8.5.
    """
    doc_data = json.loads(document_json)
    ingested_at = datetime.now(tz=UTC).isoformat()

    elements: list[dict[str, Any]] = []
    for _, item in _iter_items(doc_data):
        ref = item.get("self_ref")
        if not ref:
            continue
        specific = _element_label(item.get("label") or "")
        elements.append(
            {
                "specific_label": specific,
                "parent_ref": _parent_ref(item),
                **_element_props(item, doc_id),
            }
        )

    pages: list[dict[str, Any]] = []
    for page_no_str, page_obj in (doc_data.get("pages") or {}).items():
        try:
            page_no = int(page_no_str)
        except (TypeError, ValueError):
            continue
        size = page_obj.get("size") or {}
        pages.append(
            {
                "doc_id": doc_id,
                "page_no": page_no,
                "width": size.get("width"),
                "height": size.get("height"),
            }
        )

    reading_order = _dfs_order(doc_data)

    async with (
        neo.driver.session(database=neo.database) as session,
        await session.begin_transaction() as tx,
    ):
        # 1. Wipe existing graph for this doc_id (replace strategy).
        await tx.run(
            "MATCH (d:Document {id: $doc_id}) "
            "OPTIONAL MATCH (d)-[:HAS_ROOT|HAS_CHUNK*0..]->(n) "
            "DETACH DELETE d, n",
            doc_id=doc_id,
        )
        # Also wipe orphan elements/chunks that may still reference this doc.
        await tx.run("MATCH (e:Element {doc_id: $doc_id}) DETACH DELETE e", doc_id=doc_id)
        await tx.run("MATCH (p:Page {doc_id: $doc_id}) DETACH DELETE p", doc_id=doc_id)

        # 2. Document node (carries the verbatim JSON for TreeReader).
        await tx.run(
            """
                CREATE (d:Document {
                  id: $doc_id,
                  title: $title,
                  source_uri: $source_uri,
                  ingested_at: datetime($ingested_at),
                  docling_version: $docling_version,
                  stages_applied: ['tree'],
                  last_tree_write: datetime($ingested_at),
                  tenant_id: $tenant_id,
                  document_json: $document_json
                })
                """,
            doc_id=doc_id,
            title=filename,
            source_uri=source_uri or "",
            ingested_at=ingested_at,
            docling_version=docling_version or "",
            tenant_id=tenant_id,
            document_json=document_json,
        )

        # 3. Page nodes.
        if pages:
            await tx.run(
                "UNWIND $pages AS p "
                "CREATE (:Page {doc_id: p.doc_id, page_no: p.page_no, "
                "width: p.width, height: p.height})",
                pages=pages,
            )

        # 4. Element nodes — use dynamic :Element:<specific> labels via APOC-free trick.
        # We split by specific label so the CREATE statement is static (no APOC).
        by_specific: dict[str, list[dict[str, Any]]] = {}
        for e in elements:
            by_specific.setdefault(e["specific_label"], []).append(e)
        for specific, batch in by_specific.items():
            await tx.run(
                f"""
                    UNWIND $batch AS e
                    CREATE (n:Element:{specific} {{
                      doc_id: e.doc_id,
                      self_ref: e.self_ref,
                      docling_label: e.docling_label,
                      text: e.text,
                      prov_page: e.prov_page,
                      prov_bbox: e.prov_bbox,
                      level: e.level,
                      caption: e.caption,
                      cells_json: e.cells_json
                    }})
                    """,
                batch=batch,
            )

        # 5. PARENT_OF relations (tree structure). Order tracked inline.
        parent_rows = [
            {
                "doc_id": doc_id,
                "parent_ref": e["parent_ref"],
                "child_ref": e["self_ref"],
                "order": idx,
            }
            for idx, e in enumerate(elements)
            if e["parent_ref"] and e["parent_ref"] != "#/body"
        ]
        if parent_rows:
            await tx.run(
                """
                    UNWIND $rows AS r
                    MATCH (p:Element {doc_id: r.doc_id, self_ref: r.parent_ref})
                    MATCH (c:Element {doc_id: r.doc_id, self_ref: r.child_ref})
                    MERGE (p)-[rel:PARENT_OF]->(c)
                    SET rel.order = r.order
                    """,
                rows=parent_rows,
            )

        # 6. HAS_ROOT for top-level children of the document body.
        root_rows = [
            {"doc_id": doc_id, "child_ref": e["self_ref"]}
            for e in elements
            if e["parent_ref"] == "#/body"
        ]
        if root_rows:
            await tx.run(
                """
                    UNWIND $rows AS r
                    MATCH (d:Document {id: r.doc_id})
                    MATCH (c:Element {doc_id: r.doc_id, self_ref: r.child_ref})
                    MERGE (d)-[:HAS_ROOT]->(c)
                    """,
                rows=root_rows,
            )

        # 7. ON_PAGE from first provenance.
        on_page_rows = [
            {"doc_id": doc_id, "self_ref": e["self_ref"], "page_no": e["prov_page"]}
            for e in elements
            if e["prov_page"] is not None
        ]
        if on_page_rows:
            await tx.run(
                """
                    UNWIND $rows AS r
                    MATCH (e:Element {doc_id: r.doc_id, self_ref: r.self_ref})
                    MATCH (p:Page {doc_id: r.doc_id, page_no: r.page_no})
                    MERGE (e)-[:ON_PAGE]->(p)
                    """,
                rows=on_page_rows,
            )

        # 8. NEXT chain in DFS pre-order.
        if len(reading_order) > 1:
            pairs = [
                {"doc_id": doc_id, "a": reading_order[i], "b": reading_order[i + 1]}
                for i in range(len(reading_order) - 1)
            ]
            await tx.run(
                """
                    UNWIND $pairs AS p
                    MATCH (a:Element {doc_id: p.doc_id, self_ref: p.a})
                    MATCH (b:Element {doc_id: p.doc_id, self_ref: p.b})
                    MERGE (a)-[:NEXT]->(b)
                    """,
                pairs=pairs,
            )

        await tx.commit()

    logger.info(
        "Neo4j: wrote doc %s (%d elements, %d pages)",
        doc_id,
        len(elements),
        len(pages),
    )
    return TreeWriteResult(doc_id=doc_id, elements_written=len(elements), pages_written=len(pages))
