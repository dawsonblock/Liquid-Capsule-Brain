
"""Prometheus metrics instrumentation for Capsule Brain."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from time import time
from typing import Any, Protocol

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

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


class ASGIApp(Protocol):
    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        ...


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        start = time()
        status_code_container = {"code": "500"}

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                status_code_container["code"] = str(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time() - start
            norm_path = re.sub(r"/\d+", "/{id}", path)
            REQUEST_LATENCY.labels(method, norm_path).observe(elapsed)
            REQUEST_COUNT.labels(method, norm_path, status_code_container["code"]).inc()
