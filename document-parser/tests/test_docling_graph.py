"""Tests for `infra.docling_graph.build_graph_payload`.

The fixture mirrors the DoclingDocument shape used in
`tests/neo4j/test_tree_writer.py` so any structural drift between the two
consumers (TreeWriter -> Neo4j, builder -> SQLite reasoning-graph) surfaces
immediately.
"""

from __future__ import annotations

import json

from infra.docling_graph import build_graph_payload

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
            "data": {"num_rows": 2, "num_cols": 2},
            "prov": [{"page_no": 2, "bbox": {"l": 10, "t": 90, "r": 500, "b": 200}}],
        }
    ],
    "pictures": [],
    "groups": [],
}


def _ids(items, group=None):
    return [i["id"] for i in items if group is None or i.get("group") == group]


def _types(edges):
    return [e["type"] for e in edges]


def test_builds_document_page_and_element_nodes():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture", title="fixture.pdf")
    assert payload.doc_id == "doc-fixture"
    assert payload.page_count == 2
    assert payload.truncated is False

    assert _ids(payload.nodes, group="document") == ["doc::doc-fixture"]
    assert set(_ids(payload.nodes, group="page")) == {"page::1", "page::2"}
    assert set(_ids(payload.nodes, group="element")) == {
        "elem::#/texts/0",
        "elem::#/texts/1",
        "elem::#/texts/2",
        "elem::#/tables/0",
    }


def test_element_keeps_docling_label_and_specific_label():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture")
    by_id = {n["id"]: n for n in payload.nodes}
    section = by_id["elem::#/texts/0"]
    para = by_id["elem::#/texts/1"]
    table = by_id["elem::#/tables/0"]

    # Specific label mirrors TreeWriter's `_LABEL_MAP`.
    assert section["label"] == "SectionHeader"
    assert para["label"] == "Paragraph"
    assert table["label"] == "Table"
    # Docling's original label is preserved (lowercased) for filtering.
    assert section["docling_label"] == "section_header"
    assert para["docling_label"] == "paragraph"


def test_provs_are_carried_on_element_nodes():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture")
    by_id = {n["id"]: n for n in payload.nodes}
    para = by_id["elem::#/texts/1"]
    assert para["prov_page"] == 1
    assert len(para["provs"]) == 1
    assert para["provs"][0]["bbox_l"] == 10.0
    assert para["provs"][0]["page_no"] == 1


def test_has_root_parent_next_and_on_page_edges():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture")
    types = _types(payload.edges)
    # 4 top-level children => 4 HAS_ROOT.
    assert types.count("HAS_ROOT") == 4
    # 4 elements in reading order => 3 NEXT edges.
    assert types.count("NEXT") == 3
    # 4 elements each on 1 page => 4 ON_PAGE edges.
    assert types.count("ON_PAGE") == 4
    # No PARENT_OF in this flat fixture (all parents are #/body).
    assert types.count("PARENT_OF") == 0


def test_on_page_edges_point_to_correct_pages():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture")
    on_page = [(e["source"], e["target"]) for e in payload.edges if e["type"] == "ON_PAGE"]
    assert ("elem::#/texts/0", "page::1") in on_page
    assert ("elem::#/texts/2", "page::2") in on_page
    assert ("elem::#/tables/0", "page::2") in on_page


def test_on_page_dedups_when_element_has_multiple_provs_same_page():
    # Paragraph with two provs on the same page — we expect ONE ON_PAGE edge.
    fixture = {
        **FIXTURE,
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/body"},
                "label": "paragraph",
                "text": "Split across two provs same page",
                "prov": [
                    {"page_no": 1, "bbox": {"l": 0, "t": 0, "r": 10, "b": 10}},
                    {"page_no": 1, "bbox": {"l": 0, "t": 20, "r": 10, "b": 30}},
                ],
            },
        ],
        "tables": [],
        "body": {"self_ref": "#/body", "children": [{"$ref": "#/texts/0"}]},
    }
    payload = build_graph_payload(json.dumps(fixture), doc_id="doc-split")
    on_page = [e for e in payload.edges if e["type"] == "ON_PAGE"]
    assert len(on_page) == 1


def test_parent_of_edges_when_items_are_nested():
    fixture = {
        "pages": {"1": {"page_no": 1, "size": {"width": 595, "height": 842}}},
        "body": {"self_ref": "#/body", "children": [{"$ref": "#/texts/0"}]},
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/body"},
                "label": "section_header",
                "text": "Chapter",
                "level": 1,
                "children": [{"$ref": "#/texts/1"}],
                "prov": [{"page_no": 1, "bbox": {"l": 0, "t": 0, "r": 10, "b": 10}}],
            },
            {
                "self_ref": "#/texts/1",
                "parent": {"$ref": "#/texts/0"},
                "label": "paragraph",
                "text": "Body",
                "prov": [{"page_no": 1, "bbox": {"l": 0, "t": 20, "r": 10, "b": 30}}],
            },
        ],
        "tables": [],
        "pictures": [],
        "groups": [],
    }
    payload = build_graph_payload(json.dumps(fixture), doc_id="doc-nested")
    parents = [(e["source"], e["target"]) for e in payload.edges if e["type"] == "PARENT_OF"]
    assert parents == [("elem::#/texts/0", "elem::#/texts/1")]
    roots = [e for e in payload.edges if e["type"] == "HAS_ROOT"]
    assert len(roots) == 1  # only the section is a direct child of body
    # NEXT follows DFS order: #/texts/0 -> #/texts/1
    nexts = [(e["source"], e["target"]) for e in payload.edges if e["type"] == "NEXT"]
    assert nexts == [("elem::#/texts/0", "elem::#/texts/1")]


def test_truncated_when_page_count_exceeds_cap():
    fixture = {
        **FIXTURE,
        "pages": {str(i): {"page_no": i, "size": {"width": 1, "height": 1}} for i in range(1, 12)},
    }
    payload = build_graph_payload(json.dumps(fixture), doc_id="doc-big", max_pages=10)
    assert payload.truncated is True
    assert payload.page_count == 11
    assert payload.nodes == []
    assert payload.edges == []


def test_title_is_surfaced_on_document_node():
    payload = build_graph_payload(json.dumps(FIXTURE), doc_id="doc-fixture", title="My Doc.pdf")
    doc_node = next(n for n in payload.nodes if n["group"] == "document")
    assert doc_node["title"] == "My Doc.pdf"


def test_element_text_is_capped_at_200_chars():
    long = "x" * 500
    fixture = {
        "pages": {"1": {"page_no": 1, "size": {"width": 1, "height": 1}}},
        "body": {"self_ref": "#/body", "children": [{"$ref": "#/texts/0"}]},
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/body"},
                "label": "paragraph",
                "text": long,
                "prov": [{"page_no": 1}],
            }
        ],
        "tables": [],
        "pictures": [],
        "groups": [],
    }
    payload = build_graph_payload(json.dumps(fixture), doc_id="doc-long")
    para = next(n for n in payload.nodes if n.get("self_ref") == "#/texts/0")
    assert len(para["text"]) == 200
