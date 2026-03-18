"""Tests for domain models."""

from datetime import datetime, timezone

from domain.models import AnalysisJob, AnalysisStatus, Document


class TestDocument:
    def test_default_values(self):
        doc = Document()
        assert doc.id  # auto-generated UUID
        assert doc.filename == ""
        assert doc.content_type is None
        assert doc.file_size is None
        assert doc.page_count is None
        assert doc.storage_path == ""
        assert isinstance(doc.created_at, datetime)

    def test_custom_values(self):
        doc = Document(
            id="doc-1",
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            page_count=5,
            storage_path="/tmp/test.pdf",
        )
        assert doc.id == "doc-1"
        assert doc.filename == "test.pdf"
        assert doc.file_size == 1024
        assert doc.page_count == 5

    def test_unique_ids(self):
        d1 = Document()
        d2 = Document()
        assert d1.id != d2.id


class TestAnalysisJob:
    def test_default_values(self):
        job = AnalysisJob()
        assert job.id
        assert job.document_id == ""
        assert job.status == AnalysisStatus.PENDING
        assert job.content_markdown is None
        assert job.content_html is None
        assert job.pages_json is None
        assert job.error_message is None
        assert job.started_at is None
        assert job.completed_at is None

    def test_mark_running(self):
        job = AnalysisJob()
        assert job.started_at is None

        job.mark_running()

        assert job.status == AnalysisStatus.RUNNING
        assert job.started_at is not None

    def test_mark_completed(self):
        job = AnalysisJob()
        job.mark_running()

        job.mark_completed(
            markdown="# Title",
            html="<h1>Title</h1>",
            pages_json='[{"page": 1}]',
        )

        assert job.status == AnalysisStatus.COMPLETED
        assert job.content_markdown == "# Title"
        assert job.content_html == "<h1>Title</h1>"
        assert job.pages_json == '[{"page": 1}]'
        assert job.completed_at is not None

    def test_mark_failed(self):
        job = AnalysisJob()
        job.mark_running()

        job.mark_failed("Something went wrong")

        assert job.status == AnalysisStatus.FAILED
        assert job.error_message == "Something went wrong"
        assert job.completed_at is not None

    def test_status_transitions(self):
        """Test full lifecycle: PENDING -> RUNNING -> COMPLETED."""
        job = AnalysisJob()
        assert job.status == AnalysisStatus.PENDING

        job.mark_running()
        assert job.status == AnalysisStatus.RUNNING

        job.mark_completed(markdown="md", html="html", pages_json="[]")
        assert job.status == AnalysisStatus.COMPLETED


class TestAnalysisStatus:
    def test_values(self):
        assert AnalysisStatus.PENDING == "PENDING"
        assert AnalysisStatus.RUNNING == "RUNNING"
        assert AnalysisStatus.COMPLETED == "COMPLETED"
        assert AnalysisStatus.FAILED == "FAILED"

    def test_from_string(self):
        assert AnalysisStatus("PENDING") == AnalysisStatus.PENDING
        assert AnalysisStatus("COMPLETED") == AnalysisStatus.COMPLETED
