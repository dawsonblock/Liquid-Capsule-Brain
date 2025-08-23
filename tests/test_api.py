from fastapi.testclient import TestClient

from capsule_brain.api.server import app


def test_health_and_ready():
    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200 and r.json()["ok"] is True
        r = client.get("/ready")
        assert r.status_code == 200 and r.json()["ready"] is True


def test_state_and_graph():
    with TestClient(app) as client:
        r = client.get("/state/summary")
        assert r.status_code == 200
        js = r.json()
        assert "self_awareness_metrics" in js and "graph" in js

        r = client.post(
            "/graph/edge", params={"source": "A", "target": "B", "relation": "related_to"}
        )
        assert r.status_code == 200
        g = r.json()["graph"]
        assert g["nodes"] >= 2 and g["edges"] >= 1


def test_metrics():
    with TestClient(app) as client:
        # hit a couple endpoints first
        client.get("/healthz")
        client.get("/ready")
        # scrape metrics
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.text
        assert "cb_http_requests_total" in text
        assert "cb_request_latency_seconds_bucket" in text
