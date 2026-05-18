"""Unit tests for the Neo4jWriteError safety net in `chunk_writer`.

The integration tests in `tests/neo4j/test_chunk_writer.py` need a live
Neo4j to run. The count-mismatch assertion added in #225 is **defensive
code** that a real Neo4j server never triggers — so we can't exercise
it from an integration test. These mock-based tests verify the
assertion still fires on a forged result, so a future refactor can't
silently disable the safety net.

See `infra/neo4j/__init__.py` (Why-no-OGM docstring) for the broader
rationale on why this assertion exists at all.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from infra.neo4j.chunk_writer import Neo4jWriteError, write_chunks


class _FakeResult:
    """Stand-in for an async neo4j result.

    `single()` returns whatever we rigged at construction. Used by the
    CREATE query to forge a count mismatch.
    """

    def __init__(self, single_value: dict | None = None) -> None:
        self._single = single_value

    async def single(self) -> dict | None:
        return self._single


class _FakeTx:
    """Stand-in for an async neo4j transaction.

    Records every `run()` call so the test can assert which statements
    ran. The CREATE query returns a rigged `_FakeResult`; everything
    else returns an empty result.
    """

    def __init__(self, *, create_returns: dict | None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._create_returns = create_returns
        self.committed = False

    async def __aenter__(self) -> _FakeTx:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def run(self, query: str, **params: Any) -> _FakeResult:
        self.calls.append((query.strip(), params))
        if "CREATE (c:Chunk" in query:
            return _FakeResult(single_value=self._create_returns)
        return _FakeResult(single_value=None)

    async def commit(self) -> None:
        self.committed = True


class _FakeSession:
    def __init__(self, tx: _FakeTx) -> None:
        self._tx = tx

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def begin_transaction(self) -> _FakeTx:
        return self._tx


class _FakeDriver:
    """Mimics `neo4j.AsyncDriver.session(database=...)`."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    def session(self, database: str | None = None) -> _FakeSession:
        return self._session


class _FakeNeo:
    """Mimics `infra.neo4j.driver.Neo4jDriver` — just enough surface."""

    def __init__(self, *, create_returns: dict | None) -> None:
        self._tx = _FakeTx(create_returns=create_returns)
        self.driver = _FakeDriver(_FakeSession(self._tx))
        self.database = "neo4j"


def _chunks_payload(n: int) -> str:
    return json.dumps([{"text": f"chunk {i}", "tokenCount": 1} for i in range(n)])


async def test_neo4j_write_error_fires_on_count_mismatch() -> None:
    """If the server reports fewer created chunks than expected, the
    writer must raise `Neo4jWriteError` rather than committing a
    silent partial write.
    """
    neo = _FakeNeo(create_returns={"created": 1})  # forge a mismatch: 1 != 3
    with pytest.raises(Neo4jWriteError) as excinfo:
        await write_chunks(neo, doc_id="doc-x", chunks_json=_chunks_payload(3))
    msg = str(excinfo.value)
    assert "doc-x" in msg
    assert "3" in msg
    assert "1" in msg
    # The error must point at the most likely cause — the message is
    # what an on-call sees in logs and should not regress.
    assert "Document node" in msg
    # The transaction must never be committed on a mismatch.
    assert neo._tx.committed is False


async def test_neo4j_write_error_fires_when_single_returns_none() -> None:
    """A `None` single result (server returned no rows) is treated as
    `created = 0` — also a mismatch when chunks were expected.
    """
    neo = _FakeNeo(create_returns=None)
    with pytest.raises(Neo4jWriteError):
        await write_chunks(neo, doc_id="doc-y", chunks_json=_chunks_payload(2))
    assert neo._tx.committed is False


async def test_write_chunks_commits_when_count_matches() -> None:
    """Happy path with mocks — server reports the expected count, no
    exception, transaction commits.
    """
    neo = _FakeNeo(create_returns={"created": 4})
    result = await write_chunks(neo, doc_id="doc-z", chunks_json=_chunks_payload(4))
    assert result.chunks_written == 4
    assert neo._tx.committed is True


async def test_write_chunks_skips_create_when_empty() -> None:
    """No chunks → no CREATE → no assertion to check. The Document
    MERGE + the stages SET must still run, and commit happens.
    """
    neo = _FakeNeo(create_returns=None)
    result = await write_chunks(neo, doc_id="doc-empty", chunks_json="[]")
    assert result.chunks_written == 0
    queries = [q for q, _ in neo._tx.calls]
    assert any("MERGE (d:Document" in q for q in queries)
    assert not any("CREATE (c:Chunk" in q for q in queries)
    assert neo._tx.committed is True
