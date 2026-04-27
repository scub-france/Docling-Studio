"""Tests for `api.reasoning` — the live `docling-agent` RAG runner endpoint.

docling-agent + mellea are NOT installed in the CI test env (heavy deps).
The endpoint does a lazy import inside the handler; we stub the modules via
`sys.modules` injection so the tests cover the real code path without
bringing in Ollama, mellea, or LLM clients.
"""

from __future__ import annotations

import sys
import types
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import reasoning as reasoning_module
from api.reasoning import router
from domain.models import AnalysisJob


def _patched_settings(monkeypatch, **overrides):
    """Replace `api.reasoning.settings` with a frozen dataclass copy carrying
    the given overrides. `Settings` is frozen, so attribute-level monkeypatch
    doesn't work — we swap the whole instance on the module.
    """
    new_settings = replace(reasoning_module.settings, **overrides)
    monkeypatch.setattr(reasoning_module, "settings", new_settings)
    return new_settings


def _job_with_doc_json() -> AnalysisJob:
    job = AnalysisJob(document_id="doc-1")
    job.document_filename = "hello.pdf"
    job.mark_running()
    job.mark_completed(
        markdown="# Hello",
        html="<h1>Hello</h1>",
        pages_json="[]",
        # Minimal placeholder — the test stubs `DoclingDocument.model_validate_json`
        # so the content doesn't need to be a real DoclingDocument.
        document_json='{"stub": true}',
        chunks_json="[]",
    )
    return job


@pytest.fixture
def mock_analysis_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_latest_completed_by_document.return_value = _job_with_doc_json()
    return repo


@pytest.fixture
def stub_docling_agent(monkeypatch):
    """Inject fake `docling_agent.agents` + `docling_core.types.doc.document`
    modules so the endpoint's lazy imports resolve to our stubs.

    Returns the `DoclingRAGAgent` stub class so tests can assert on its calls
    / configure its `_rag_loop` return value.
    """
    fake_result = MagicMock()
    fake_result.answer = "stub answer"
    fake_result.converged = True
    fake_result.iterations = [
        MagicMock(
            model_dump=lambda: {
                "iteration": 1,
                "section_ref": "#/texts/0",
                "reason": "looks relevant",
                "section_text_length": 42,
                "can_answer": True,
                "response": "stub answer",
            }
        )
    ]

    agent_instance = MagicMock()
    agent_instance._rag_loop.return_value = fake_result
    agent_class = MagicMock(return_value=agent_instance)

    fake_agents_mod = types.ModuleType("docling_agent.agents")
    fake_agents_mod.DoclingRAGAgent = agent_class
    fake_root_mod = types.ModuleType("docling_agent")
    fake_root_mod.agents = fake_agents_mod

    fake_doc_class = MagicMock()
    fake_doc_class.model_validate_json = MagicMock(return_value="fake-doc-instance")
    fake_doc_mod = types.ModuleType("docling_core.types.doc.document")
    fake_doc_mod.DoclingDocument = fake_doc_class

    # Stub `mellea.backends.model_ids.ModelIdentifier` — the endpoint wraps
    # the string model_id in this dataclass before handing to DoclingRAGAgent.
    # Identity-like: stores the kwargs so tests can assert on `ollama_name`.
    def fake_model_identifier(**kwargs):
        m = MagicMock()
        m.ollama_name = kwargs.get("ollama_name")
        m.openai_name = kwargs.get("openai_name")
        return m

    fake_model_ids_mod = types.ModuleType("mellea.backends.model_ids")
    fake_model_ids_mod.ModelIdentifier = fake_model_identifier
    fake_backends_mod = types.ModuleType("mellea.backends")
    fake_backends_mod.model_ids = fake_model_ids_mod
    fake_mellea_mod = types.ModuleType("mellea")
    fake_mellea_mod.backends = fake_backends_mod

    monkeypatch.setitem(sys.modules, "docling_agent", fake_root_mod)
    monkeypatch.setitem(sys.modules, "docling_agent.agents", fake_agents_mod)
    monkeypatch.setitem(sys.modules, "docling_core.types.doc.document", fake_doc_mod)
    monkeypatch.setitem(sys.modules, "mellea", fake_mellea_mod)
    monkeypatch.setitem(sys.modules, "mellea.backends", fake_backends_mod)
    monkeypatch.setitem(sys.modules, "mellea.backends.model_ids", fake_model_ids_mod)

    return agent_class, agent_instance, fake_result


@pytest.fixture
def client(mock_analysis_repo: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.state.analysis_repo = mock_analysis_repo
    return TestClient(app)


class TestRagDisabled:
    def test_503_when_flag_off(self, client: TestClient, monkeypatch) -> None:
        _patched_settings(monkeypatch, rag_enabled=False)
        resp = client.post("/api/documents/doc-1/rag", json={"query": "Q"})
        assert resp.status_code == 503
        assert "RAG_ENABLED" in resp.json()["detail"]


class TestRagValidation:
    def test_400_when_query_empty(self, client: TestClient, monkeypatch) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        resp = client.post("/api/documents/doc-1/rag", json={"query": "   "})
        assert resp.status_code == 400

    def test_404_when_no_completed_analysis(
        self, client: TestClient, mock_analysis_repo: AsyncMock, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        mock_analysis_repo.find_latest_completed_by_document.return_value = None
        resp = client.post("/api/documents/doc-1/rag", json={"query": "Q"})
        assert resp.status_code == 404


class TestRagSuccess:
    def test_returns_rag_result_shape(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        _agent_class, _agent_instance, _fake_result = stub_docling_agent

        resp = client.post("/api/documents/doc-1/rag", json={"query": "What is this?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "stub answer"
        assert data["converged"] is True
        assert len(data["iterations"]) == 1
        it = data["iterations"][0]
        assert it["iteration"] == 1
        assert it["section_ref"] == "#/texts/0"
        assert it["can_answer"] is True

    def test_calls_rag_loop_with_query_and_doc(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        _agent_class, agent_instance, _ = stub_docling_agent

        client.post("/api/documents/doc-1/rag", json={"query": "Hello?"})

        agent_instance._rag_loop.assert_called_once()
        kwargs = agent_instance._rag_loop.call_args.kwargs
        assert kwargs["query"] == "Hello?"
        # The stub returns the string "fake-doc-instance" from model_validate_json
        # and we pass it straight through to `doc=`.
        assert kwargs["doc"] == "fake-doc-instance"

    def test_uses_default_model_id_when_not_overridden(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True, rag_model_id="custom-model:7b")
        agent_class, _, _ = stub_docling_agent

        client.post("/api/documents/doc-1/rag", json={"query": "Q"})

        agent_class.assert_called_once()
        # model_id is wrapped in a ModelIdentifier(ollama_name=...) dataclass
        # before reaching the agent — the stub exposes the field for assertion.
        passed = agent_class.call_args.kwargs["model_id"]
        assert passed.ollama_name == "custom-model:7b"

    def test_per_request_model_id_override_wins(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True, rag_model_id="default:7b")
        agent_class, _, _ = stub_docling_agent

        client.post("/api/documents/doc-1/rag", json={"query": "Q", "model_id": "override:13b"})

        passed = agent_class.call_args.kwargs["model_id"]
        assert passed.ollama_name == "override:13b"

    def test_sets_ollama_host_env_from_settings(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        import os

        _patched_settings(monkeypatch, rag_enabled=True, ollama_host="http://ollama:11434")

        client.post("/api/documents/doc-1/rag", json={"query": "Q"})
        assert os.environ["OLLAMA_HOST"] == "http://ollama:11434"


class TestRagDepsMissing:
    def test_503_when_docling_agent_not_installed(self, client: TestClient, monkeypatch) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        # Simulate the import failing: remove any stub and ensure the name
        # resolves to a module that raises on attribute access.
        monkeypatch.setitem(sys.modules, "docling_agent.agents", None)

        resp = client.post("/api/documents/doc-1/rag", json={"query": "Q"})
        assert resp.status_code == 503
        assert "docling-agent" in resp.json()["detail"]


class TestRagUpstreamFailure:
    def test_502_when_docling_agent_raises_indexerror(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        """Known docling-agent bug: `find_json_dicts(answer.value)[0]` raises
        `IndexError` when the model fails to produce parseable JSON after
        retries. Our endpoint must surface a 502 with a human-readable
        message, not a 500 stack trace."""
        _patched_settings(monkeypatch, rag_enabled=True, rag_model_id="granite4:micro-h")
        _agent_class, agent_instance, _ = stub_docling_agent
        agent_instance._rag_loop.side_effect = IndexError("list index out of range")

        resp = client.post("/api/documents/doc-1/rag", json={"query": "Quelle tarification ?"})
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert "granite4:micro-h" in detail
        assert "parseable" in detail or "rephrase" in detail

    def test_500_for_other_unexpected_errors(
        self, client: TestClient, stub_docling_agent, monkeypatch
    ) -> None:
        _patched_settings(monkeypatch, rag_enabled=True)
        _agent_class, agent_instance, _ = stub_docling_agent
        agent_instance._rag_loop.side_effect = RuntimeError("Ollama unreachable")

        resp = client.post("/api/documents/doc-1/rag", json={"query": "Q"})
        assert resp.status_code == 500
        assert "Ollama unreachable" in resp.json()["detail"]
