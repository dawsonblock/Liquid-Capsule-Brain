#!/usr/bin/env python3
"""Simple smoke test against a running Capsule Brain instance."""
from __future__ import annotations

import os
import re
import sys
import time

import httpx

BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:8000")


def scrape_metrics(client: httpx.Client) -> dict[str, list[tuple[dict[str, str], float]]]:
    response = client.get(f"{BASE}/metrics", timeout=5.0)
    response.raise_for_status()
    metrics: dict[str, list[tuple[dict[str, str], float]]] = {}
    for line in response.text.splitlines():
        if line.startswith("#"):
            continue
        match = re.match(r"(\w+)(\{.*\})?\s+(\d+(?:\.\d+)?)", line)
        if not match:
            continue
        name, labels_raw, value = match.groups()
        labels: dict[str, str] = {}
        if labels_raw:
            pairs = re.findall(r"(\w+)=\"([^\"]+)\"", labels_raw)
            labels = {key: val for key, val in pairs}
        metrics.setdefault(name, []).append((labels, float(value)))
    return metrics


def require_metric_sum(metrics: dict[str, list[tuple[dict[str, str], float]]], name: str, labels: dict[str, str]) -> float:
    total = 0.0
    for metric_labels, value in metrics.get(name, []):
        if all(metric_labels.get(key) == expected for key, expected in labels.items()):
            total += value
    if total == 0.0:
        raise RuntimeError(f"Missing metric {name} with labels {labels}")
    return total


def main() -> int:
    with httpx.Client() as client:
        print("Checking health endpoint...")
        health = client.get(f"{BASE}/healthz", timeout=5.0)
        health.raise_for_status()
        print("✅ /healthz responded")

        print("Checking readiness...")
        ready = client.get(f"{BASE}/ready", timeout=5.0)
        ready.raise_for_status()
        print("✅ /ready responded")

        print("Scraping metrics...")
        metrics = scrape_metrics(client)
        require_metric_sum(metrics, "cb_http_requests_total", {"path": "/healthz", "status": "200"})
        print("✅ Metrics look sane")

        print("Performing /ask round-trip...")
        payload = {"q": "Summarize the state of the system."}
        response = client.post(f"{BASE}/ask", json=payload, timeout=10.0)
        response.raise_for_status()
        print("✅ /ask request succeeded")

        print("Waiting briefly for background tasks...")
        time.sleep(1.0)
        return 0


if __name__ == "__main__":
    sys.exit(main())
