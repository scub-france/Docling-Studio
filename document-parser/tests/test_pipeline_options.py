"""Tests for pipeline options — build_converter, convert_document routing, service forwarding."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
)

from domain.parsing import build_converter, convert_document, get_default_converter


# ---------------------------------------------------------------------------
# build_converter — verifies Docling pipeline options are wired correctly
# ---------------------------------------------------------------------------

class TestBuildConverter:
    """Verify that build_converter produces a DocumentConverter with the right PdfPipelineOptions."""

    def _get_pipeline_options(self, converter) -> PdfPipelineOptions:
        """Extract PdfPipelineOptions from a DocumentConverter."""
        fmt_opt = converter.format_to_options[InputFormat.PDF]
        return fmt_opt.pipeline_options

    def test_defaults(self):
        conv = build_converter()
        opts = self._get_pipeline_options(conv)
        assert opts.do_ocr is True
        assert opts.do_table_structure is True
        assert opts.table_structure_options.mode == TableFormerMode.ACCURATE
        assert opts.do_code_enrichment is False
        assert opts.do_formula_enrichment is False
        assert opts.do_picture_classification is False
        assert opts.do_picture_description is False
        assert opts.generate_page_images is False
        assert opts.generate_picture_images is False
        assert opts.images_scale == 1.0

    def test_ocr_disabled(self):
        conv = build_converter(do_ocr=False)
        opts = self._get_pipeline_options(conv)
        assert opts.do_ocr is False

    def test_table_mode_fast(self):
        conv = build_converter(table_mode="fast")
        opts = self._get_pipeline_options(conv)
        assert opts.table_structure_options.mode == TableFormerMode.FAST

    def test_table_mode_accurate(self):
        conv = build_converter(table_mode="accurate")
        opts = self._get_pipeline_options(conv)
        assert opts.table_structure_options.mode == TableFormerMode.ACCURATE

    def test_table_structure_disabled(self):
        conv = build_converter(do_table_structure=False)
        opts = self._get_pipeline_options(conv)
        assert opts.do_table_structure is False

    def test_code_enrichment_enabled(self):
        conv = build_converter(do_code_enrichment=True)
        opts = self._get_pipeline_options(conv)
        assert opts.do_code_enrichment is True

    def test_formula_enrichment_enabled(self):
        conv = build_converter(do_formula_enrichment=True)
        opts = self._get_pipeline_options(conv)
        assert opts.do_formula_enrichment is True

    def test_picture_classification_enabled(self):
        conv = build_converter(do_picture_classification=True)
        opts = self._get_pipeline_options(conv)
        assert opts.do_picture_classification is True

    def test_picture_description_enabled(self):
        conv = build_converter(do_picture_description=True)
        opts = self._get_pipeline_options(conv)
        assert opts.do_picture_description is True

    def test_generate_picture_images(self):
        conv = build_converter(generate_picture_images=True)
        opts = self._get_pipeline_options(conv)
        assert opts.generate_picture_images is True

    def test_generate_page_images(self):
        conv = build_converter(generate_page_images=True)
        opts = self._get_pipeline_options(conv)
        assert opts.generate_page_images is True

    def test_images_scale(self):
        conv = build_converter(images_scale=2.0)
        opts = self._get_pipeline_options(conv)
        assert opts.images_scale == 2.0

    def test_all_options_combined(self):
        conv = build_converter(
            do_ocr=False,
            do_table_structure=True,
            table_mode="fast",
            do_code_enrichment=True,
            do_formula_enrichment=True,
            do_picture_classification=True,
            do_picture_description=True,
            generate_picture_images=True,
            generate_page_images=True,
            images_scale=1.5,
        )
        opts = self._get_pipeline_options(conv)
        assert opts.do_ocr is False
        assert opts.do_table_structure is True
        assert opts.table_structure_options.mode == TableFormerMode.FAST
        assert opts.do_code_enrichment is True
        assert opts.do_formula_enrichment is True
        assert opts.do_picture_classification is True
        assert opts.do_picture_description is True
        assert opts.generate_picture_images is True
        assert opts.generate_page_images is True
        assert opts.images_scale == 1.5


# ---------------------------------------------------------------------------
# convert_document — default vs custom converter routing
# ---------------------------------------------------------------------------

class TestConvertDocumentRouting:
    """Verify convert_document uses default converter for default opts, custom otherwise."""

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_default_converter_with_all_defaults(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_get_default.return_value = mock_conv

        convert_document("/tmp/test.pdf")

        mock_get_default.assert_called_once()
        mock_build.assert_not_called()

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_ocr_disabled(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", do_ocr=False)

        mock_build.assert_called_once()
        mock_get_default.assert_not_called()

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_table_mode_fast(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", table_mode="fast")

        mock_build.assert_called_once()
        assert mock_build.call_args.kwargs["table_mode"] == "fast"

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_code_enrichment_on(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", do_code_enrichment=True)

        mock_build.assert_called_once()
        assert mock_build.call_args.kwargs["do_code_enrichment"] is True

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_formula_enrichment_on(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", do_formula_enrichment=True)

        mock_build.assert_called_once()

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_picture_options_on(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", do_picture_classification=True)

        mock_build.assert_called_once()

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_generate_images_on(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", generate_picture_images=True)

        mock_build.assert_called_once()

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_uses_custom_converter_when_images_scale_changed(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document("/tmp/test.pdf", images_scale=2.0)

        mock_build.assert_called_once()
        assert mock_build.call_args.kwargs["images_scale"] == 2.0

    @patch("domain.parsing.get_default_converter")
    @patch("domain.parsing.build_converter")
    def test_forwards_all_options_to_build_converter(self, mock_build, mock_get_default):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_result.document.pages = {}
        mock_result.document.iterate_items.return_value = []
        mock_result.document.export_to_markdown.return_value = ""
        mock_result.document.export_to_html.return_value = ""
        mock_conv.convert.return_value = mock_result
        mock_build.return_value = mock_conv

        convert_document(
            "/tmp/test.pdf",
            do_ocr=False,
            do_table_structure=False,
            table_mode="fast",
            do_code_enrichment=True,
            do_formula_enrichment=True,
            do_picture_classification=True,
            do_picture_description=True,
            generate_picture_images=True,
            generate_page_images=True,
            images_scale=1.5,
        )

        mock_build.assert_called_once_with(
            do_ocr=False,
            do_table_structure=False,
            table_mode="fast",
            do_code_enrichment=True,
            do_formula_enrichment=True,
            do_picture_classification=True,
            do_picture_description=True,
            generate_picture_images=True,
            generate_page_images=True,
            images_scale=1.5,
        )


# ---------------------------------------------------------------------------
# Service layer — pipeline options forwarding
# ---------------------------------------------------------------------------

class TestServiceForwardsPipelineOptions:
    """Verify analysis_service.create and _run_analysis forward pipeline options."""

    @pytest.fixture
    def mock_doc(self):
        from domain.models import Document
        return Document(id="d1", filename="test.pdf", storage_path="/tmp/test.pdf")

    @pytest.fixture
    def mock_job(self):
        from domain.models import AnalysisJob
        return AnalysisJob(id="j1", document_id="d1", document_filename="test.pdf")

    @patch("services.analysis_service.document_repo")
    @patch("services.analysis_service.analysis_repo")
    @patch("services.analysis_service._run_analysis")
    @pytest.mark.asyncio
    async def test_create_passes_pipeline_options_to_run(
        self, mock_run, mock_analysis_repo, mock_doc_repo, mock_doc,
    ):
        mock_doc_repo.find_by_id = AsyncMock(return_value=mock_doc)
        mock_analysis_repo.insert = AsyncMock()
        # Patch _run_analysis as a coroutine that we can inspect
        mock_run.return_value = None

        from services import analysis_service

        opts = {"do_ocr": False, "table_mode": "fast"}

        # We need to patch asyncio.create_task to capture the coroutine args
        with patch("services.analysis_service.asyncio.create_task") as mock_task:
            await analysis_service.create("d1", pipeline_options=opts)

            # create_task should have been called with _run_analysis(...)
            mock_task.assert_called_once()

    @patch("services.analysis_service.document_repo")
    @patch("services.analysis_service.analysis_repo")
    @pytest.mark.asyncio
    async def test_create_passes_none_when_no_options(
        self, mock_analysis_repo, mock_doc_repo, mock_doc,
    ):
        mock_doc_repo.find_by_id = AsyncMock(return_value=mock_doc)
        mock_analysis_repo.insert = AsyncMock()

        from services import analysis_service

        with patch("services.analysis_service.asyncio.create_task") as mock_task:
            await analysis_service.create("d1")
            mock_task.assert_called_once()

    @patch("services.analysis_service.analysis_repo")
    @patch("services.analysis_service.document_repo")
    @patch("services.analysis_service.convert_document")
    @pytest.mark.asyncio
    async def test_run_analysis_forwards_options_to_convert(
        self, mock_convert, mock_doc_repo, mock_analysis_repo, mock_job,
    ):
        from domain.parsing import ConversionResult, PageDetail

        mock_analysis_repo.find_by_id = AsyncMock(return_value=mock_job)
        mock_analysis_repo.update_status = AsyncMock()
        mock_doc_repo.update_page_count = AsyncMock()
        mock_convert.return_value = ConversionResult(
            page_count=1,
            content_markdown="# Test",
            content_html="<h1>Test</h1>",
            pages=[PageDetail(page_number=1, width=612.0, height=792.0)],
        )

        from services.analysis_service import _run_analysis

        opts = {
            "do_ocr": False,
            "table_mode": "fast",
            "do_code_enrichment": True,
            "do_formula_enrichment": False,
            "do_picture_classification": False,
            "do_picture_description": False,
            "generate_picture_images": True,
            "generate_page_images": False,
            "images_scale": 2.0,
        }

        await _run_analysis("j1", "/tmp/test.pdf", "test.pdf", opts)

        mock_convert.assert_called_once_with(
            "/tmp/test.pdf",
            do_ocr=False,
            table_mode="fast",
            do_code_enrichment=True,
            do_formula_enrichment=False,
            do_picture_classification=False,
            do_picture_description=False,
            generate_picture_images=True,
            generate_page_images=False,
            images_scale=2.0,
        )

    @patch("services.analysis_service.analysis_repo")
    @patch("services.analysis_service.document_repo")
    @patch("services.analysis_service.convert_document")
    @pytest.mark.asyncio
    async def test_run_analysis_uses_defaults_when_no_options(
        self, mock_convert, mock_doc_repo, mock_analysis_repo, mock_job,
    ):
        from domain.parsing import ConversionResult, PageDetail

        mock_analysis_repo.find_by_id = AsyncMock(return_value=mock_job)
        mock_analysis_repo.update_status = AsyncMock()
        mock_doc_repo.update_page_count = AsyncMock()
        mock_convert.return_value = ConversionResult(
            page_count=1,
            content_markdown="",
            content_html="",
            pages=[PageDetail(page_number=1, width=612.0, height=792.0)],
        )

        from services.analysis_service import _run_analysis

        await _run_analysis("j1", "/tmp/test.pdf", "test.pdf", None)

        # Called with file_path only (no kwargs spread from empty dict)
        mock_convert.assert_called_once_with("/tmp/test.pdf")

    @patch("services.analysis_service.analysis_repo")
    @patch("services.analysis_service.document_repo")
    @patch("services.analysis_service.convert_document")
    @pytest.mark.asyncio
    async def test_run_analysis_marks_failed_on_error(
        self, mock_convert, mock_doc_repo, mock_analysis_repo, mock_job,
    ):
        mock_analysis_repo.find_by_id = AsyncMock(return_value=mock_job)
        mock_analysis_repo.update_status = AsyncMock()
        mock_convert.side_effect = RuntimeError("Docling crashed")

        from services.analysis_service import _run_analysis

        await _run_analysis("j1", "/tmp/test.pdf", "test.pdf", {"do_ocr": False})

        # Should have called update_status twice: RUNNING then FAILED
        assert mock_analysis_repo.update_status.call_count == 2
        last_job = mock_analysis_repo.update_status.call_args_list[-1][0][0]
        assert last_job.status.value == "FAILED"
        assert "Docling crashed" in last_job.error_message


# ---------------------------------------------------------------------------
# API endpoint — full request/response with pipeline options
# ---------------------------------------------------------------------------

class TestAnalysisEndpointPipelineOptions:
    """Integration-level tests for the analysis creation endpoint with pipeline options."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app, raise_server_exceptions=False)

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_no_pipeline_options_sends_none(self, mock_create, client):
        from domain.models import AnalysisJob
        mock_create.return_value = AnalysisJob(id="j1", document_id="d1")

        client.post("/api/analyses", json={"documentId": "d1"})

        mock_create.assert_called_once_with("d1", pipeline_options=None)

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_empty_pipeline_options_object_uses_defaults(self, mock_create, client):
        from domain.models import AnalysisJob
        mock_create.return_value = AnalysisJob(id="j1", document_id="d1")

        client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {},
        })

        opts = mock_create.call_args.kwargs["pipeline_options"]
        assert opts["do_ocr"] is True
        assert opts["do_table_structure"] is True
        assert opts["table_mode"] == "accurate"
        assert opts["do_code_enrichment"] is False
        assert opts["do_formula_enrichment"] is False
        assert opts["images_scale"] == 1.0

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_partial_pipeline_options_merges_with_defaults(self, mock_create, client):
        from domain.models import AnalysisJob
        mock_create.return_value = AnalysisJob(id="j1", document_id="d1")

        client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {"do_ocr": False, "images_scale": 1.5},
        })

        opts = mock_create.call_args.kwargs["pipeline_options"]
        assert opts["do_ocr"] is False
        assert opts["images_scale"] == 1.5
        # All other fields should have defaults
        assert opts["do_table_structure"] is True
        assert opts["table_mode"] == "accurate"
        assert opts["do_code_enrichment"] is False
        assert opts["do_formula_enrichment"] is False
        assert opts["do_picture_classification"] is False
        assert opts["do_picture_description"] is False
        assert opts["generate_picture_images"] is False
        assert opts["generate_page_images"] is False

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_full_pipeline_options(self, mock_create, client):
        from domain.models import AnalysisJob
        mock_create.return_value = AnalysisJob(id="j1", document_id="d1")

        payload = {
            "documentId": "d1",
            "pipelineOptions": {
                "do_ocr": False,
                "do_table_structure": False,
                "table_mode": "fast",
                "do_code_enrichment": True,
                "do_formula_enrichment": True,
                "do_picture_classification": True,
                "do_picture_description": True,
                "generate_picture_images": True,
                "generate_page_images": True,
                "images_scale": 2.0,
            },
        }

        resp = client.post("/api/analyses", json=payload)
        assert resp.status_code == 200

        opts = mock_create.call_args.kwargs["pipeline_options"]
        assert opts == payload["pipelineOptions"]

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_invalid_pipeline_option_type_rejected(self, mock_create, client):
        resp = client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {"do_ocr": "not-a-bool"},
        })
        assert resp.status_code == 422

    @patch("services.analysis_service.create", new_callable=AsyncMock)
    def test_unknown_pipeline_option_ignored(self, mock_create, client):
        from domain.models import AnalysisJob
        mock_create.return_value = AnalysisJob(id="j1", document_id="d1")

        resp = client.post("/api/analyses", json={
            "documentId": "d1",
            "pipelineOptions": {"do_ocr": True, "unknown_field": True},
        })
        # Pydantic ignores extra fields by default
        assert resp.status_code == 200
