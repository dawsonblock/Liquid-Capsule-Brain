#!/usr/bin/env python3
import os
import re
import sys
import time
from typing import Dict, List, Tuple

import httpx


BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:8000")


MetricRecord = Tuple[Dict[str, str], float]
MetricCollection = Dict[str, List[MetricRecord]]


def scrape_metrics(client: httpx.Client) -> MetricCollection:
    response = client.get(f"{BASE}/metrics")
    response.raise_for_status()
    metrics: MetricCollection = {}
    for line in response.text.splitlines():
        if line.startswith("#"):
            continue

        label_match = re.match(
            r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([0-9.eE+-]+)$", line.strip()
        )
        if label_match:
            name, labels_str, value = label_match.groups()
            labels: Dict[str, str] = {}
            for part in labels_str.split(","):
                key, val = part.split("=")
                labels[key.strip()] = val.strip().strip('"')
            metrics.setdefault(name, []).append((labels, float(value)))
            continue

        fallback_match = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([0-9.eE+-]+)$", line.strip())
        if fallback_match:
            name, value = fallback_match.groups()
            metrics.setdefault(name, []).append(({}, float(value)))

    return metrics


def counter_for(metrics: MetricCollection, name: str, labels: Dict[str, str]) -> float:
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

        assert (
            health_after >= health_before + 1
        ), f"/healthz counter did not increase (before={health_before}, after={health_after})"
        assert (
            summary_after >= summary_before + 1
        ), f"/state/summary counter did not increase (before={summary_before}, after={summary_after})"

        print("[OK] Smoke run successful. Metrics counters increased as expected.")
        sys.exit(0)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        sys.exit(2)
    finally:
        client.close()


if __name__ == "__main__":
    main()
