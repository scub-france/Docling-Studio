"""Tests for FastAPI API endpoints using TestClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from domain.models import AnalysisJob, Document
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_analysis_service(client):
    """Inject a mock AnalysisService into app.state for the duration of the test."""
    mock_svc = MagicMock()
    original = getattr(app.state, "analysis_service", None)
    app.state.analysis_service = mock_svc
    yield mock_svc
    app.state.analysis_service = original


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "engine" in data


class TestDocumentEndpoints:
    @patch("services.document_service.find_all", new_callable=AsyncMock)
    def test_list_documents(self, mock_find_all, client):
        mock_find_all.return_value = [
            Document(id="d1", filename="a.pdf", storage_path="/tmp/a"),
            Document(id="d2", filename="b.pdf", storage_path="/tmp/b"),
        ]

        resp = client.get("/api/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == "d1"
        assert data[0]["filename"] == "a.pdf"
        # Verify camelCase
        assert "createdAt" in data[0]

    @patch("services.document_service.find_by_id", new_callable=AsyncMock)
    def test_get_document(self, mock_find, client):
        mock_find.return_value = Document(
            id="d1", filename="test.pdf", content_type="application/pdf",
            file_size=2048, page_count=3, storage_path="/tmp/test",
        )

        resp = client.get("/api/documents/d1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "d1"
        assert data["fileSize"] == 2048
        assert data["pageCount"] == 3

    @patch("services.document_service.find_by_id", new_callable=AsyncMock)
    def test_get_document_not_found(self, mock_find, client):
        mock_find.return_value = None

        resp = client.get("/api/documents/missing")
        assert resp.status_code == 404

    @patch("services.document_service.upload", new_callable=AsyncMock)
    def test_upload_document(self, mock_upload, client):
        mock_upload.return_value = Document(
            id="new-1", filename="uploaded.pdf",
            content_type="application/pdf", file_size=512,
            storage_path="/tmp/uploaded",
        )

        resp = client.post(
            "/api/documents/upload",
            files={"file": ("uploaded.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "new-1"
        assert data["filename"] == "uploaded.pdf"

    @patch("services.document_service.upload", new_callable=AsyncMock)
    def test_upload_too_large(self, mock_upload, client):
        mock_upload.side_effect = ValueError("File too large (max 50 MB)")

        resp = client.post(
            "/api/documents/upload",
            files={"file": ("big.pdf", b"x", "application/pdf")},
        )
        assert resp.status_code == 413

    @patch("services.document_service.delete", new_callable=AsyncMock)
    def test_delete_document(self, mock_delete, client):
        mock_delete.return_value = True

        resp = client.delete("/api/documents/d1")
        assert resp.status_code == 204

    @patch("services.document_service.delete", new_callable=AsyncMock)
    def test_delete_document_not_found(self, mock_delete, client):
        mock_delete.return_value = False

        resp = client.delete("/api/documents/missing")
        assert resp.status_code == 404


class TestAnalysisEndpoints:
    def test_list_analyses(self, client, mock_analysis_service):
        mock_analysis_service.find_all = AsyncMock(return_value=[
            AnalysisJob(id="j1", document_id="d1", document_filename="test.pdf"),
        ])

        resp = client.get("/api/analyses")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "j1"
        assert data[0]["documentId"] == "d1"
        assert data[0]["documentFilename"] == "test.pdf"
        assert data[0]["status"] == "PENDING"

    def test_get_analysis(self, client, mock_analysis_service):
        job = AnalysisJob(id="j1", document_id="d1", document_filename="test.pdf")
        job.mark_running()
        mock_analysis_service.find_by_id = AsyncMock(return_value=job)

        resp = client.get("/api/analyses/j1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "RUNNING"
        assert data["startedAt"] is not None

    def test_get_analysis_not_found(self, client, mock_analysis_service):
        mock_analysis_service.find_by_id = AsyncMock(return_value=None)

        resp = client.get("/api/analyses/missing")
        assert resp.status_code == 404

    def test_create_analysis(self, client, mock_analysis_service):
        mock_analysis_service.create = AsyncMock(return_value=AnalysisJob(
            id="j1", document_id="d1", document_filename="test.pdf",
        ))

        resp = client.post("/api/analyses", json={"documentId": "d1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "j1"
        assert data["documentId"] == "d1"
        mock_analysis_service.create.assert_called_once_with("d1", pipeline_options=None)

    def test_create_analysis_with_pipeline_options(self, client, mock_analysis_service):
        mock_analysis_service.create = AsyncMock(return_value=AnalysisJob(
            id="j2", document_id="d1", document_filename="test.pdf",
        ))

        resp = client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {
                "do_ocr": False,
                "do_table_structure": True,
                "table_mode": "fast",
                "do_code_enrichment": True,
                "do_formula_enrichment": False,
                "do_picture_classification": False,
                "do_picture_description": False,
                "generate_picture_images": True,
                "generate_page_images": False,
                "images_scale": 2.0,
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "j2"

        call_kwargs = mock_analysis_service.create.call_args
        opts = call_kwargs.kwargs["pipeline_options"]
        assert opts["do_ocr"] is False
        assert opts["table_mode"] == "fast"
        assert opts["do_code_enrichment"] is True
        assert opts["generate_picture_images"] is True
        assert opts["images_scale"] == 2.0

    def test_create_analysis_with_partial_pipeline_options(self, client, mock_analysis_service):
        """Pipeline options should use defaults for unspecified fields."""
        mock_analysis_service.create = AsyncMock(return_value=AnalysisJob(
            id="j3", document_id="d1", document_filename="test.pdf",
        ))

        resp = client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {"do_ocr": False}
        })
        assert resp.status_code == 200

        opts = mock_analysis_service.create.call_args.kwargs["pipeline_options"]
        assert opts["do_ocr"] is False
        # Defaults
        assert opts["do_table_structure"] is True
        assert opts["table_mode"] == "accurate"
        assert opts["do_code_enrichment"] is False

    def test_create_analysis_document_not_found(self, client, mock_analysis_service):
        mock_analysis_service.create = AsyncMock(side_effect=ValueError("Document not found: d99"))

        resp = client.post("/api/analyses", json={"documentId": "d99"})
        assert resp.status_code == 404

    def test_create_analysis_empty_document_id(self, client, mock_analysis_service):
        resp = client.post("/api/analyses", json={"documentId": ""})
        assert resp.status_code == 400

    def test_create_analysis_whitespace_document_id(self, client, mock_analysis_service):
        resp = client.post("/api/analyses", json={"documentId": "   "})
        assert resp.status_code == 400

    def test_delete_analysis(self, client, mock_analysis_service):
        mock_analysis_service.delete = AsyncMock(return_value=True)

        resp = client.delete("/api/analyses/j1")
        assert resp.status_code == 204

    def test_delete_analysis_not_found(self, client, mock_analysis_service):
        mock_analysis_service.delete = AsyncMock(return_value=False)

        resp = client.delete("/api/analyses/missing")
        assert resp.status_code == 404
