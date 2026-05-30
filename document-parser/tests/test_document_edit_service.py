"""Tests for DocumentEditService generalized page-element edits."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domain.models import AnalysisJob, AnalysisStatus, Document
from persistence.analysis_repo import SqliteAnalysisRepository
from persistence.database import init_db
from persistence.document_edit_repo import SqliteDocumentEditRepository
from persistence.document_repo import SqliteDocumentRepository
from services.document_edit_service import DocumentEditConflictError, DocumentEditService

FIXTURE_DIR = (
    Path(__file__).resolve().parent.parent
    / "local-experiments"
    / "docling-edit"
    / "output"
    / "test-file"
)


@pytest.fixture(autouse=True)
async def setup_db(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("persistence.database.DB_PATH", db_path)
    await init_db()
    yield


@pytest.fixture
def fixture_document_json() -> str:
    return (FIXTURE_DIR / "document.json").read_text(encoding="utf-8")


@pytest.fixture
def fixture_pages_json() -> str:
    return (FIXTURE_DIR / "pages.json").read_text(encoding="utf-8")


@pytest.fixture
async def doc() -> Document:
    repo = SqliteDocumentRepository()
    document = Document(
        id="doc-edit-1", filename="test-file.pdf", storage_path="/tmp/test-file.pdf"
    )
    await repo.insert(document)
    return document


@pytest.fixture
def repos():
    return {
        "documents": SqliteDocumentRepository(),
        "analyses": SqliteAnalysisRepository(),
        "edits": SqliteDocumentEditRepository(),
    }


@pytest.fixture
async def analysis(doc, repos, fixture_document_json: str, fixture_pages_json: str) -> AnalysisJob:
    job = AnalysisJob(document_id=doc.id, status=AnalysisStatus.COMPLETED)
    await repos["analyses"].insert(job)
    job.document_json = fixture_document_json
    job.pages_json = fixture_pages_json
    job.content_markdown = "fixture markdown"
    job.content_html = "<p>fixture html</p>"
    job.completed_at = datetime.now(UTC)
    await repos["analyses"].update_status(job)
    return job


@pytest.fixture
def service(repos) -> DocumentEditService:
    return DocumentEditService(
        document_repo=repos["documents"],
        analysis_repo=repos["analyses"],
        edit_repo=repos["edits"],
    )


class TestDocumentEditService:
    async def test_update_content_preview_and_commit(self, service, repos, doc, analysis):
        updated_content = "Updated correspondence block"

        session = await service.apply_commands(
            doc.id,
            commands=[
                {
                    "action": "update_page_element",
                    "targetRef": "#/texts/12",
                    "payload": {"content": updated_content},
                }
            ],
        )

        preview_element = _element_by_ref(session["pages"], "#/texts/12")
        assert preview_element["content"] == updated_content
        assert len(session["pendingCommands"]) == 1

        commit_result = await service.commit(doc.id, session["pages"])
        assert commit_result["committed"] is True
        assert commit_result["consistent"] is True

        persisted = await repos["analyses"].find_latest_completed_by_document(doc.id)
        assert persisted is not None
        persisted_element = _element_by_ref(json.loads(persisted.pages_json or "[]"), "#/texts/12")
        assert persisted_element["content"] == updated_content

        persisted_doc = json.loads(persisted.document_json or "{}")
        text_item = next(
            item for item in persisted_doc["texts"] if item["self_ref"] == "#/texts/12"
        )
        assert text_item["text"] == updated_content
        assert text_item["orig"] == updated_content

        assert await repos["edits"].find_pending_for_document(doc.id) == []

    async def test_update_bbox_preview_and_commit(self, service, repos, doc, analysis):
        updated_bbox = [120.5, 630.25, 340.75, 655.5]

        session = await service.apply_commands(
            doc.id,
            commands=[
                {
                    "action": "update_page_element",
                    "targetRef": "#/texts/12",
                    "payload": {"bbox": updated_bbox},
                }
            ],
        )

        preview_element = _element_by_ref(session["pages"], "#/texts/12")
        assert preview_element["bbox"] == pytest.approx(updated_bbox)

        commit_result = await service.commit(doc.id, session["pages"])
        assert commit_result["committed"] is True
        persisted = await repos["analyses"].find_latest_completed_by_document(doc.id)
        assert persisted is not None
        persisted_element = _element_by_ref(json.loads(persisted.pages_json or "[]"), "#/texts/12")
        assert persisted_element["bbox"] == pytest.approx(updated_bbox)

    async def test_allows_safe_type_change_within_text_family(self, service, doc, analysis):
        session = await service.apply_commands(
            doc.id,
            commands=[
                {
                    "action": "update_page_element",
                    "targetRef": "#/texts/12",
                    "payload": {"type": "section_header"},
                }
            ],
        )

        preview_element = _element_by_ref(session["pages"], "#/texts/12")
        assert preview_element["type"] == "section_header"

        commit_result = await service.commit(doc.id, session["pages"])
        assert commit_result["committed"] is True

        persisted = await service._analyses.find_latest_completed_by_document(doc.id)
        assert persisted is not None
        text_item = _text_item_by_ref(json.loads(persisted.document_json or "{}"), "#/texts/12")
        assert text_item["label"] == "section_header"
        assert text_item["level"] == 1

    async def test_replaces_committed_text_item_shape_for_title_transition(
        self, service, doc, analysis
    ):
        session = await service.apply_commands(
            doc.id,
            commands=[
                {
                    "action": "update_page_element",
                    "targetRef": "#/texts/12",
                    "payload": {"type": "title"},
                }
            ],
        )

        preview_element = _element_by_ref(session["pages"], "#/texts/12")
        assert preview_element["type"] == "title"

        commit_result = await service.commit(doc.id, session["pages"])
        assert commit_result["committed"] is True

        persisted = await service._analyses.find_latest_completed_by_document(doc.id)
        assert persisted is not None
        text_item = _text_item_by_ref(json.loads(persisted.document_json or "{}"), "#/texts/12")
        assert text_item["label"] == "title"
        assert "level" not in text_item

    async def test_rejects_cross_family_type_change_from_table(self, service, doc, analysis):
        with pytest.raises(DocumentEditConflictError) as exc:
            await service.apply_commands(
                doc.id,
                commands=[
                    {
                        "action": "update_page_element",
                        "targetRef": "#/tables/0",
                        "payload": {"type": "section_header"},
                    }
                ],
            )

        assert "allowed: table" in str(exc.value)


def _element_by_ref(pages: list[dict], target_ref: str) -> dict:
    for page in pages:
        for element in page.get("elements", []):
            if element.get("self_ref") == target_ref:
                return element
    raise AssertionError(f"Element not found in pages: {target_ref}")


def _text_item_by_ref(document_json: dict, target_ref: str) -> dict:
    for item in document_json.get("texts", []):
        if item.get("self_ref") == target_ref:
            return item
    raise AssertionError(f"Text item not found in document_json: {target_ref}")
