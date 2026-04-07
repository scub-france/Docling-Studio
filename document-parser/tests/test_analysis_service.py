"""Tests for AnalysisService — callbacks, concurrency, and orchestration."""

from __future__ import annotations

import asyncio
import functools
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.analysis_service import AnalysisService, _on_task_done


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
