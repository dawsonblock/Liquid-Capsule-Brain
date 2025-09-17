#!/usr/bin/env python3
"""Simple smoke test that validates key Capsule Brain HTTP endpoints."""

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

        match_with_labels = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([0-9.eE+-]+)$", stripped)
        if match_with_labels:
            name, labels_str, value = match_with_labels.groups()
            labels: dict[str, str] = {}
            for part in labels_str.split(","):
                key, raw_value = part.split("=")
                labels[key.strip()] = raw_value.strip().strip('"')
            metrics.setdefault(name, []).append((labels, float(value)))
            continue

        match_without_labels = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([0-9.eE+-]+)$", stripped)
        if match_without_labels:
            name, value = match_without_labels.groups()
            metrics.setdefault(name, []).append(({}, float(value)))

    return metrics


def counter_for(metrics: dict[str, list[tuple[dict[str, str], float]]], name: str, labels: dict[str, str]) -> float:
    total = 0.0
    for metric_labels, value in metrics.get(name, []):
        if all(metric_labels.get(key) == expected for key, expected in labels.items()):
            total += value
    return total


def main() -> None:
    client = httpx.Client(timeout=10.0)
    try:
        before = scrape_metrics(client)

        for endpoint in ["/healthz", "/ready", "/state/summary"]:
            response = client.get(f"{BASE}{endpoint}")
            response.raise_for_status()

        post_response = client.post(
            f"{BASE}/graph/edge",
            params={"source": "S", "target": "T", "relation": "related_to"},
        )
        post_response.raise_for_status()

        time.sleep(0.5)
        after = scrape_metrics(client)

        health_labels = {"method": "GET", "path": "/healthz", "status": "200"}
        state_labels = {"method": "GET", "path": "/state/summary", "status": "200"}

        health_before = counter_for(before, "cb_http_requests_total", health_labels)
        health_after = counter_for(after, "cb_http_requests_total", health_labels)
        state_before = counter_for(before, "cb_http_requests_total", state_labels)
        state_after = counter_for(after, "cb_http_requests_total", state_labels)

        if health_after < health_before + 1:
            raise RuntimeError(
                f"/healthz counter did not increase (before={health_before}, after={health_after})"
            )

        if state_after < state_before + 1:
            raise RuntimeError(
                "/state/summary counter did not increase "
                f"(before={state_before}, after={state_after})"
            )

        print("[OK] Smoke run successful. Metrics counters increased as expected.")
    except Exception as exc:  # pragma: no cover - CLI feedback
        print(f"[FAIL] {exc}")
        sys.exit(2)
    else:
        sys.exit(0)
    finally:
        client.close()


if __name__ == "__main__":
    main()
