from __future__ import annotations

from fastapi.testclient import TestClient

from capsule_brain.api.server import app


def test_health_and_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200 and response.json()["ok"] is True
        response = client.get("/ready")
        assert response.status_code == 200 and response.json()["ready"] is True


def test_state_and_graph() -> None:
    with TestClient(app) as client:
        response = client.get("/state/summary")
        assert response.status_code == 200
        payload = response.json()
        assert "self_awareness_metrics" in payload and "graph" in payload

        response = client.post(
            "/graph/edge", params={"source": "A", "target": "B", "relation": "related_to"}
        )
        assert response.status_code == 200
        graph = response.json()["graph"]
        assert graph["nodes"] >= 2 and graph["edges"] >= 1


def test_metrics() -> None:
    with TestClient(app) as client:
        client.get("/healthz")
        client.get("/ready")
        response = client.get("/metrics")
        assert response.status_code == 200
        text = response.text
        assert "cb_http_requests_total" in text
        assert "cb_request_latency_seconds_bucket" in text
