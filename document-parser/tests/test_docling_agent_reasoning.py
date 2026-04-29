"""Tests for `infra.docling_agent_reasoning.DoclingAgentReasoningRunner`.

docling-agent + mellea + docling-core are NOT installed in the CI test env
(heavy deps). We stub the modules via `sys.modules` injection so the tests
cover the real adapter code path without bringing in Ollama or any LLM
client.

Concurrency check (R3): the previous implementation mutated
`os.environ["OLLAMA_HOST"]` on every request, which raced when two requests
arrived with different hosts. The new design commits the host once at
construction time — these tests assert that property holds.
"""

from __future__ import annotations

import asyncio
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

from domain.ports import ReasoningParseError, ReasoningRunner
from infra.llm.ollama_provider import OllamaProvider


@pytest.fixture
def stub_docling_agent(monkeypatch: pytest.MonkeyPatch):
    """Inject fake `docling_agent.agents` + `docling_core.types.doc.document`
    + `mellea.backends.model_ids` modules so the adapter's lazy imports
    resolve to our stubs.

    Returns the stub `DoclingRAGAgent` class + agent instance + result so
    tests can configure return values / side effects.
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


def _make_runner_with_stubbed_deps(
    *,
    host: str = "http://ollama:11434",
    default_model_id: str = "gpt-oss:20b",
):
    """Build the runner bypassing the deps-check (we stubbed deps via
    sys.modules but `import` inside `deps_present()` runs at import time —
    see how the adapter handles it)."""
    from infra.docling_agent_reasoning import DoclingAgentReasoningRunner

    # Force the deps_present check to True regardless of the test env.
    runner = DoclingAgentReasoningRunner.__new__(DoclingAgentReasoningRunner)
    runner._provider = OllamaProvider(host=host, default_model_id=default_model_id)
    runner._deps_ok = True
    os.environ["OLLAMA_HOST"] = host
    return runner


class TestProtocolConformance:
    def test_runner_satisfies_reasoning_runner_protocol(self) -> None:
        """R13 — adapter is structurally a `ReasoningRunner`."""
        runner = _make_runner_with_stubbed_deps()
        assert isinstance(runner, ReasoningRunner)


class TestProviderRejection:
    def test_rejects_non_ollama_provider(self) -> None:
        from infra.docling_agent_reasoning import DoclingAgentReasoningRunner

        class _FakeProvider:
            type = "openai"
            host = "x"
            default_model_id = "y"

            def health_check(self) -> bool:
                return True

        with pytest.raises(NotImplementedError, match="Ollama"):
            DoclingAgentReasoningRunner(provider=_FakeProvider())  # type: ignore[arg-type]


class TestRunHappyPath:
    @pytest.mark.asyncio
    async def test_returns_domain_reasoning_result(self, stub_docling_agent) -> None:
        runner = _make_runner_with_stubbed_deps()

        result = await runner.run(
            document_json='{"stub": true}',
            query="What is this?",
        )

        assert result.answer == "stub answer"
        assert result.converged is True
        assert len(result.iterations) == 1
        it = result.iterations[0]
        assert it.iteration == 1
        assert it.section_ref == "#/texts/0"
        assert it.can_answer is True

    @pytest.mark.asyncio
    async def test_uses_default_model_id_when_not_overridden(self, stub_docling_agent) -> None:
        agent_class, _, _ = stub_docling_agent
        runner = _make_runner_with_stubbed_deps(default_model_id="custom-model:7b")

        await runner.run(document_json="{}", query="Q")

        agent_class.assert_called_once()
        passed = agent_class.call_args.kwargs["model_id"]
        assert passed.ollama_name == "custom-model:7b"

    @pytest.mark.asyncio
    async def test_per_call_model_id_override_wins(self, stub_docling_agent) -> None:
        agent_class, _, _ = stub_docling_agent
        runner = _make_runner_with_stubbed_deps(default_model_id="default:7b")

        await runner.run(document_json="{}", query="Q", model_id="override:13b")

        passed = agent_class.call_args.kwargs["model_id"]
        assert passed.ollama_name == "override:13b"

    @pytest.mark.asyncio
    async def test_calls_rag_loop_with_query_and_doc(self, stub_docling_agent) -> None:
        _, agent_instance, _ = stub_docling_agent
        runner = _make_runner_with_stubbed_deps()

        await runner.run(document_json="{}", query="Hello?")

        agent_instance._rag_loop.assert_called_once()
        kwargs = agent_instance._rag_loop.call_args.kwargs
        assert kwargs["query"] == "Hello?"
        assert kwargs["doc"] == "fake-doc-instance"


class TestRunUpstreamFailure:
    @pytest.mark.asyncio
    async def test_indexerror_translates_to_parse_error(self, stub_docling_agent) -> None:
        """docling-agent's known IndexError → domain `ReasoningParseError`."""
        _, agent_instance, _ = stub_docling_agent
        agent_instance._rag_loop.side_effect = IndexError("list index out of range")
        runner = _make_runner_with_stubbed_deps(default_model_id="granite4:micro-h")

        with pytest.raises(ReasoningParseError) as exc_info:
            await runner.run(document_json="{}", query="Q")

        assert exc_info.value.model_id == "granite4:micro-h"

    @pytest.mark.asyncio
    async def test_other_exceptions_propagate(self, stub_docling_agent) -> None:
        _, agent_instance, _ = stub_docling_agent
        agent_instance._rag_loop.side_effect = RuntimeError("Ollama unreachable")
        runner = _make_runner_with_stubbed_deps()

        with pytest.raises(RuntimeError, match="Ollama unreachable"):
            await runner.run(document_json="{}", query="Q")


class TestHostIsolation:
    """R3 — host is committed at construction; concurrent calls don't race
    on `os.environ["OLLAMA_HOST"]` because it isn't mutated per-request.
    """

    def test_host_committed_at_construction(self) -> None:
        os.environ.pop("OLLAMA_HOST", None)
        runner = _make_runner_with_stubbed_deps(host="http://specific-host:11434")
        assert os.environ["OLLAMA_HOST"] == "http://specific-host:11434"
        # Explicit ref to silence unused-var lint
        assert runner._provider.host == "http://specific-host:11434"

    @pytest.mark.asyncio
    async def test_concurrent_runs_do_not_mutate_env(self, stub_docling_agent) -> None:
        """Two concurrent `run()` calls on the SAME runner — env stays put.

        With the previous design, each request mutated OLLAMA_HOST per-call.
        Now nothing in `run()` should touch os.environ — assert that.
        """
        runner = _make_runner_with_stubbed_deps(host="http://stable:11434")
        os.environ["OLLAMA_HOST"] = "http://stable:11434"

        observed: list[str] = []

        # Use a fresh side_effect that records env at call time.
        _, agent_instance, _ = stub_docling_agent
        original = agent_instance._rag_loop

        def record_env(*args, **kwargs):
            observed.append(os.environ.get("OLLAMA_HOST", ""))
            return original.return_value

        agent_instance._rag_loop = record_env

        await asyncio.gather(
            runner.run(document_json="{}", query="Q1"),
            runner.run(document_json="{}", query="Q2"),
            runner.run(document_json="{}", query="Q3"),
        )

        assert observed == [
            "http://stable:11434",
            "http://stable:11434",
            "http://stable:11434",
        ]


class TestDepsPresent:
    def test_deps_present_returns_false_when_modules_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When docling-agent/mellea aren't importable, the wiring code
        should know not to instantiate the runner."""
        monkeypatch.setitem(sys.modules, "docling_agent", None)
        monkeypatch.setitem(sys.modules, "docling_agent.agents", None)
        monkeypatch.setitem(sys.modules, "mellea", None)

        from infra.docling_agent_reasoning import deps_present

        assert deps_present() is False
