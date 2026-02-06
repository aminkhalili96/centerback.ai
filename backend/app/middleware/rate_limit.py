"""Simple per-IP in-memory rate limiting middleware."""

from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request

from app.config import settings

_lock = threading.Lock()
_buckets: dict[str, tuple[int, int]] = {}


def enforce_rate_limit(request: Request) -> None:
    """Reject requests above configured rate threshold."""
    path = request.url.path
    if path in {"/health", "/metrics"}:
        return

    client = request.client.host if request.client else "unknown"
    now = int(time.time())
    window = now // 60
    limit = settings.rate_limit_per_minute

    with _lock:
        existing = _buckets.get(client)
        if existing is None or existing[0] != window:
            _buckets[client] = (window, 1)
            return

        count = existing[1] + 1
        _buckets[client] = (window, count)

    if count > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

