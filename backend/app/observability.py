"""Metrics and request instrumentation."""

from __future__ import annotations

import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "centerback_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "centerback_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


async def metrics_middleware(request: Request, call_next):
    """Collect request-level Prometheus metrics."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)
    return response


def metrics_response() -> Response:
    """Expose metrics in Prometheus text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

