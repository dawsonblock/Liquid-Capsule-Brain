from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from capsule_brain.api.server import app


ADMIN_HEADERS = {"x-admin-token": "test-admin-token"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN_HEADERS["x-admin-token"])
    monkeypatch.setenv("APP_ENV", "test")


def test_health_and_ready() -> None:
    with TestClient(app) as client:
        r = client.get("/healthz", headers=ADMIN_HEADERS)
        assert r.status_code == 200 and r.json()["ok"] is True
        r = client.get("/ready", headers=ADMIN_HEADERS)
        assert r.status_code == 200 and r.json()["ready"] is True


def test_state_and_graph() -> None:
    with TestClient(app) as client:
        r = client.get("/state/summary", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        js = r.json()
        assert "self_awareness_metrics" in js and "graph" in js

        r = client.post(
            "/graph/edge",
            params={"source": "A", "target": "B", "relation": "related_to"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 200
        g = r.json()["graph"]
        assert g["nodes"] >= 2 and g["edges"] >= 1


def test_metrics() -> None:
    with TestClient(app) as client:
        # hit a couple endpoints first
        client.get("/healthz", headers=ADMIN_HEADERS)
        client.get("/ready", headers=ADMIN_HEADERS)
        # scrape metrics
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.text
        assert "cb_http_requests_total" in text
        assert "cb_request_latency_seconds_bucket" in text


def test_protected_endpoints_require_admin_header() -> None:
    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 403

        r = client.get("/healthz", headers={"x-admin-token": "wrong"})
        assert r.status_code == 403

        r = client.get("/healthz", headers=ADMIN_HEADERS)
        assert r.status_code == 200
