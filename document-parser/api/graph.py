"""Graph API — returns a cytoscape-shaped view of the document structure.

Two endpoints:
- `/graph` — read from Neo4j. Rich graph (elements + chunks + pages + merges).
  Requires the Maintain step (IngestionPipeline) to have run for the document.
- `/reasoning-graph` — built on-the-fly from the SQLite `document_json` blob.
  No Neo4j dependency. Lighter graph (no chunks) but enough to render the
  reasoning-trace overlay on top of `GraphView`.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from infra.docling_graph import build_graph_payload
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


@router.get("/{doc_id}/reasoning-graph", response_model=GraphResponse)
async def get_reasoning_graph(doc_id: str, request: Request) -> GraphResponse:
    """Graph projection built from SQLite `document_json` — no Neo4j needed.

    Serves the reasoning-trace viewer, which only needs the element/page/edge
    structure to overlay iterations onto.
    """
    analysis_repo = getattr(request.app.state, "analysis_repo", None)
    if analysis_repo is None:
        raise HTTPException(status_code=500, detail="AnalysisRepository not wired")

    latest = await analysis_repo.find_latest_completed_by_document(doc_id)
    if latest is None or not latest.document_json:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis with document_json for {doc_id}",
        )

    payload = build_graph_payload(
        latest.document_json,
        doc_id=doc_id,
        title=latest.document_filename or doc_id,
        max_pages=MAX_PAGES,
    )
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
