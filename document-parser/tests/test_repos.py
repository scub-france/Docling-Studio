"""Tests for persistence repositories using a temporary SQLite database."""

import pytest

from domain.models import AnalysisJob, AnalysisStatus, Document
from persistence import analysis_repo, document_repo
from persistence.database import init_db


@pytest.fixture(autouse=True)
async def setup_db(monkeypatch, tmp_path):
    """Use a temp file SQLite database for all repo tests."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("persistence.database.DB_PATH", db_path)
    await init_db()
    yield


class TestDocumentRepo:
    async def test_insert_and_find_by_id(self):
        doc = Document(
            id="doc-1",
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            storage_path="/tmp/test.pdf",
        )
        await document_repo.insert(doc)

        found = await document_repo.find_by_id("doc-1")
        assert found is not None
        assert found.id == "doc-1"
        assert found.filename == "test.pdf"
        assert found.file_size == 1024

    async def test_find_by_id_not_found(self):
        found = await document_repo.find_by_id("nonexistent")
        assert found is None

    async def test_find_all(self):
        for i in range(3):
            doc = Document(id=f"doc-{i}", filename=f"file{i}.pdf", storage_path=f"/tmp/{i}")
            await document_repo.insert(doc)

        all_docs = await document_repo.find_all()
        assert len(all_docs) == 3

    async def test_update_page_count(self):
        doc = Document(id="doc-1", filename="test.pdf", storage_path="/tmp/test.pdf")
        await document_repo.insert(doc)

        await document_repo.update_page_count("doc-1", 10)

        updated = await document_repo.find_by_id("doc-1")
        assert updated.page_count == 10

    async def test_delete(self):
        doc = Document(id="doc-1", filename="test.pdf", storage_path="/tmp/test.pdf")
        await document_repo.insert(doc)

        deleted = await document_repo.delete("doc-1")
        assert deleted is True

        found = await document_repo.find_by_id("doc-1")
        assert found is None

    async def test_delete_nonexistent(self):
        deleted = await document_repo.delete("nonexistent")
        assert deleted is False


class TestAnalysisRepo:
    async def _insert_doc(self):
        doc = Document(id="doc-1", filename="test.pdf", storage_path="/tmp/test.pdf")
        await document_repo.insert(doc)
        return doc

    async def test_insert_and_find_by_id(self):
        await self._insert_doc()
        job = AnalysisJob(id="job-1", document_id="doc-1")
        await analysis_repo.insert(job)

        found = await analysis_repo.find_by_id("job-1")
        assert found is not None
        assert found.id == "job-1"
        assert found.document_id == "doc-1"
        assert found.status == AnalysisStatus.PENDING
        assert found.document_filename == "test.pdf"

    async def test_find_by_id_not_found(self):
        found = await analysis_repo.find_by_id("nonexistent")
        assert found is None

    async def test_find_all(self):
        await self._insert_doc()
        for i in range(3):
            job = AnalysisJob(id=f"job-{i}", document_id="doc-1")
            await analysis_repo.insert(job)

        all_jobs = await analysis_repo.find_all()
        assert len(all_jobs) == 3

    async def test_update_status(self):
        await self._insert_doc()
        job = AnalysisJob(id="job-1", document_id="doc-1")
        await analysis_repo.insert(job)

        job.mark_running()
        await analysis_repo.update_status(job)

        found = await analysis_repo.find_by_id("job-1")
        assert found.status == AnalysisStatus.RUNNING
        assert found.started_at is not None

    async def test_update_status_completed(self):
        await self._insert_doc()
        job = AnalysisJob(id="job-1", document_id="doc-1")
        await analysis_repo.insert(job)

        job.mark_running()
        job.mark_completed(markdown="# Test", html="<h1>Test</h1>", pages_json="[]")
        await analysis_repo.update_status(job)

        found = await analysis_repo.find_by_id("job-1")
        assert found.status == AnalysisStatus.COMPLETED
        assert found.content_markdown == "# Test"
        assert found.content_html == "<h1>Test</h1>"
        assert found.pages_json == "[]"

    async def test_delete(self):
        await self._insert_doc()
        job = AnalysisJob(id="job-1", document_id="doc-1")
        await analysis_repo.insert(job)

        deleted = await analysis_repo.delete("job-1")
        assert deleted is True

        found = await analysis_repo.find_by_id("job-1")
        assert found is None

    async def test_delete_nonexistent(self):
        deleted = await analysis_repo.delete("nonexistent")
        assert deleted is False

    async def test_delete_by_document(self):
        await self._insert_doc()
        for i in range(3):
            job = AnalysisJob(id=f"job-{i}", document_id="doc-1")
            await analysis_repo.insert(job)

        count = await analysis_repo.delete_by_document("doc-1")
        assert count == 3

        all_jobs = await analysis_repo.find_all()
        assert len(all_jobs) == 0
