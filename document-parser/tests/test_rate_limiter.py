"""Tests for the in-memory rate limiter middleware."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.rate_limiter import RateLimiterMiddleware, _ClientBucket


class TestClientBucket:
    def test_count_recent_filters_old_entries(self):
        bucket = _ClientBucket(timestamps=[1.0, 2.0, 3.0, 10.0])
        count = bucket.count_recent(window=5.0, now=12.0)
        assert count == 1  # only 10.0 is within [7.0, 12.0]

    def test_count_recent_keeps_all_when_within_window(self):
        bucket = _ClientBucket(timestamps=[10.0, 11.0, 12.0])
        count = bucket.count_recent(window=60.0, now=15.0)
        assert count == 3

    def test_add(self):
        bucket = _ClientBucket()
        bucket.add(1.0)
        bucket.add(2.0)
        assert len(bucket.timestamps) == 2


@pytest.fixture
def limited_app():
    """FastAPI app with a very low rate limit for testing."""
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        requests_per_window=3,
        window_seconds=60,
        exclude_paths=("/health",),
    )

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(limited_app):
    return TestClient(limited_app)


class TestRateLimiterMiddleware:
    def test_allows_requests_under_limit(self, client):
        for _ in range(3):
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_blocks_requests_over_limit(self, client):
        for _ in range(3):
            client.get("/test")

        resp = client.get("/test")
        assert resp.status_code == 429
        assert resp.json()["detail"] == "Too many requests"
        assert "Retry-After" in resp.headers

    def test_health_excluded_from_limit(self, client):
        # Exhaust the limit
        for _ in range(3):
            client.get("/test")

        # Health should still work
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_window_resets(self, client):
        """After the window expires, requests should be allowed again."""
        for _ in range(3):
            client.get("/test")

        assert client.get("/test").status_code == 429

        # Simulate time passing beyond the window
        with patch("time.monotonic", return_value=1e12):
            resp = client.get("/test")
            assert resp.status_code == 200
