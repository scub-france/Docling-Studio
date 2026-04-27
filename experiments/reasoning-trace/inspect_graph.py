#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "neo4j>=5.20,<6",
# ]
# ///
"""
Compare the Neo4j graph for a given doc_id against the source DoclingDocument
stored in SQLite. Reports whether the graph is "well-formed" — all elements
present, hierarchy intact, no orphans, reading order faithful.

Use when you want to sanity-check the Neo4j writer before building anything
on top of the graph (e.g. the live RAG overlay).

Usage:
    uv run experiments/reasoning-trace/inspect_graph.py \\
        --doc-id 307ad2ba-93d8-4dfd-8e38-c1ea06d23f0d

Env:
    NEO4J_URI        default bolt://localhost:7687
    NEO4J_USER       default neo4j
    NEO4J_PASSWORD   default changeme
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DB_PATH = REPO / "document-parser" / "data" / "docling_studio.db"


def _load_doc_json(doc_id: str) -> tuple[str, dict]:
    """Return (filename, parsed DoclingDocument dict) for the latest completed
    analysis of this doc."""
    if not DB_PATH.exists():
        sys.exit(f"SQLite DB not found at {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        """
        SELECT d.filename, aj.document_json
        FROM analysis_jobs aj
        JOIN documents d ON d.id = aj.document_id
        WHERE aj.document_id = ?
          AND aj.status = 'COMPLETED'
          AND aj.document_json IS NOT NULL
        ORDER BY aj.completed_at DESC LIMIT 1
        """,
        (doc_id,),
    ).fetchone()
    con.close()
    if not row:
        sys.exit(f"No completed analysis with document_json for doc_id={doc_id}")
    return row["filename"], json.loads(row["document_json"])


# ---------------------------------------------------------------------------
# Source-side summaries (DoclingDocument JSON)
# ---------------------------------------------------------------------------
_ITEM_LISTS = ("texts", "tables", "pictures", "groups")


def _iter_items(doc: dict):
    for key in _ITEM_LISTS:
        for it in doc.get(key) or []:
            yield key, it


def _parent_ref(item: dict) -> str | None:
    parent = item.get("parent")
    if isinstance(parent, dict):
        return parent.get("$ref") or parent.get("cref")
    return None


def _dfs_reading_order(doc: dict) -> list[str]:
    by_ref: dict[str, dict] = {}
    for _, it in _iter_items(doc):
        ref = it.get("self_ref")
        if ref:
            by_ref[ref] = it
    body = doc.get("body") or {}
    order: list[str] = []

    def walk(children):
        for ch in children or []:
            ref = ch.get("$ref") or ch.get("cref")
            if not ref:
                continue
            order.append(ref)
            walk((by_ref.get(ref) or {}).get("children"))

    walk(body.get("children"))
    return order


def _summarize_source(doc: dict) -> dict:
    items_by_kind = Counter()
    labels = Counter()
    roots_from_body = 0
    with_prov = 0
    no_text_no_caption = 0
    section_headers: list[str] = []

    for kind, it in _iter_items(doc):
        items_by_kind[kind] += 1
        label = (it.get("label") or "").lower()
        labels[label] += 1
        if _parent_ref(it) == "#/body":
            roots_from_body += 1
        if it.get("prov"):
            with_prov += 1
        if not (it.get("text") or it.get("caption")):
            no_text_no_caption += 1
        if label in ("section_header", "title"):
            section_headers.append(it.get("self_ref") or "<?>")

    pages = doc.get("pages") or {}
    reading_order = _dfs_reading_order(doc)

    return {
        "filename_in_doc": doc.get("name"),
        "items_by_kind": dict(items_by_kind),
        "labels": dict(labels),
        "total_items": sum(items_by_kind.values()),
        "section_headers_count": len(section_headers),
        "section_headers_sample": section_headers[:5],
        "roots_from_body": roots_from_body,
        "items_with_prov": with_prov,
        "items_without_prov": sum(items_by_kind.values()) - with_prov,
        "items_without_text_nor_caption": no_text_no_caption,
        "pages_count": len(pages),
        "reading_order_length": len(reading_order),
        "reading_order_sample": reading_order[:5],
    }


# ---------------------------------------------------------------------------
# Graph-side summaries (Neo4j)
# ---------------------------------------------------------------------------
async def _summarize_graph(neo, doc_id: str) -> dict:
    async with neo.driver.session(database=neo.database) as s:

        async def q(cypher: str, **params) -> list[dict]:
            res = await s.run(cypher, doc_id=doc_id, **params)
            return [dict(r) async for r in res]

        doc = await q("MATCH (d:Document {id: $doc_id}) RETURN d.title AS title")
        if not doc:
            return {"exists": False}

        elements = await q(
            "MATCH (e:Element {doc_id: $doc_id}) "
            "RETURN labels(e) AS labels, e.docling_label AS docling_label, "
            "       e.self_ref AS self_ref, e.prov_page AS page"
        )
        pages = await q(
            "MATCH (p:Page {doc_id: $doc_id}) RETURN p.page_no AS page_no"
        )

        edges_by_type = await q(
            """
            MATCH (n {doc_id: $doc_id})-[r]->(m)
            WHERE (m:Document OR m:Element OR m:Page OR m:Chunk)
            RETURN type(r) AS type, count(r) AS n
            """
        )
        # HAS_ROOT starts at :Document, so n.doc_id filter above miss the edge
        # (doc has id= not doc_id=); fetch separately.
        has_root = await q(
            "MATCH (d:Document {id: $doc_id})-[:HAS_ROOT]->(c:Element) "
            "RETURN count(c) AS n"
        )

        # Orphan detection: elements with no incoming PARENT_OF and not a root.
        orphans = await q(
            """
            MATCH (e:Element {doc_id: $doc_id})
            WHERE NOT (()-[:PARENT_OF]->(e))
              AND NOT ((:Document {id: $doc_id})-[:HAS_ROOT]->(e))
            RETURN e.self_ref AS self_ref, e.docling_label AS label
            """
        )
        # Elements with prov_page but no ON_PAGE edge.
        on_page_missing = await q(
            """
            MATCH (e:Element {doc_id: $doc_id})
            WHERE e.prov_page IS NOT NULL AND NOT (e)-[:ON_PAGE]->(:Page)
            RETURN count(e) AS n
            """
        )
        # Pages with no element attached.
        empty_pages = await q(
            """
            MATCH (p:Page {doc_id: $doc_id})
            WHERE NOT (:Element {doc_id: $doc_id})-[:ON_PAGE]->(p)
            RETURN p.page_no AS page_no
            """
        )

    specific_label_counter: Counter = Counter()
    docling_label_counter: Counter = Counter()
    for e in elements:
        specifics = [lbl for lbl in e["labels"] if lbl != "Element"]
        specific_label_counter[specifics[0] if specifics else "<none>"] += 1
        docling_label_counter[e["docling_label"] or "<none>"] += 1

    edges = {row["type"]: row["n"] for row in edges_by_type}
    edges["HAS_ROOT"] = has_root[0]["n"] if has_root else 0

    return {
        "exists": True,
        "title": doc[0]["title"],
        "element_count": len(elements),
        "page_count": len(pages),
        "specific_labels": dict(specific_label_counter),
        "docling_labels": dict(docling_label_counter),
        "edges": edges,
        "orphan_elements": orphans,
        "elements_with_prov_but_no_on_page": on_page_missing[0]["n"] if on_page_missing else 0,
        "empty_pages": [r["page_no"] for r in empty_pages],
    }


# ---------------------------------------------------------------------------
# Coherence checks
# ---------------------------------------------------------------------------
async def _coherence(neo, doc_id: str, doc: dict) -> dict:
    source_refs = {it.get("self_ref") for _, it in _iter_items(doc) if it.get("self_ref")}
    async with neo.driver.session(database=neo.database) as s:
        res = await s.run(
            "MATCH (e:Element {doc_id: $doc_id}) RETURN e.self_ref AS r",
            doc_id=doc_id,
        )
        graph_refs = {row["r"] async for row in res}

    return {
        "source_refs_count": len(source_refs),
        "graph_refs_count": len(graph_refs),
        "missing_in_graph": sorted(source_refs - graph_refs)[:20],
        "missing_in_graph_count": len(source_refs - graph_refs),
        "extra_in_graph": sorted(graph_refs - source_refs)[:20],
        "extra_in_graph_count": len(graph_refs - source_refs),
        "reading_order_source_len": len(_dfs_reading_order(doc)),
    }


# ---------------------------------------------------------------------------
# Pretty report
# ---------------------------------------------------------------------------
def _section(title: str, payload: dict) -> str:
    lines = [f"\n── {title} " + "─" * max(2, 70 - len(title))]
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False, default=str)[:220]}")
        else:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def _verdict(source: dict, graph: dict, coherence: dict) -> str:
    issues: list[str] = []

    if not graph.get("exists"):
        return "❌  No graph in Neo4j for this doc."

    if coherence["missing_in_graph_count"]:
        issues.append(
            f"MISSING — {coherence['missing_in_graph_count']} self_ref(s) in "
            "the source DoclingDocument are not in Neo4j"
        )
    if coherence["extra_in_graph_count"]:
        issues.append(
            f"EXTRA — {coherence['extra_in_graph_count']} self_ref(s) in the "
            "graph are not in the source doc"
        )

    # Edge integrity:
    edges = graph.get("edges", {})
    expected_has_root = source["roots_from_body"]
    actual_has_root = edges.get("HAS_ROOT", 0)
    if actual_has_root != expected_has_root:
        issues.append(
            f"HAS_ROOT mismatch — source has {expected_has_root} top-level "
            f"items, graph has {actual_has_root}"
        )

    # Reading order: NEXT chain should be reading_order_length - 1.
    expected_next = max(source["reading_order_length"] - 1, 0)
    actual_next = edges.get("NEXT", 0)
    if actual_next != expected_next:
        issues.append(
            f"NEXT chain mismatch — expected {expected_next}, got {actual_next}"
        )

    # ON_PAGE: every item with prov should have one ON_PAGE edge.
    expected_on_page = source["items_with_prov"]
    actual_on_page = edges.get("ON_PAGE", 0)
    if actual_on_page != expected_on_page:
        issues.append(
            f"ON_PAGE mismatch — {expected_on_page} items have prov, "
            f"{actual_on_page} ON_PAGE edges exist"
        )

    if graph.get("elements_with_prov_but_no_on_page"):
        issues.append(
            f"ON_PAGE broken — {graph['elements_with_prov_but_no_on_page']} "
            "elements have prov_page but no ON_PAGE edge"
        )
    if graph.get("orphan_elements"):
        orphans = graph["orphan_elements"]
        issues.append(f"ORPHANS — {len(orphans)} disconnected Element node(s)")
    if graph.get("empty_pages"):
        issues.append(
            f"EMPTY PAGES — pages with no element attached: {graph['empty_pages']}"
        )

    if not issues:
        return "✅  Graph is well-formed — matches source doc 1:1."
    return "⚠️   Findings:\n  " + "\n  ".join(f"• {x}" for x in issues)


async def main_async() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--doc-id", required=True, help="documents.id (not analysis_jobs.id)")
    args = p.parse_args()

    filename, doc = _load_doc_json(args.doc_id)

    # Imports deferred so we can patch sys.path from within the script runtime.
    sys.path.insert(0, str(REPO / "document-parser"))
    from infra.neo4j import close_driver, get_driver

    neo = await get_driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "changeme"),
    )
    try:
        source = _summarize_source(doc)
        graph = await _summarize_graph(neo, args.doc_id)
        coh = await _coherence(neo, args.doc_id, doc)

        print(f"Document: {filename}")
        print(f"doc_id: {args.doc_id}")
        print(_section("SOURCE (DoclingDocument from SQLite)", source))
        print(_section("GRAPH (Neo4j)", graph))
        print(_section("COHERENCE", coh))
        print()
        print(_verdict(source, graph, coh))
    finally:
        await close_driver()


if __name__ == "__main__":
    asyncio.run(main_async())
