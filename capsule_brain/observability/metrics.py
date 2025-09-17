from __future__ import annotations

import re
from time import time
from typing import Awaitable, Callable, MutableMapping, Any

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.types import Receive, Scope, Send

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


class MetricsMiddleware:
    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        start = time()
        status_code_container = {"code": "500"}

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
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
