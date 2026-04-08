"""Tests for AnalysisService — callbacks, concurrency, orchestration, and batching."""

from __future__ import annotations

import asyncio
import functools
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.value_objects import ConversionResult, PageDetail
from services.analysis_service import (
    AnalysisService,
    _count_pdf_pages,
    _extract_html_body,
    _merge_results,
    _on_task_done,
)


class TestOnTaskDone:
    """Bug #1: _on_task_done must call _mark_failed when the task raises."""

    @pytest.mark.asyncio
    async def test_exception_marks_job_failed(self):
        """When a background task raises, the job should be marked FAILED."""
        job_id = "job-123"

        # Create a task that raises
        async def failing_task():
            raise RuntimeError("unexpected failure")

        task = asyncio.create_task(failing_task())
        await asyncio.sleep(0)  # let the task fail

        with patch("services.analysis_service._mark_failed", new_callable=AsyncMock) as mock_mark:
            _on_task_done(task, job_id=job_id)
            # ensure_future schedules it; give the event loop a tick
            await asyncio.sleep(0)

        mock_mark.assert_called_once_with(job_id, "unexpected failure")

    @pytest.mark.asyncio
    async def test_exception_uses_classify_error(self):
        """_on_task_done should route exceptions through _classify_error."""
        job_id = "job-classify"

        async def timeout_task():
            raise TimeoutError("timeout exceeded while processing")

        task = asyncio.create_task(timeout_task())
        await asyncio.sleep(0)

        with patch("services.analysis_service._mark_failed", new_callable=AsyncMock) as mock_mark:
            _on_task_done(task, job_id=job_id)
            await asyncio.sleep(0)

        mock_mark.assert_called_once_with(
            job_id, "Processing took too long — try with fewer pages or simpler options"
        )

    @pytest.mark.asyncio
    async def test_cancelled_task_marks_job_failed(self):
        """When a background task is cancelled, the job should be marked FAILED."""
        job_id = "job-456"

        async def slow_task():
            await asyncio.sleep(999)

        import contextlib

        task = asyncio.create_task(slow_task())
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        with patch("services.analysis_service._mark_failed", new_callable=AsyncMock) as mock_mark:
            _on_task_done(task, job_id=job_id)
            await asyncio.sleep(0)

        mock_mark.assert_called_once_with(job_id, "Task was cancelled")

    @pytest.mark.asyncio
    async def test_successful_task_does_not_mark_failed(self):
        """When a background task succeeds, _mark_failed should not be called."""
        job_id = "job-789"

        async def ok_task():
            return "done"

        task = asyncio.create_task(ok_task())
        await task

        with patch("services.analysis_service._mark_failed", new_callable=AsyncMock) as mock_mark:
            _on_task_done(task, job_id=job_id)
            await asyncio.sleep(0)

        mock_mark.assert_not_called()


class TestAnalysisServiceCancellation:
    """Verify delete cancels running tasks."""

    @pytest.mark.asyncio
    async def test_delete_cancels_running_task(self):
        """Deleting a job while running should cancel its task."""
        converter = MagicMock()
        service = AnalysisService(converter=converter)

        blocker = asyncio.Event()

        async def slow_analysis():
            await blocker.wait()

        task = asyncio.create_task(slow_analysis())
        service._running_tasks["j1"] = task

        with patch("services.analysis_service.analysis_repo") as mock_repo:
            mock_repo.delete = AsyncMock(return_value=True)
            result = await service.delete("j1")

        assert result is True
        assert task.cancelling() or task.cancelled()
        assert "j1" not in service._running_tasks

    @pytest.mark.asyncio
    async def test_delete_completed_job_no_error(self):
        """Deleting a completed job should not raise even if no task tracked."""
        converter = MagicMock()
        service = AnalysisService(converter=converter)

        with patch("services.analysis_service.analysis_repo") as mock_repo:
            mock_repo.delete = AsyncMock(return_value=True)
            result = await service.delete("j-gone")

        assert result is True

    @pytest.mark.asyncio
    async def test_task_cleaned_from_running_on_completion(self):
        """After a task completes, it should be removed from _running_tasks."""
        converter = MagicMock()
        service = AnalysisService(converter=converter)

        async def instant():
            pass

        task = asyncio.create_task(instant())
        service._running_tasks["j1"] = task
        task.add_done_callback(functools.partial(service._on_task_done, job_id="j1"))
        await task

        assert "j1" not in service._running_tasks


class TestAnalysisServiceConcurrency:
    """Verify that the semaphore limits concurrent analysis jobs."""

    def test_semaphore_initialized_with_max_concurrent(self):
        converter = MagicMock()
        service = AnalysisService(converter=converter, max_concurrent=5)
        assert service._semaphore._value == 5

    def test_default_max_concurrent(self):
        converter = MagicMock()
        service = AnalysisService(converter=converter)
        assert service._semaphore._value == 3

    @pytest.mark.asyncio
    async def test_semaphore_limits_parallel_jobs(self):
        """Only max_concurrent jobs should run in parallel; others must wait."""
        call_order: list[str] = []
        blocker = asyncio.Event()

        converter = MagicMock()
        service = AnalysisService(converter=converter, max_concurrent=1)

        async def fake_inner(self, *args, **kwargs):
            call_order.append("start")
            await blocker.wait()
            call_order.append("end")

        with patch.object(AnalysisService, "_run_analysis_inner", fake_inner):
            t1 = asyncio.create_task(service._run_analysis("j1", "/f", "f.pdf"))
            t2 = asyncio.create_task(service._run_analysis("j2", "/f", "f.pdf"))
            await asyncio.sleep(0.05)

            # With max_concurrent=1, only one task should have started
            assert call_order.count("start") == 1

            blocker.set()
            await asyncio.gather(t1, t2)

            # Both should have completed
            assert call_order.count("start") == 2
            assert call_order.count("end") == 2


# ---------------------------------------------------------------------------
# Batch helper tests
# ---------------------------------------------------------------------------


class TestCountPdfPages:
    def test_valid_pdf(self, tmp_path):
        """A real (minimal) PDF should return its page count."""
        # Create a minimal valid 1-page PDF using pypdfium2
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument.new()
        pdf.new_page(612, 792)
        path = tmp_path / "test.pdf"
        pdf.save(str(path))
        pdf.close()

        assert _count_pdf_pages(str(path)) == 1

    def test_non_pdf_file(self, tmp_path):
        """A non-PDF file should return 0."""
        path = tmp_path / "test.docx"
        path.write_bytes(b"PK\x03\x04 not a pdf")
        assert _count_pdf_pages(str(path)) == 0

    def test_nonexistent_file(self):
        """A nonexistent file should return 0."""
        assert _count_pdf_pages("/no/such/file.pdf") == 0

    def test_empty_file(self, tmp_path):
        """An empty file should return 0."""
        path = tmp_path / "empty.pdf"
        path.write_bytes(b"")
        assert _count_pdf_pages(str(path)) == 0


class TestExtractHtmlBody:
    def test_extracts_body(self):
        html = '<html><head></head><body class="x"><p>Hello</p></body></html>'
        assert _extract_html_body(html) == "<p>Hello</p>"

    def test_no_body_tag_returns_raw(self):
        html = "<p>No body tag</p>"
        assert _extract_html_body(html) == html

    def test_empty_body(self):
        html = "<html><body></body></html>"
        assert _extract_html_body(html) == ""


class TestMergeResults:
    def test_empty_list(self):
        result = _merge_results([])
        assert result.page_count == 0
        assert result.content_markdown == ""
        assert result.pages == []
        assert result.document_json is None

    def test_single_result_passthrough(self):
        r = ConversionResult(
            page_count=3,
            content_markdown="# Page 1",
            content_html="<html><body><p>Page 1</p></body></html>",
            pages=[PageDetail(page_number=1, width=612, height=792)],
            document_json='{"pages": {}}',
        )
        merged = _merge_results([r])
        assert merged.page_count == 3
        assert merged.content_markdown == "# Page 1"
        assert merged.pages == [PageDetail(page_number=1, width=612, height=792)]
        assert merged.document_json is None  # intentionally dropped

    def test_merges_multiple_results(self):
        r1 = ConversionResult(
            page_count=2,
            content_markdown="# Batch 1",
            content_html="<html><body><p>B1</p></body></html>",
            pages=[
                PageDetail(page_number=1, width=612, height=792),
                PageDetail(page_number=2, width=612, height=792),
            ],
            skipped_items=1,
        )
        r2 = ConversionResult(
            page_count=2,
            content_markdown="# Batch 2",
            content_html="<html><body><p>B2</p></body></html>",
            pages=[
                PageDetail(page_number=3, width=612, height=792),
                PageDetail(page_number=4, width=612, height=792),
            ],
            skipped_items=2,
        )
        merged = _merge_results([r1, r2])
        assert merged.page_count == 4
        assert merged.content_markdown == "# Batch 1\n\n# Batch 2"
        assert len(merged.pages) == 4
        assert merged.pages[0].page_number == 1
        assert merged.pages[3].page_number == 4
        assert merged.skipped_items == 3
        assert merged.document_json is None
        assert "<p>B1</p>" in merged.content_html
        assert "<p>B2</p>" in merged.content_html
        # Valid HTML structure
        assert merged.content_html.startswith("<!DOCTYPE html>")
        assert "</body></html>" in merged.content_html


# ---------------------------------------------------------------------------
# Batched conversion integration tests
# ---------------------------------------------------------------------------


class TestBatchedConversion:
    @pytest.mark.asyncio
    async def test_batched_conversion_produces_merged_result(self):
        """When batch_page_size is set and document exceeds it, results are merged."""
        converter = AsyncMock()

        # Simulate 2 batches: pages 1-5 and 6-8
        converter.convert.side_effect = [
            ConversionResult(
                page_count=5,
                content_markdown="# Batch 1",
                content_html="<html><body><p>B1</p></body></html>",
                pages=[PageDetail(page_number=i, width=612, height=792) for i in range(1, 6)],
            ),
            ConversionResult(
                page_count=3,
                content_markdown="# Batch 2",
                content_html="<html><body><p>B2</p></body></html>",
                pages=[PageDetail(page_number=i, width=612, height=792) for i in range(6, 9)],
            ),
        ]

        service = AnalysisService(converter=converter, conversion_timeout=60)

        with patch("services.analysis_service.analysis_repo") as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=MagicMock())
            mock_repo.update_progress = AsyncMock()

            result = await service._run_batched_conversion(
                "job-1",
                "/fake.pdf",
                MagicMock(),
                total_pages=8,
                batch_size=5,
            )

        assert result is not None
        assert result.page_count == 8
        assert len(result.pages) == 8
        assert result.document_json is None
        assert converter.convert.call_count == 2

        # Verify page_range was passed correctly
        call1_kwargs = converter.convert.call_args_list[0].kwargs
        call2_kwargs = converter.convert.call_args_list[1].kwargs
        assert call1_kwargs["page_range"] == (1, 5)
        assert call2_kwargs["page_range"] == (6, 8)

    @pytest.mark.asyncio
    async def test_batch_failure_raises_with_enriched_message(self):
        """If a batch fails, RuntimeError is raised with batch info."""
        converter = AsyncMock()
        converter.convert.side_effect = [
            ConversionResult(
                page_count=5,
                content_markdown="ok",
                content_html="<html><body>ok</body></html>",
                pages=[PageDetail(page_number=i, width=612, height=792) for i in range(1, 6)],
            ),
            RuntimeError("OOM"),
        ]

        service = AnalysisService(converter=converter, conversion_timeout=60)

        with patch("services.analysis_service.analysis_repo") as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=MagicMock())
            mock_repo.update_progress = AsyncMock()

            with pytest.raises(RuntimeError, match=r"Batch 2/2 \(pages 6-8\) failed: OOM"):
                await service._run_batched_conversion(
                    "job-fail",
                    "/fake.pdf",
                    MagicMock(),
                    total_pages=8,
                    batch_size=5,
                )

    @pytest.mark.asyncio
    async def test_job_deleted_mid_batch_returns_none(self):
        """If the job is deleted between batches, conversion aborts with None."""
        converter = AsyncMock()
        converter.convert.return_value = ConversionResult(
            page_count=5,
            content_markdown="ok",
            content_html="<html><body>ok</body></html>",
            pages=[PageDetail(page_number=i, width=612, height=792) for i in range(1, 6)],
        )

        service = AnalysisService(converter=converter, conversion_timeout=60)

        # First check returns job, second returns None (deleted)
        with patch("services.analysis_service.analysis_repo") as mock_repo:
            mock_repo.find_by_id = AsyncMock(side_effect=[MagicMock(), None])
            mock_repo.update_progress = AsyncMock()

            result = await service._run_batched_conversion(
                "job-del",
                "/fake.pdf",
                MagicMock(),
                total_pages=10,
                batch_size=5,
            )

        assert result is None
        # Only first batch should have been converted
        assert converter.convert.call_count == 1
