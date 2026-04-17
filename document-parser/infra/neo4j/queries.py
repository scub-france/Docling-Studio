"""Reusable Cypher queries — kept out of the API layer for reuse + testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infra.neo4j.driver import Neo4jDriver


@dataclass
class GraphPayload:
    doc_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    node_count: int
    edge_count: int
    truncated: bool
    page_count: int


# Full graph for one doc: Document + Elements + Pages + Chunks and their edges.
# The graph is returned as flat node + edge lists ready for cytoscape.
_FETCH_GRAPH = """
MATCH (d:Document {id: $doc_id})
OPTIONAL MATCH (d)-[:HAS_ROOT]->(root:Element)
OPTIONAL MATCH (e:Element {doc_id: $doc_id})
OPTIONAL MATCH (p:Page {doc_id: $doc_id})
OPTIONAL MATCH (c:Chunk {doc_id: $doc_id})
WITH d,
     collect(DISTINCT e) AS elements,
     collect(DISTINCT p) AS pages,
     collect(DISTINCT c) AS chunks
OPTIONAL MATCH (pe:Element {doc_id: $doc_id})-[r_po:PARENT_OF]->(ce:Element {doc_id: $doc_id})
OPTIONAL MATCH (a:Element {doc_id: $doc_id})-[r_nx:NEXT]->(b:Element {doc_id: $doc_id})
OPTIONAL MATCH (er:Element {doc_id: $doc_id})-[r_op:ON_PAGE]->(pr:Page {doc_id: $doc_id})
OPTIONAL MATCH (d)-[r_hr:HAS_ROOT]->(rr:Element {doc_id: $doc_id})
OPTIONAL MATCH (d)-[r_hc:HAS_CHUNK]->(rc:Chunk {doc_id: $doc_id})
OPTIONAL MATCH (cc:Chunk {doc_id: $doc_id})-[r_df:DERIVED_FROM]->(ee:Element {doc_id: $doc_id})
RETURN
  d AS document,
  elements, pages, chunks,
  collect(DISTINCT {from: pe.self_ref, to: ce.self_ref, order: r_po.order, type: 'PARENT_OF'}) AS parent_edges,
  collect(DISTINCT {from: a.self_ref, to: b.self_ref, type: 'NEXT'}) AS next_edges,
  collect(DISTINCT {from: er.self_ref, to: pr.page_no, type: 'ON_PAGE'}) AS on_page_edges,
  collect(DISTINCT {from: d.id, to: rr.self_ref, type: 'HAS_ROOT'}) AS has_root_edges,
  collect(DISTINCT {from: d.id, to: rc.id, type: 'HAS_CHUNK'}) AS has_chunk_edges,
  collect(DISTINCT {from: cc.id, to: ee.self_ref, type: 'DERIVED_FROM'}) AS derived_from_edges
"""


def _element_node(doc_id: str, e: dict[str, Any]) -> dict[str, Any]:
    # Determine the specific element label: Neo4j returns it via labels(e) on the
    # driver side; when we project nodes via RETURN, the driver wraps them as Node
    # objects, so we convert below.
    return {
        "id": f"elem::{e.get('self_ref')}",
        "group": "element",
        "docling_label": e.get("docling_label"),
        "self_ref": e.get("self_ref"),
        "text": (e.get("text") or "")[:200],
        "prov_page": e.get("prov_page"),
        "level": e.get("level"),
        "doc_id": doc_id,
    }


def _page_node(doc_id: str, p: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"page::{p.get('page_no')}",
        "group": "page",
        "page_no": p.get("page_no"),
        "width": p.get("width"),
        "height": p.get("height"),
        "doc_id": doc_id,
    }


def _chunk_node(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"chunk::{p.get('id')}",
        "group": "chunk",
        "chunk_index": p.get("chunk_index"),
        "text": (p.get("text") or "")[:200],
        "token_count": p.get("token_count"),
    }


def _edge_id(from_id: str, to_id: str, edge_type: str) -> str:
    return f"{edge_type}::{from_id}::{to_id}"


async def fetch_graph(
    neo: Neo4jDriver,
    doc_id: str,
    *,
    max_pages: int = 200,
) -> GraphPayload | None:
    """Return the full graph for a document, or None if the document is unknown.

    Enforces the page cap from design §8.4: beyond `max_pages`, returns a
    `truncated=True` payload with empty node/edge lists so the caller can
    surface a clean error (HTTP 413) to the UI.
    """
    async with neo.driver.session(database=neo.database) as session:
        page_count_result = await session.run(
            "MATCH (p:Page {doc_id: $doc_id}) RETURN count(p) AS n",
            doc_id=doc_id,
        )
        pc_record = await page_count_result.single()
        if pc_record is None:
            return None
        page_count = int(pc_record["n"])

        exists_result = await session.run(
            "MATCH (d:Document {id: $doc_id}) RETURN count(d) AS n",
            doc_id=doc_id,
        )
        exists_record = await exists_result.single()
        if not exists_record or exists_record["n"] == 0:
            return None

        if page_count > max_pages:
            return GraphPayload(
                doc_id=doc_id,
                nodes=[],
                edges=[],
                node_count=0,
                edge_count=0,
                truncated=True,
                page_count=page_count,
            )

        result = await session.run(_FETCH_GRAPH, doc_id=doc_id)
        record = await result.single()

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    if record is None:
        return None

    # Document node.
    doc_node = record["document"]
    if doc_node is not None:
        nodes.append(
            {
                "id": f"doc::{doc_id}",
                "group": "document",
                "doc_id": doc_id,
                "title": doc_node.get("title"),
                "stages_applied": doc_node.get("stages_applied"),
            }
        )

    # Element nodes, keeping the specific label (:SectionHeader, etc.).
    for e in record["elements"] or []:
        if e is None:
            continue
        labels = [label for label in e.labels if label != "Element"]
        node = _element_node(doc_id, dict(e))
        node["label"] = labels[0] if labels else "TextElement"
        nodes.append(node)

    # Pages.
    for p in record["pages"] or []:
        if p is None:
            continue
        nodes.append(_page_node(doc_id, dict(p)))

    # Chunks.
    for c in record["chunks"] or []:
        if c is None:
            continue
        nodes.append(_chunk_node(dict(c)))

    # Edges — filter out rows whose from/to is null (OPTIONAL MATCH can yield them).
    def _push_element_edge(e: dict[str, Any], from_prefix: str, to_prefix: str) -> None:
        frm, to = e.get("from"), e.get("to")
        if frm is None or to is None:
            return
        edges.append(
            {
                "id": _edge_id(f"{from_prefix}{frm}", f"{to_prefix}{to}", e["type"]),
                "source": f"{from_prefix}{frm}",
                "target": f"{to_prefix}{to}",
                "type": e["type"],
                "order": e.get("order"),
            }
        )

    for e in record["parent_edges"] or []:
        _push_element_edge(e, "elem::", "elem::")
    for e in record["next_edges"] or []:
        _push_element_edge(e, "elem::", "elem::")
    for e in record["on_page_edges"] or []:
        _push_element_edge(e, "elem::", "page::")
    for e in record["has_root_edges"] or []:
        _push_element_edge(e, "doc::", "elem::")
    for e in record["has_chunk_edges"] or []:
        _push_element_edge(e, "doc::", "chunk::")
    for e in record["derived_from_edges"] or []:
        _push_element_edge(e, "chunk::", "elem::")

    return GraphPayload(
        doc_id=doc_id,
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
        truncated=False,
        page_count=page_count,
    )
