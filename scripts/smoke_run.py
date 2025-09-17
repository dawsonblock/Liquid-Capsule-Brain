#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import time

import httpx

BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:8000")


def scrape_metrics(client: httpx.Client) -> dict[str, list[tuple[dict[str, str], float]]]:
    response = client.get(f"{BASE}/metrics")
    response.raise_for_status()
    metrics: dict[str, list[tuple[dict[str, str], float]]] = {}
    for line in response.text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        labeled_match = re.match(r"^([\w:]+)\{([^}]*)\}\s+([0-9.eE+-]+)$", stripped)
        if labeled_match:
            name, labels_str, value_str = labeled_match.groups()
            labels: dict[str, str] = {}
            for part in labels_str.split(","):
                key, val = part.split("=")
                labels[key.strip()] = val.strip().strip('"')
            metrics.setdefault(name, []).append((labels, float(value_str)))
            continue

        simple_match = re.match(r"^([\w:]+)\s+([0-9.eE+-]+)$", stripped)
        if simple_match:
            name, value_str = simple_match.groups()
            metrics.setdefault(name, []).append(({}, float(value_str)))
    return metrics


def counter_for(metrics: dict[str, list[tuple[dict[str, str], float]]], name: str, labels: dict[str, str]) -> float:
    total = 0.0
    for entry_labels, value in metrics.get(name, []):
        if all(entry_labels.get(key) == val for key, val in labels.items()):
            total += value
    return total


def main() -> None:
    client = httpx.Client(timeout=10.0)
    try:
        before = scrape_metrics(client)

        endpoints = ["/healthz", "/ready", "/state/summary"]
        for endpoint in endpoints:
            response = client.get(f"{BASE}{endpoint}")
            assert response.status_code == 200, f"{endpoint} failed: {response.status_code}"

        response = client.post(
            f"{BASE}/graph/edge",
            params={"source": "S", "target": "T", "relation": "related_to"},
        )
        assert response.status_code == 200, f"/graph/edge failed: {response.status_code}"

        time.sleep(0.5)
        after = scrape_metrics(client)

        health_before = counter_for(
            before,
            "cb_http_requests_total",
            {"method": "GET", "path": "/healthz", "status": "200"},
        )
        health_after = counter_for(
            after,
            "cb_http_requests_total",
            {"method": "GET", "path": "/healthz", "status": "200"},
        )
        state_before = counter_for(
            before,
            "cb_http_requests_total",
            {"method": "GET", "path": "/state/summary", "status": "200"},
        )
        state_after = counter_for(
            after,
            "cb_http_requests_total",
            {"method": "GET", "path": "/state/summary", "status": "200"},
        )

        assert health_after >= health_before + 1, (
            f"/healthz counter did not increase (before={health_before}, after={health_after})"
        )
        assert state_after >= state_before + 1, (
            f"/state/summary counter did not increase (before={state_before}, after={state_after})"
        )

        print("[OK] Smoke run successful. Metrics counters increased as expected.")
        sys.exit(0)
    except Exception as exc:  # pragma: no cover - best effort script
        print(f"[FAIL] {exc}")
        sys.exit(2)
    finally:
        client.close()


if __name__ == "__main__":
    main()
