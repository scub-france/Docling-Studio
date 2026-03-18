"""Tests for API schemas — camelCase serialization."""

from datetime import datetime

from api.schemas import (
    AnalysisResponse,
    CreateAnalysisRequest,
    DocumentResponse,
    _to_camel,
)


class TestToCamel:
    def test_single_word(self):
        assert _to_camel("status") == "status"

    def test_two_words(self):
        assert _to_camel("document_id") == "documentId"

    def test_three_words(self):
        assert _to_camel("content_html_raw") == "contentHtmlRaw"

    def test_already_camel(self):
        assert _to_camel("documentId") == "documentId"


class TestDocumentResponse:
    def test_serializes_to_camel_case(self):
        doc = DocumentResponse(
            id="1",
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            page_count=5,
            created_at="2024-01-01",
        )
        data = doc.model_dump(by_alias=True)
        assert "contentType" in data
        assert "fileSize" in data
        assert "pageCount" in data
        assert "createdAt" in data
        # Original snake_case should not appear
        assert "content_type" not in data
        assert "file_size" not in data

    def test_optional_fields_default_to_none(self):
        doc = DocumentResponse(id="1", filename="test.pdf", created_at="2024-01-01")
        assert doc.content_type is None
        assert doc.file_size is None
        assert doc.page_count is None


class TestAnalysisResponse:
    def test_serializes_to_camel_case(self):
        resp = AnalysisResponse(
            id="1",
            document_id="d1",
            status="COMPLETED",
            content_markdown="# Hello",
            pages_json="[]",
            created_at="2024-01-01",
        )
        data = resp.model_dump(by_alias=True)
        assert "documentId" in data
        assert "contentMarkdown" in data
        assert "pagesJson" in data
        assert "errorMessage" in data
        assert "startedAt" in data
        assert "completedAt" in data

    def test_populate_by_name(self):
        """Can create using snake_case field names."""
        resp = AnalysisResponse(
            id="1",
            document_id="d1",
            status="PENDING",
            created_at="2024-01-01",
        )
        assert resp.document_id == "d1"


class TestCreateAnalysisRequest:
    def test_parses_document_id(self):
        req = CreateAnalysisRequest(documentId="doc-42")
        assert req.documentId == "doc-42"
