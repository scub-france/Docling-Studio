"""Tests for the ingestion REST API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from services.ingestion_service import IngestionError, IngestionResult


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear_ingestion_service():
    """Ensure ingestion_service is reset after each test."""
    original = getattr(app.state, "ingestion_service", None)
    yield
    app.state.ingestion_service = original


# ---------------------------------------------------------------------------
# GET /api/ingestion/status
# ---------------------------------------------------------------------------


def test_status_available(client):
    app.state.ingestion_service = MagicMock()
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200
    assert resp.json()["available"] is True


def test_status_unavailable(client):
    app.state.ingestion_service = None
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200
    assert resp.json()["available"] is False


# ---------------------------------------------------------------------------
# POST /api/ingestion/{job_id}
# ---------------------------------------------------------------------------


def test_ingest_success(client):
    svc = MagicMock()
    svc.ingest = AsyncMock(
        return_value=IngestionResult(doc_id="doc-1", chunks_indexed=5, embedding_dimension=384)
    )
    app.state.ingestion_service = svc
    resp = client.post("/api/ingestion/job-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["doc_id"] == "doc-1"
    assert data["chunks_indexed"] == 5
    assert data["embedding_dimension"] == 384


def test_ingest_no_service(client):
    app.state.ingestion_service = None
    resp = client.post("/api/ingestion/job-1")
    assert resp.status_code == 503


def test_ingest_ingestion_error(client):
    svc = MagicMock()
    svc.ingest = AsyncMock(side_effect=IngestionError("job not found"))
    app.state.ingestion_service = svc
    resp = client.post("/api/ingestion/job-1")
    assert resp.status_code == 422
    assert "job not found" in resp.json()["detail"]


def test_ingest_unexpected_error(client):
    svc = MagicMock()
    svc.ingest = AsyncMock(side_effect=RuntimeError("boom"))
    app.state.ingestion_service = svc
    resp = client.post("/api/ingestion/job-1")
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/ingestion/{doc_id}
# ---------------------------------------------------------------------------


def test_delete_success(client):
    svc = MagicMock()
    svc.delete = AsyncMock(return_value=3)
    app.state.ingestion_service = svc
    resp = client.delete("/api/ingestion/doc-1")
    assert resp.status_code == 204


def test_delete_no_service(client):
    app.state.ingestion_service = None
    resp = client.delete("/api/ingestion/doc-1")
    assert resp.status_code == 503


def test_delete_ingestion_error(client):
    svc = MagicMock()
    svc.delete = AsyncMock(side_effect=IngestionError("opensearch error"))
    app.state.ingestion_service = svc
    resp = client.delete("/api/ingestion/doc-1")
    assert resp.status_code == 422
