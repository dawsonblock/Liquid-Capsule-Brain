#!/usr/bin/env python3
"""Simple smoke test for the Capsule Brain HTTP API."""

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
        if line.startswith("#"):
            continue
        match = re.match(
            r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([0-9.eE+-]+)$", line.strip()
        )
        if match:
            name, labels_str, value = match.groups()
            labels: dict[str, str] = {}
            for part in labels_str.split(","):
                key, raw_value = part.split("=")
                labels[key.strip()] = raw_value.strip().strip('"')
            metrics.setdefault(name, []).append((labels, float(value)))
            continue
        match = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([0-9.eE+-]+)$", line.strip())
        if match:
            name, value = match.groups()
            metrics.setdefault(name, []).append(({}, float(value)))
    return metrics


def counter_for(
    metrics: dict[str, list[tuple[dict[str, str], float]]],
    name: str,
    labels: dict[str, str],
) -> float:
    total = 0.0
    for metric_labels, value in metrics.get(name, []):
        if all(metric_labels.get(key) == val for key, val in labels.items()):
            total += value
    return total


def main() -> None:
    client = httpx.Client(timeout=10.0)
    try:
        before = scrape_metrics(client)

        endpoints = ["/healthz", "/ready", "/state/summary"]
        for endpoint in endpoints:
            response = client.get(f"{BASE}{endpoint}")
            response.raise_for_status()

        response = client.post(
            f"{BASE}/graph/edge", params={"source": "S", "target": "T", "relation": "related_to"}
        )
        response.raise_for_status()

        time.sleep(0.5)
        after = scrape_metrics(client)

        health_before = counter_for(
            before, "cb_http_requests_total", {"method": "GET", "path": "/healthz", "status": "200"}
        )
        health_after = counter_for(
            after, "cb_http_requests_total", {"method": "GET", "path": "/healthz", "status": "200"}
        )
        summary_before = counter_for(
            before,
            "cb_http_requests_total",
            {"method": "GET", "path": "/state/summary", "status": "200"},
        )
        summary_after = counter_for(
            after,
            "cb_http_requests_total",
            {"method": "GET", "path": "/state/summary", "status": "200"},
        )

        assert health_after >= health_before + 1, (
            f"/healthz counter did not increase (before={health_before}, after={health_after})"
        )
        assert summary_after >= summary_before + 1, (
            f"/state/summary counter did not increase (before={summary_before}, after={summary_after})"
        )

        print("[OK] Smoke run successful. Metrics counters increased as expected.")
        sys.exit(0)
    except Exception as exc:  # pragma: no cover - CLI utility
        print(f"[FAIL] {exc}")
        sys.exit(2)
    finally:
        client.close()


if __name__ == "__main__":
    main()
