"""Tests for `api.reasoning` — the HTTP layer over a `ReasoningRunner` port.

The API layer is decoupled from docling-agent / mellea / docling-core. Tests
inject a fake `ReasoningRunner` on `app.state.reasoning_runner` and assert on
HTTP status / payload + on what the runner was called with.

Adapter behaviour (the actual docling-agent integration) is tested separately
in `tests/test_docling_agent_reasoning.py`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.reasoning import router
from domain.models import AnalysisJob
from domain.ports import ReasoningParseError
from domain.value_objects import ReasoningIteration, ReasoningResult


def _job_with_doc_json() -> AnalysisJob:
    job = AnalysisJob(document_id="doc-1")
    job.document_filename = "hello.pdf"
    job.mark_running()
    job.mark_completed(
        markdown="# Hello",
        html="<h1>Hello</h1>",
        pages_json="[]",
        document_json='{"stub": true}',
        chunks_json="[]",
    )
    return job


def _sample_result() -> ReasoningResult:
    return ReasoningResult(
        answer="stub answer",
        converged=True,
        iterations=[
            ReasoningIteration(
                iteration=1,
                section_ref="#/texts/0",
                reason="looks relevant",
                section_text_length=42,
                can_answer=True,
                response="stub answer",
            )
        ],
    )


class _FakeRunner:
    """In-memory ReasoningRunner. Records the last call so tests can assert
    on the args without touching docling-agent."""

    def __init__(
        self,
        *,
        result: ReasoningResult | None = None,
        is_available: bool = True,
        raises: Exception | None = None,
    ) -> None:
        self._result = result or _sample_result()
        self._is_available = is_available
        self._raises = raises
        self.last_call: dict | None = None

    @property
    def is_available(self) -> bool:
        return self._is_available

    async def run(
        self,
        *,
        document_json: str,
        query: str,
        model_id: str | None = None,
    ) -> ReasoningResult:
        self.last_call = {
            "document_json": document_json,
            "query": query,
            "model_id": model_id,
        }
        if self._raises is not None:
            raise self._raises
        return self._result


@pytest.fixture
def mock_analysis_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_latest_completed_by_document.return_value = _job_with_doc_json()
    return repo


def _make_client(*, runner: _FakeRunner | None, repo: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.state.analysis_repo = repo
    app.state.reasoning_runner = runner
    return TestClient(app)


class TestReasoningDisabled:
    def test_503_when_runner_not_wired(self, mock_analysis_repo: AsyncMock) -> None:
        client = _make_client(runner=None, repo=mock_analysis_repo)
        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})
        assert resp.status_code == 503
        assert "REASONING_ENABLED" in resp.json()["detail"]

    def test_503_when_runner_unavailable(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner(is_available=False)
        client = _make_client(runner=runner, repo=mock_analysis_repo)
        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})
        assert resp.status_code == 503


class TestReasoningValidation:
    def test_400_when_query_empty(self, mock_analysis_repo: AsyncMock) -> None:
        client = _make_client(runner=_FakeRunner(), repo=mock_analysis_repo)
        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "   "})
        assert resp.status_code == 400

    def test_404_when_no_completed_analysis(self, mock_analysis_repo: AsyncMock) -> None:
        mock_analysis_repo.find_latest_completed_by_document.return_value = None
        client = _make_client(runner=_FakeRunner(), repo=mock_analysis_repo)
        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})
        assert resp.status_code == 404


class TestReasoningSuccess:
    def test_returns_reasoning_result_shape(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner()
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "What is this?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "stub answer"
        assert data["converged"] is True
        assert len(data["iterations"]) == 1
        it = data["iterations"][0]
        assert it["iteration"] == 1
        assert it["section_ref"] == "#/texts/0"
        assert it["can_answer"] is True
        assert it["section_text_length"] == 42

    def test_passes_query_and_doc_json_to_runner(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner()
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        client.post("/api/documents/doc-1/reasoning", json={"query": "Hello?"})

        assert runner.last_call is not None
        assert runner.last_call["query"] == "Hello?"
        assert runner.last_call["document_json"] == '{"stub": true}'

    def test_no_model_override_passes_none(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner()
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})

        assert runner.last_call is not None
        assert runner.last_call["model_id"] is None

    def test_per_request_model_id_override_wins(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner()
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        client.post(
            "/api/documents/doc-1/reasoning",
            json={"query": "Q", "model_id": "override:13b"},
        )

        assert runner.last_call is not None
        assert runner.last_call["model_id"] == "override:13b"

    def test_iterations_with_multiple_steps_serialize_correctly(
        self, mock_analysis_repo: AsyncMock
    ) -> None:
        """R6 — trace serializable on >=2 iterations, all fields preserved."""
        result = ReasoningResult(
            answer="final",
            converged=False,
            iterations=[
                ReasoningIteration(
                    iteration=1,
                    section_ref="#/texts/0",
                    reason="r1",
                    section_text_length=10,
                    can_answer=False,
                    response="not yet",
                ),
                ReasoningIteration(
                    iteration=2,
                    section_ref="#/texts/5",
                    reason="r2",
                    section_text_length=20,
                    can_answer=True,
                    response="final",
                ),
            ],
        )
        runner = _FakeRunner(result=result)
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["converged"] is False
        assert [it["iteration"] for it in data["iterations"]] == [1, 2]
        assert [it["section_ref"] for it in data["iterations"]] == [
            "#/texts/0",
            "#/texts/5",
        ]
        assert data["iterations"][0]["can_answer"] is False
        assert data["iterations"][1]["can_answer"] is True


class TestReasoningUpstreamFailure:
    def test_502_when_runner_raises_parse_error(self, mock_analysis_repo: AsyncMock) -> None:
        """The model couldn't produce a parseable JSON answer after retries."""
        runner = _FakeRunner(
            raises=ReasoningParseError(model_id="granite4:micro-h", reason="no parseable answer")
        )
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        resp = client.post(
            "/api/documents/doc-1/reasoning",
            json={"query": "Quelle tarification ?"},
        )
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert "granite4:micro-h" in detail
        assert "parseable" in detail or "rephrase" in detail

    def test_500_for_other_unexpected_errors(self, mock_analysis_repo: AsyncMock) -> None:
        runner = _FakeRunner(raises=RuntimeError("Ollama unreachable"))
        client = _make_client(runner=runner, repo=mock_analysis_repo)

        resp = client.post("/api/documents/doc-1/reasoning", json={"query": "Q"})
        assert resp.status_code == 500
        assert "Ollama unreachable" in resp.json()["detail"]
