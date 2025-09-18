"""Prometheus metrics integration using prometheus-fastapi-instrumentator."""

from __future__ import annotations

from typing import Set

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

_instrumentator = Instrumentator(should_instrument_requests_inprogress=True)
_configured_apps: Set[int] = set()


def setup_metrics(app: FastAPI) -> None:
    """Attach Prometheus instrumentation and expose `/metrics` once per app."""

    app_id = id(app)
    if app_id in _configured_apps:
        return

    _instrumentator.instrument(app).expose(app, include_in_schema=False)
    _configured_apps.add(app_id)

