"""Tests for the ingestion API endpoints (api.ingestion)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.ingestion import router
from domain.models import AnalysisJob
from services.ingestion_service import IngestionResult


@pytest.fixture
def mock_ingestion_service() -> AsyncMock:
    svc = AsyncMock()
    svc.ingest.return_value = IngestionResult(
        doc_id="doc-1", chunks_indexed=5, embedding_dimension=384
    )
    svc.delete_document.return_value = 3
    return svc


@pytest.fixture
def mock_analysis_service() -> AsyncMock:
    svc = AsyncMock()
    job = AnalysisJob(document_id="doc-1")
    job.document_filename = "test.pdf"
    job.mark_running()
    job.mark_completed(
        markdown="# Test",
        html="<h1>Test</h1>",
        pages_json="[]",
        document_json='{"doc": true}',
        chunks_json='[{"text": "hello"}]',
    )
    svc.find_by_id.return_value = job
    return svc


@pytest.fixture
def client(mock_ingestion_service: AsyncMock, mock_analysis_service: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.state.ingestion_service = mock_ingestion_service
    app.state.analysis_service = mock_analysis_service
    return TestClient(app)


class TestIngestAnalysis:
    def test_ingest_success(self, client: TestClient) -> None:
        resp = client.post("/api/ingestion/job-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["docId"] == "doc-1"
        assert data["chunksIndexed"] == 5
        assert data["embeddingDimension"] == 384

    def test_ingest_not_found(self, client: TestClient, mock_analysis_service: AsyncMock) -> None:
        mock_analysis_service.find_by_id.return_value = None
        resp = client.post("/api/ingestion/missing")
        assert resp.status_code == 404

    def test_ingest_not_completed(
        self, client: TestClient, mock_analysis_service: AsyncMock
    ) -> None:
        job = AnalysisJob(document_id="doc-1")
        mock_analysis_service.find_by_id.return_value = job
        resp = client.post("/api/ingestion/job-1")
        assert resp.status_code == 400

    def test_ingest_no_chunks(self, client: TestClient, mock_analysis_service: AsyncMock) -> None:
        job = AnalysisJob(document_id="doc-1")
        job.mark_running()
        job.mark_completed(markdown="x", html="x", pages_json="[]")
        mock_analysis_service.find_by_id.return_value = job
        resp = client.post("/api/ingestion/job-1")
        assert resp.status_code == 400


class TestDeleteIngested:
    def test_delete_success(self, client: TestClient) -> None:
        resp = client.delete("/api/ingestion/doc-1")
        assert resp.status_code == 204


class TestIngestionStatus:
    def test_available(self, client: TestClient) -> None:
        resp = client.get("/api/ingestion/status")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    def test_not_available(self) -> None:
        app = FastAPI()
        app.include_router(router)
        app.state.ingestion_service = None
        app.state.analysis_service = AsyncMock()
        tc = TestClient(app)
        resp = tc.get("/api/ingestion/status")
        assert resp.status_code == 200
        assert resp.json()["available"] is False


class TestIngestionDisabled:
    def test_returns_503_when_disabled(self) -> None:
        app = FastAPI()
        app.include_router(router)
        app.state.ingestion_service = None
        app.state.analysis_service = AsyncMock()
        tc = TestClient(app)
        resp = tc.post("/api/ingestion/job-1")
        assert resp.status_code == 503
