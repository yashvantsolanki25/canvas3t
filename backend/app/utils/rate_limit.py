from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from flask import Flask, abort, current_app, request


class SimpleLimiter:
    """Naive in-memory rate limiter (best-effort, single-process)."""

    def __init__(self) -> None:
        self._buckets: dict[str, Deque[float]] = defaultdict(deque)
        self._limit = 200
        self._window = 60

    def init_app(self, app: Flask) -> None:
        limit = app.config.get("RATE_LIMIT", "50/minute")
        try:
            amount, per = limit.split("/")
            self._limit = int(amount)
            self._window = 60 if per.startswith("minute") else 1
        except Exception:  # pragma: no cover - fallback
            app.logger.warning("Invalid RATE_LIMIT config, using defaults")

        @app.before_request
        def _enforce():
            if not app.config.get("ENABLE_RATE_LIMITS", True):
                return
            # Skip rate limiting for health checks and static paths
            if request.path in ("/api/health", "/health", "/"):
                return
            key = request.remote_addr or "anonymous"
            bucket = self._buckets[key]
            now = time.time()

            while bucket and now - bucket[0] > self._window:
                bucket.popleft()

            if len(bucket) >= self._limit:
                abort(429, description="Too many requests")
            bucket.append(now)


limiter = SimpleLimiter()

