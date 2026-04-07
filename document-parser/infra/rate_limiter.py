"""Lightweight in-memory rate limiter middleware for FastAPI.

Uses a sliding-window counter per client IP. No external dependency
required — suitable for single-process deployments with SQLite.

For multi-process or distributed setups, replace with a Redis-backed
solution (e.g. slowapi).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)


@dataclass
class _ClientBucket:
    """Sliding window of request timestamps for a single client."""

    timestamps: list[float] = field(default_factory=list)

    def count_recent(self, window: float, now: float) -> int:
        """Remove expired entries and return the count of recent requests."""
        cutoff = now - window
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        return len(self.timestamps)

    def add(self, now: float) -> None:
        self.timestamps.append(now)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiter using in-memory sliding windows.

    Args:
        app: The ASGI application.
        requests_per_window: Max requests allowed per window.
        window_seconds: Size of the sliding window in seconds.
        exclude_paths: Paths exempt from rate limiting (e.g. health checks).
    """

    def __init__(
        self,
        app,
        *,
        requests_per_window: int = 60,
        window_seconds: float = 60.0,
        exclude_paths: tuple[str, ...] = ("/api/health",),
    ):
        super().__init__(app)
        self._max_requests = requests_per_window
        self._window = window_seconds
        self._exclude = exclude_paths
        self._buckets: dict[str, _ClientBucket] = defaultdict(_ClientBucket)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self._exclude:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        bucket = self._buckets[client_ip]
        recent = bucket.count_recent(self._window, now)

        if recent >= self._max_requests:
            retry_after = int(self._window)
            logger.warning(
                "Rate limit exceeded for %s (%d/%d)", client_ip, recent, self._max_requests
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )

        bucket.add(now)
        return await call_next(request)
