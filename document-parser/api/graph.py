"""Graph API — returns a cytoscape-shaped view of the Neo4j graph for a doc.

v0.5 contract:
- Returns the **full** graph for the document (see design §8.4)
- Hard cap at 200 pages; beyond that, HTTP 413 with `truncated: true`
- No pagination (ships in v0.6)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from infra.neo4j import fetch_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["graph"])

MAX_PAGES = 200


class GraphNode(BaseModel):
    id: str
    group: str
    label: str | None = None

    model_config = {"extra": "allow"}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    order: int | None = None


class GraphResponse(BaseModel):
    doc_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_count: int
    edge_count: int
    truncated: bool
    page_count: int


@router.get("/{doc_id}/graph", response_model=GraphResponse)
async def get_document_graph(doc_id: str, request: Request) -> GraphResponse:
    neo = getattr(request.app.state, "neo4j", None)
    if neo is None:
        raise HTTPException(status_code=503, detail="Neo4j is not configured")

    payload = await fetch_graph(neo, doc_id, max_pages=MAX_PAGES)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"No graph for document {doc_id}")
    if payload.truncated:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Graph too large: document has {payload.page_count} pages "
                f"(cap {MAX_PAGES}). Pagination ships in v0.6."
            ),
        )

    return GraphResponse(
        doc_id=payload.doc_id,
        nodes=[GraphNode(**n) for n in payload.nodes],
        edges=[GraphEdge(**e) for e in payload.edges],
        node_count=payload.node_count,
        edge_count=payload.edge_count,
        truncated=payload.truncated,
        page_count=payload.page_count,
    )
