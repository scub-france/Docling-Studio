"""TreeWriter round-trip + structural sanity checks.

Fixture is a hand-crafted DoclingDocument JSON with: one section containing
two paragraphs and a table, spanning two pages. Tests verify that the graph
mirrors the structure (HAS_ROOT, PARENT_OF, ON_PAGE, NEXT) and that
re-writing the same doc is an idempotent replace.
"""

from __future__ import annotations

import json

from infra.neo4j import read_document_json, write_document
from infra.neo4j.schema import bootstrap_schema

FIXTURE = {
    "name": "fixture.pdf",
    "pages": {
        "1": {"page_no": 1, "size": {"width": 595, "height": 842}},
        "2": {"page_no": 2, "size": {"width": 595, "height": 842}},
    },
    "body": {
        "self_ref": "#/body",
        "children": [
            {"$ref": "#/texts/0"},
            {"$ref": "#/texts/1"},
            {"$ref": "#/texts/2"},
            {"$ref": "#/tables/0"},
        ],
    },
    "texts": [
        {
            "self_ref": "#/texts/0",
            "parent": {"$ref": "#/body"},
            "label": "section_header",
            "text": "Introduction",
            "level": 1,
            "prov": [{"page_no": 1, "bbox": {"l": 10, "t": 10, "r": 100, "b": 30}}],
        },
        {
            "self_ref": "#/texts/1",
            "parent": {"$ref": "#/body"},
            "label": "paragraph",
            "text": "First paragraph on page 1.",
            "prov": [{"page_no": 1, "bbox": {"l": 10, "t": 40, "r": 500, "b": 80}}],
        },
        {
            "self_ref": "#/texts/2",
            "parent": {"$ref": "#/body"},
            "label": "paragraph",
            "text": "Continued on page 2.",
            "prov": [{"page_no": 2, "bbox": {"l": 10, "t": 40, "r": 500, "b": 80}}],
        },
    ],
    "tables": [
        {
            "self_ref": "#/tables/0",
            "parent": {"$ref": "#/body"},
            "label": "table",
            "text": "",
            "data": {"num_rows": 2, "num_cols": 2, "grid": [[1, 2], [3, 4]]},
            "prov": [{"page_no": 2, "bbox": {"l": 10, "t": 90, "r": 500, "b": 200}}],
        }
    ],
    "pictures": [],
    "groups": [],
}


async def _count(session, cypher: str, **params) -> int:
    r = await session.run(cypher, **params)
    rec = await r.single()
    return int(rec["n"]) if rec else 0


async def test_write_creates_expected_structure(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    doc_json = json.dumps(FIXTURE)

    result = await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=doc_json,
    )

    assert result.elements_written == 4
    assert result.pages_written == 2
    # Every item in FIXTURE has exactly one prov entry → 4 Provenance nodes.
    assert result.provenances_written == 4

    async with neo4j_driver.driver.session(database=neo4j_driver.database) as s:
        assert (
            await _count(
                s,
                "MATCH (d:Document {id: $id}) RETURN count(d) AS n",
                id="doc-fixture",
            )
            == 1
        )
        assert (
            await _count(
                s,
                "MATCH (:Document {id: $id})-[:HAS_ROOT]->(e:Element) RETURN count(e) AS n",
                id="doc-fixture",
            )
            == 4
        )
        assert (
            await _count(
                s,
                "MATCH (e:Element:SectionHeader {doc_id: $id, self_ref: '#/texts/0'}) "
                "RETURN count(e) AS n",
                id="doc-fixture",
            )
            == 1
        )
        assert (
            await _count(
                s,
                "MATCH (e:Element:Table {doc_id: $id}) RETURN count(e) AS n",
                id="doc-fixture",
            )
            == 1
        )
        # Reading-order chain: 3 NEXT edges for 4 elements.
        assert (
            await _count(
                s,
                "MATCH (a:Element {doc_id: $id})-[:NEXT]->(b:Element {doc_id: $id}) "
                "RETURN count(*) AS n",
                id="doc-fixture",
            )
            == 3
        )
        # Post-v0.6: ON_PAGE attaches Provenance to Page, not Element directly.
        # Traverse through the Provenance node.
        assert (
            await _count(
                s,
                "MATCH (:Element {doc_id: $id})-[:HAS_PROV]->"
                "(:Provenance)-[:ON_PAGE]->(:Page {doc_id: $id}) "
                "RETURN count(*) AS n",
                id="doc-fixture",
            )
            == 4
        )
        # Each element has exactly one Provenance here (single-page fixture).
        assert (
            await _count(
                s,
                "MATCH (e:Element {doc_id: $id})-[:HAS_PROV]->(pv:Provenance) "
                "RETURN count(pv) AS n",
                id="doc-fixture",
            )
            == 4
        )


async def test_rewrite_is_idempotent_replace(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    doc_json = json.dumps(FIXTURE)

    await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=doc_json,
    )
    # Second write with the same id must not duplicate anything.
    await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=doc_json,
    )

    async with neo4j_driver.driver.session(database=neo4j_driver.database) as s:
        assert (
            await _count(s, "MATCH (d:Document {id: $id}) RETURN count(d) AS n", id="doc-fixture")
            == 1
        )
        assert (
            await _count(
                s,
                "MATCH (e:Element {doc_id: $id}) RETURN count(e) AS n",
                id="doc-fixture",
            )
            == 4
        )


async def test_reader_returns_verbatim_json(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    doc_json = json.dumps(FIXTURE, sort_keys=True)
    await write_document(
        neo4j_driver,
        doc_id="doc-fixture",
        filename="fixture.pdf",
        document_json=doc_json,
    )

    read_back = await read_document_json(neo4j_driver, "doc-fixture")
    assert read_back is not None
    assert json.loads(read_back) == json.loads(doc_json)


async def test_reader_missing_doc_returns_none(neo4j_driver):
    await bootstrap_schema(neo4j_driver)
    assert await read_document_json(neo4j_driver, "no-such-doc") is None
