#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["neo4j>=5.20,<6"]
# ///
"""
Second-pass inspector: how well does our Neo4j graph model the *semantics*
of a DoclingDocument — the parts Peter Staar would care about?

Goes beyond structural 1:1 coverage (inspect_graph.py) to answer:
 - Are SectionHeader levels preserved (outline hierarchy intact)?
 - Can we reconstruct "section scope" (section → its content) from the graph?
 - Are lists vs list-items distinguishable?
 - Are figure captions linked to their figures?
 - What's the depth of the actual hierarchy vs the flat body?
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


async def main_async(doc_id: str) -> None:
    sys.path.insert(0, str(REPO / "document-parser"))
    from infra.neo4j import close_driver, get_driver

    neo = await get_driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "changeme"),
    )
    try:
        async with neo.driver.session(database=neo.database) as s:

            async def q(cypher: str, **params):
                res = await s.run(cypher, doc_id=doc_id, **params)
                return [dict(r) async for r in res]

            print("=== 1. OUTLINE HIERARCHY (section header levels) ===")
            rows = await q(
                """
                MATCH (e:SectionHeader {doc_id: $doc_id})
                RETURN e.self_ref AS ref, e.level AS level, substring(e.text, 0, 60) AS text
                ORDER BY e.self_ref
                """
            )
            for r in rows:
                print(f"  level={r['level']}  {r['ref']:<14}  {r['text']}")
            levels = [r["level"] for r in rows]
            print(f"  → distinct levels: {sorted(set(levels))}")

            print("\n=== 2. DIRECT TREE DEPTH via PARENT_OF ===")
            rows = await q(
                """
                MATCH (root:Element {doc_id: $doc_id})
                WHERE NOT (()-[:PARENT_OF]->(root))
                OPTIONAL MATCH path = (root)-[:PARENT_OF*]->(leaf)
                WITH root, max(length(path)) AS depth
                RETURN
                  labels(root) AS labels,
                  root.docling_label AS docling_label,
                  coalesce(depth, 0) AS depth
                ORDER BY depth DESC
                LIMIT 10
                """
            )
            for r in rows:
                specific = [l for l in r["labels"] if l != "Element"][0]
                print(f"  depth={r['depth']}  {specific:<15}  ({r['docling_label']})")

            print("\n=== 3. SECTION SCOPE (can we infer section content from NEXT?) ===")
            # For each section header, walk NEXT until the next section header —
            # that's the section's content span as per docling-agent's logic.
            rows = await q(
                """
                MATCH (sh:SectionHeader {doc_id: $doc_id})
                OPTIONAL MATCH p = (sh)-[:NEXT*]->(next:SectionHeader {doc_id: $doc_id})
                WITH sh, min(length(p)) AS span
                RETURN
                  sh.self_ref AS ref,
                  sh.level AS level,
                  coalesce(span - 1, -1) AS items_in_scope_if_span_works,
                  substring(sh.text, 0, 50) AS title
                ORDER BY sh.self_ref
                """
            )
            for r in rows:
                span = r["items_in_scope_if_span_works"]
                label = f"~{span} items" if span >= 0 else "last (unknown span)"
                print(f"  level={r['level']}  {r['ref']:<14}  {label:<18}  {r['title']}")

            print("\n=== 4. LIST CONTAINER vs LIST ITEM distinction ===")
            rows = await q(
                """
                MATCH (e:ListItem {doc_id: $doc_id})
                RETURN e.docling_label AS docling_label, count(*) AS n
                ORDER BY docling_label
                """
            )
            for r in rows:
                print(f"  docling_label={r['docling_label']:<12}  neo4j_label=:ListItem  count={r['n']}")
            print("  ⚠️  Both 'list' (container) and 'list_item' get :ListItem in Neo4j.")

            print("\n=== 5. FIGURE ↔ CAPTION linkage ===")
            captions = await q(
                "MATCH (c:Caption {doc_id: $doc_id}) RETURN count(c) AS n"
            )
            linked = await q(
                """
                MATCH (fig:Figure {doc_id: $doc_id})-[:PARENT_OF]-(c:Caption {doc_id: $doc_id})
                RETURN count(DISTINCT fig) AS figs_with_caption, count(DISTINCT c) AS captions_linked
                """
            )
            print(
                f"  captions={captions[0]['n']}  "
                f"figures_with_caption={linked[0]['figs_with_caption']}  "
                f"captions_linked={linked[0]['captions_linked']}"
            )

            print("\n=== 6. TABLE CELL CONTENT — graph-addressable or opaque? ===")
            rows = await q(
                """
                MATCH (t:Table {doc_id: $doc_id})
                RETURN t.self_ref AS ref,
                       CASE WHEN t.cells_json IS NOT NULL THEN 'JSON-blob' ELSE 'missing' END
                        AS cells_mode,
                       size(coalesce(t.cells_json, '')) AS cells_bytes
                """
            )
            for r in rows:
                print(f"  {r['ref']:<14}  cells={r['cells_mode']}  ({r['cells_bytes']} bytes)")
            if rows:
                print("  ⚠️  Cells are a JSON string on the Table node — not queryable as graph nodes.")

            print("\n=== 7. WHAT AN AGENT VISIT LOOKS LIKE (section subgraph) ===")
            # Pick the first section header and show what would be highlighted
            # if we traversed its scope (via NEXT until next same-or-higher-level section).
            rows = await q(
                """
                MATCH (sh:SectionHeader {doc_id: $doc_id})
                WITH sh ORDER BY sh.self_ref LIMIT 1
                OPTIONAL MATCH chain = (sh)-[:NEXT*0..50]->(e:Element {doc_id: $doc_id})
                WITH sh, e, length(chain) AS pos
                OPTIONAL MATCH (e)<-[:NEXT*0..]-(_stop:SectionHeader)
                WHERE _stop <> sh AND _stop.level <= sh.level
                WITH sh, e, pos
                ORDER BY pos
                LIMIT 8
                RETURN pos, labels(e) AS labels, e.docling_label AS kind,
                       substring(e.text, 0, 60) AS text
                """
            )
            for r in rows:
                specific = [l for l in r["labels"] if l != "Element"][0]
                print(f"  pos={r['pos']:<3}  {specific:<15}  {r['text']}")
            print(
                "  → Visiting a section on the graph shows ONE node. Its 'scope' "
                "(the content) must be inferred via NEXT-walk — not materialized as edges."
            )

    finally:
        await close_driver()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doc-id", required=True)
    args = p.parse_args()
    asyncio.run(main_async(args.doc_id))
