from typing import Any, cast

from fastapi.testclient import TestClient

import capsule_brain.api.server as server
from capsule_brain.core.capsule_engine import CapsuleEngine


def test_health_and_ready() -> None:
    with TestClient(server.app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200 and r.json()["ok"] is True
        r = client.get("/ready")
        assert r.status_code == 200 and r.json()["ready"] is True

def test_state_and_graph() -> None:
    with TestClient(server.app) as client:
        r = client.get("/state/summary")
        assert r.status_code == 200
        js = r.json()
        assert "self_awareness_metrics" in js and "graph" in js

        r = client.post("/graph/edge", params={"source": "A", "target": "B", "relation": "related_to"})
        assert r.status_code == 200
        g = r.json()["graph"]
        assert g["nodes"] >= 2 and g["edges"] >= 1

def test_metrics() -> None:
    with TestClient(server.app) as client:
        # hit a couple endpoints first
        client.get("/healthz")
        client.get("/ready")
        # scrape metrics
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.text
        assert "cb_http_requests_total" in text
        assert "cb_request_latency_seconds_bucket" in text


def test_ask_accepts_multiple_payloads() -> None:
    with TestClient(server.app) as client:
        ready = client.get("/ready")
        assert ready.status_code == 200
        assert server.engine is not None
        current_engine = cast(CapsuleEngine, server.engine)

        def _post_and_check(payload: dict[str, Any], expected: str) -> None:
            before = len(current_engine.memory)
            response = client.post("/ask", **payload)
            assert response.status_code == 200
            body = response.json()
            assert body["ack"] is True
            assert len(current_engine.memory) == before + 1
            assert current_engine.memory[-1]["content"] == expected

        _post_and_check({"json": {"q": "json alias"}}, "json alias")
        _post_and_check({"json": {"question": "json question"}}, "json question")
        _post_and_check({"params": {"q": "query question"}}, "query question")

        missing = client.post("/ask")
        assert missing.status_code == 422
