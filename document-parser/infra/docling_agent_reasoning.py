"""docling-agent reasoning runner adapter.

Implements `ReasoningRunner` for an `OllamaProvider`-backed `LLMProvider`.
Encapsulates everything that talks to docling-agent / mellea so neither the
domain nor the API layer depends on those packages.

Why we still call the private `_rag_loop`: `DoclingRAGAgent.run()` wraps the
answer in a synthetic `DoclingDocument` and discards the iteration trace.
Tracked upstream at https://github.com/docling-project/docling-agent/issues/26
— switch to the public surface once the issue lands.
"""

from __future__ import annotations

import asyncio
import logging
import os

from domain.ports import LLMProvider, ReasoningParseError
from domain.value_objects import (
    LLMProviderType,
    ReasoningIteration,
    ReasoningResult,
)

logger = logging.getLogger(__name__)


def deps_present() -> bool:
    """Import-check for the heavy reasoning deps. Used by the DI wire-up to
    decide whether to instantiate the runner at all (so the backend boots
    cleanly when docling-agent + mellea aren't installed)."""
    try:
        import docling_agent.agents  # noqa: F401
        import mellea  # noqa: F401
    except ImportError:
        return False
    return True


class DoclingAgentReasoningRunner:
    """ReasoningRunner adapter wrapping docling-agent + mellea.

    The provider's host is committed to the process-wide `OLLAMA_HOST` env
    var at construction time — Ollama's Python client reads it on session
    creation. Setting it once at boot (instead of per-request) eliminates the
    cross-request race the previous implementation exposed.
    """

    def __init__(self, provider: LLMProvider) -> None:
        if provider.type is not LLMProviderType.OLLAMA:
            raise NotImplementedError(
                f"docling-agent v0.1.0 only supports Ollama, got provider type "
                f"{provider.type!r}. See "
                f"https://github.com/docling-project/docling-agent/issues/26"
            )
        self._provider = provider
        self._deps_ok = deps_present()
        # Commit the host at boot — concurrent `run()` calls then share the
        # same value with no racy mutation.
        os.environ["OLLAMA_HOST"] = provider.host

    @property
    def is_available(self) -> bool:
        return self._deps_ok

    async def run(
        self,
        *,
        document_json: str,
        query: str,
        model_id: str | None = None,
    ) -> ReasoningResult:
        if not self._deps_ok:
            raise RuntimeError("docling-agent / mellea not importable — cannot run reasoning")

        # Lazy imports keep the module loadable when deps are missing (the
        # runner is only ever instantiated when `deps_present()` is True, but
        # this also makes the import surface explicit).
        from docling_agent.agents import DoclingRAGAgent
        from docling_core.types.doc.document import DoclingDocument
        from mellea.backends.model_ids import ModelIdentifier

        raw_model_id = model_id or self._provider.default_model_id
        # `DoclingRAGAgent` (pydantic) validates `model_id` strictly against
        # `ModelIdentifier` from mellea. Wrapping on the Ollama axis is the
        # only realizable path today (cf. LLMProvider docstring).
        wrapped_model_id = ModelIdentifier(ollama_name=raw_model_id)

        try:
            doc = DoclingDocument.model_validate_json(document_json)
        except Exception as e:
            raise RuntimeError(f"Failed to parse document_json: {e}") from e

        agent = DoclingRAGAgent(model_id=wrapped_model_id, tools=[])
        logger.info(
            "Reasoning run: model_id=%s ollama_host=%s query=%r",
            raw_model_id,
            self._provider.host,
            query[:120],
        )

        try:
            # `_rag_loop` is sync + LLM-heavy (N * model latency). Offload to
            # a worker thread so concurrent calls don't block the event loop.
            # Private API kept until docling-agent#26 lands.
            raw_result = await asyncio.to_thread(agent._rag_loop, query=query, doc=doc)
        except IndexError as e:
            # docling-agent v0.1.0 bug: `_attempt_answer` / `_select_section`
            # call `find_json_dicts(answer.value)[0]` without handling an
            # empty list. When the model can't produce a parseable JSON after
            # 3 rejection-sampling retries + 3 `select_from_failure` retries,
            # the list is empty and `[0]` raises IndexError. Translate to a
            # domain-level error the API can map to 502.
            logger.warning(
                "docling-agent produced no parseable JSON for model=%s query=%r",
                raw_model_id,
                query[:120],
            )
            raise ReasoningParseError(
                model_id=raw_model_id,
                reason="no parseable answer after retries",
            ) from e

        return ReasoningResult(
            answer=raw_result.answer,
            iterations=[ReasoningIteration(**it.model_dump()) for it in raw_result.iterations],
            converged=raw_result.converged,
        )
