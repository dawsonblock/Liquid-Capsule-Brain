"""Smoke tests for the FastAPI surface."""

from __future__ import annotations

from fastapi.testclient import TestClient

from capsule_brain.api.server import app


def test_health_and_ready() -> None:
    with TestClient(app) as client:
        health_response = client.get("/healthz")
        assert health_response.status_code == 200
        assert health_response.json()["ok"] is True

        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["ready"] is True


def test_state_and_graph() -> None:
    with TestClient(app) as client:
        state_response = client.get("/state/summary")
        assert state_response.status_code == 200
        summary = state_response.json()
        assert "self_awareness_metrics" in summary
        assert "graph" in summary

        graph_response = client.post(
            "/graph/edge",
            params={"source": "A", "target": "B", "relation": "related_to"},
        )
        assert graph_response.status_code == 200
        graph = graph_response.json()["graph"]
        assert graph["nodes"] >= 2
        assert graph["edges"] >= 1


def test_metrics() -> None:
    with TestClient(app) as client:
        client.get("/healthz")
        client.get("/ready")

        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        metrics_payload = metrics_response.text
        assert "cb_http_requests_total" in metrics_payload
        assert "cb_request_latency_seconds_bucket" in metrics_payload
