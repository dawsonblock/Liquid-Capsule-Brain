"""Prometheus metrics instrumentation for the Capsule Brain API."""

from __future__ import annotations

import re
import time

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

registry = CollectorRegistry()
REQUEST_COUNT = Counter(
    "cb_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)
REQUEST_LATENCY = Histogram(
    "cb_request_latency_seconds",
    "Request latency (seconds)",
    ["method", "path"],
    registry=registry,
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)
TOKENS_USED = Counter(
    "cb_tokens_total",
    "Total LLM tokens consumed",
    ["model"],
    registry=registry,
)

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path = request.url.path

        start = time.perf_counter()
        response = await call_next(request)

        elapsed = time.perf_counter() - start
        norm_path = re.sub(r"/\d+", "/{id}", path)
        REQUEST_LATENCY.labels(method, norm_path).observe(elapsed)
        REQUEST_COUNT.labels(method, norm_path, str(response.status_code)).inc()

        return response
