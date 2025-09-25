"""Prometheus metrics integration using prometheus-fastapi-instrumentator."""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

_instrumentator = Instrumentator(should_instrument_requests_inprogress=True)
_configured_apps: set[int] = set()

# LLM token usage metrics (provider/model scoped)
_tokens_total = Counter(
    "cb_tokens_total",
    "Total tokens used by LLM calls (labeled by provider/model/type)",
    labelnames=("provider", "model", "type"),
)

_tokens_per_prompt = Histogram(
    "cb_tokens_per_prompt",
    "Tokens per prompt/completion for LLM calls",
    labelnames=("provider", "model", "type"),
    buckets=(1, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192),
)

# Custom application metrics
_ask_requests_total = Counter(
    "cb_ask_requests_total",
    "Total number of ask requests",
    labelnames=("status", "error_type"),
)

_ask_request_duration = Histogram(
    "cb_ask_request_duration_seconds",
    "Duration of ask requests",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

_file_uploads_total = Counter(
    "cb_file_uploads_total",
    "Total number of file uploads",
    labelnames=("file_type", "status"),
)

_active_connections = Gauge(
    "cb_active_connections",
    "Number of active WebSocket connections",
)

_memory_usage_bytes = Gauge(
    "cb_memory_usage_bytes",
    "Current memory usage in bytes",
)


def setup_metrics(app: FastAPI) -> None:
    """Attach Prometheus instrumentation and expose `/metrics` once per app."""

    app_id = id(app)
    if app_id in _configured_apps:
        return

    _instrumentator.instrument(app).expose(app, include_in_schema=False)
    _configured_apps.add(app_id)


def record_llm_tokens(
    provider: str,
    model: str,
    *,
    prompt_tokens: int | float = 0,
    completion_tokens: int | float = 0,
) -> None:
    """Record token usage and per-prompt histograms for an LLM call.

    Provider examples: "deepseek", "openai". Model examples: "deepseek-chat".
    """

    try:
        p = float(prompt_tokens or 0)
        c = float(completion_tokens or 0)
    except Exception:
        p = 0.0
        c = 0.0

    # Counters
    if p:
        _tokens_total.labels(provider, model, "prompt").inc(p)
    if c:
        _tokens_total.labels(provider, model, "completion").inc(c)
    total = p + c
    if total:
        _tokens_total.labels(provider, model, "total").inc(total)

    # Histograms (observe distribution per request)
    if p:
        _tokens_per_prompt.labels(provider, model, "prompt").observe(p)
    if c:
        _tokens_per_prompt.labels(provider, model, "completion").observe(c)


def record_ask_request(status: str, error_type: str = "none") -> None:
    """Record an ask request."""
    _ask_requests_total.labels(status=status, error_type=error_type).inc()


def record_ask_duration(duration_seconds: float) -> None:
    """Record ask request duration."""
    _ask_request_duration.observe(duration_seconds)


def record_file_upload(file_type: str, status: str) -> None:
    """Record a file upload."""
    _file_uploads_total.labels(file_type=file_type, status=status).inc()


def set_active_connections(count: int) -> None:
    """Set the number of active WebSocket connections."""
    _active_connections.set(count)


def set_memory_usage(bytes_used: int) -> None:
    """Set current memory usage."""
    _memory_usage_bytes.set(bytes_used)
