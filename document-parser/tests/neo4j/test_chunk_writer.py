"""ChunkWriter creates Chunk nodes + DERIVED_FROM links.

Builds on the tree_writer fixture — writes the tree first so that DERIVED_FROM
has Elements to link against.
"""

from __future__ import annotations

import json

from infra.neo4j import fetch_graph, write_chunks, write_document
from infra.neo4j.schema import bootstrap_schema
from tests.neo4j.test_tree_writer import FIXTURE

CHUNKS = [
    {
        "text": "Introduction. First paragraph on page 1.",
        "sourcePage": 1,
        "tokenCount": 8,
        "docItems": [
            {"selfRef": "#/texts/0", "label": "section_header"},
            {"selfRef": "#/texts/1", "label": "paragraph"},
        ],
    },
    {
        "text": "Continued on page 2.",
        "sourcePage": 2,
        "tokenCount": 4,
        "docItems": [{"selfRef": "#/texts/2", "label": "paragraph"}],
        "deleted": False,
    },
    # soft-deleted chunk: must be ignored
    {"text": "gone", "deleted": True, "docItems": []},
]


async def test_write_chunks_and_derived_from(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=json.dumps(FIXTURE),
    )

    result = await write_chunks(
        neo4j_driver,
        doc_id="doc-fixture",
        chunks_json=json.dumps(CHUNKS),
    )

    assert result.chunks_written == 2
    assert result.derived_from_edges == 3

    async with neo4j_driver.driver.session(database=neo4j_driver.database) as s:
        count = await (
            await s.run(
                "MATCH (:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) AS n",
                id="doc-fixture",
            )
        ).single()
        assert count["n"] == 2

        # First chunk derives from 2 elements, second from 1.
        for idx, expected in [(0, 2), (1, 1)]:
            cnt = await (
                await s.run(
                    "MATCH (c:Chunk {id: $cid})-[:DERIVED_FROM]->(e:Element) RETURN count(e) AS n",
                    cid=f"doc-fixture::chunk::{idx}",
                )
            ).single()
            assert cnt["n"] == expected

        stages = await (
            await s.run(
                "MATCH (d:Document {id: $id}) RETURN d.stages_applied AS s", id="doc-fixture"
            )
        ).single()
        assert "chunks" in stages["s"]


async def test_fetch_graph_returns_full_payload(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=json.dumps(FIXTURE),
    )
    await write_chunks(
        neo4j_driver,
        doc_id="doc-fixture",
        chunks_json=json.dumps(CHUNKS),
    )

    payload = await fetch_graph(neo4j_driver, "doc-fixture")
    assert payload is not None
    assert payload.truncated is False
    assert payload.page_count == 2

    groups = {n["group"] for n in payload.nodes}
    assert groups == {"document", "element", "page", "chunk"}

    edge_types = {e["type"] for e in payload.edges}
    # Every edge kind written by TreeWriter and ChunkWriter should be present.
    assert {"HAS_ROOT", "PARENT_OF", "NEXT", "ON_PAGE", "HAS_CHUNK", "DERIVED_FROM"} <= edge_types


async def test_fetch_graph_missing_doc_returns_none(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    assert await fetch_graph(neo4j_driver, "no-such-doc") is None
