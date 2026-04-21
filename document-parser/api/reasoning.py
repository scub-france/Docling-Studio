"""Reasoning API — live `docling-agent` runner (R&D).

`POST /api/documents/:id/rag` invokes `docling-agent`'s Chunkless RAG loop
against the stored `DoclingDocument` and returns a `RAGResult` in the same
shape the v1 import dialog already consumes — so the frontend overlay code
is fully reused.

Constraints (docling-agent v0.1.0):
- Backend is hard-wired to Ollama (`setup_local_session` in
  `docling_agent/agent_models.py`). Set `OLLAMA_HOST` + `RAG_MODEL_ID` in the
  environment. No OpenAI/WatsonX path without forking upstream.
- We call the private `_rag_loop` because `DoclingRAGAgent.run()` wraps the
  answer in a synthetic `DoclingDocument` and never returns the iteration
  trace. This is brittle — track upstream for a public hook.
- Sync blocking call offloaded to a thread so we don't stall the event loop.
  No streaming at this step (see design doc §7 for v2 SSE plan).
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from infra.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["reasoning"])


class RagRunRequest(BaseModel):
    query: str
    # Optional per-run override; falls back to settings.rag_model_id.
    model_id: str | None = None


class RagIterationResponse(BaseModel):
    iteration: int
    section_ref: str
    reason: str
    section_text_length: int
    can_answer: bool
    response: str


class RagResultResponse(BaseModel):
    answer: str
    iterations: list[RagIterationResponse]
    converged: bool


@router.post("/{doc_id}/rag", response_model=RagResultResponse)
async def run_rag(doc_id: str, body: RagRunRequest, request: Request) -> RagResultResponse:
    if not settings.rag_enabled:
        raise HTTPException(status_code=503, detail="Live reasoning disabled (RAG_ENABLED=false)")

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    analysis_repo = getattr(request.app.state, "analysis_repo", None)
    if analysis_repo is None:
        raise HTTPException(status_code=500, detail="AnalysisRepository not wired")

    latest = await analysis_repo.find_latest_completed_by_document(doc_id)
    if latest is None or not latest.document_json:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis with document_json for {doc_id}",
        )

    # Lazy-import docling-agent so the backend boots even if the dep isn't
    # installed (R&D group). If missing, return 503 with a clear install hint.
    try:
        from docling_agent.agents import DoclingRAGAgent
        from docling_core.types.doc.document import DoclingDocument
        from mellea.backends.model_ids import ModelIdentifier
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"docling-agent not installed: {e}. `pip install docling-agent mellea`.",
        ) from e

    # Ollama client reads OLLAMA_HOST at request time; set it per-call so the
    # configured host takes effect without needing to restart the server.
    os.environ["OLLAMA_HOST"] = settings.ollama_host
    raw_model_id = body.model_id or settings.rag_model_id
    # `DoclingRAGAgent` (pydantic) validates `model_id` strictly against the
    # `ModelIdentifier` dataclass from Mellea. A raw string like "gpt-oss:20b"
    # is rejected even though the Ollama backend itself would accept one.
    # Wrap on the Ollama axis; add other axes here if we ever fork upstream to
    # support non-Ollama backends.
    model_id = ModelIdentifier(ollama_name=raw_model_id)

    try:
        doc = DoclingDocument.model_validate_json(latest.document_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document_json: {e}") from e

    agent = DoclingRAGAgent(model_id=model_id, tools=[])
    logger.info(
        "RAG run: doc_id=%s model_id=%s ollama_host=%s query=%r",
        doc_id,
        model_id,
        settings.ollama_host,
        body.query[:120],
    )

    try:
        # `_rag_loop` is a synchronous LLM-heavy call (N * model latency). Run
        # it in a worker thread so concurrent requests don't block the loop.
        result = await asyncio.to_thread(agent._rag_loop, query=body.query, doc=doc)
    except IndexError as e:
        # Known docling-agent bug: `_attempt_answer` / `_select_section` call
        # `find_json_dicts(answer.value)[0]` without checking for an empty
        # list. When the model can't produce a parseable JSON after 3
        # rejection-sampling retries + 3 `select_from_failure` retries, the
        # list is empty and the `[0]` crashes. It's model-dependent (some
        # questions + some models trip it, others don't).
        #
        # Report as 502 Bad Gateway — the upstream LLM couldn't produce a
        # usable response, not our fault — with a message the UI can show
        # to the user so they pick another model or rephrase.
        logger.warning(
            "docling-agent produced no parseable JSON for doc=%s model=%s query=%r",
            doc_id,
            raw_model_id,
            body.query[:120],
        )
        raise HTTPException(
            status_code=502,
            detail=(
                f"The model '{raw_model_id}' couldn't produce a parseable "
                "answer after retries. Try a different model (e.g. mistral-small3.2) "
                "or rephrase the question."
            ),
        ) from e
    except Exception as e:
        logger.exception("RAG loop failed for doc %s", doc_id)
        raise HTTPException(status_code=500, detail=f"RAG loop failed: {e}") from e

    return RagResultResponse(
        answer=result.answer,
        iterations=[RagIterationResponse(**it.model_dump()) for it in result.iterations],
        converged=result.converged,
    )
