"""Tests for AnalysisService — focus on _on_task_done callback (bug #1 fix)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.analysis_service import _on_task_done


class TestOnTaskDone:
    """Bug #1: _on_task_done must call _mark_failed when the task raises."""

    @pytest.mark.asyncio
    async def test_exception_marks_job_failed(self):
        """When a background task raises, the job should be marked FAILED."""
        job_id = "job-123"

        # Create a task that raises
        async def failing_task():
            raise RuntimeError("boom")

        task = asyncio.create_task(failing_task())
        await asyncio.sleep(0)  # let the task fail

        with patch("services.analysis_service._mark_failed", new_callable=AsyncMock) as mock_mark:
            _on_task_done(task, job_id=job_id)
            # ensure_future schedules it; give the event loop a tick
            await asyncio.sleep(0)

        mock_mark.assert_called_once_with(job_id, "boom")

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
