#!/usr/bin/env python3
import os
import re
import sys
import time

import httpx

BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:8000")


def scrape_metrics(client: httpx.Client) -> dict[str, list[tuple[dict[str, str], float]]]:
    r = client.get(f"{BASE}/metrics")
    r.raise_for_status()
    metrics: dict[str, list[tuple[dict[str, str], float]]] = {}
    for line in r.text.splitlines():
        if line.startswith("#"):
            continue
        # e.g., cb_http_requests_total{method="GET",path="/healthz",status="200"} 3.0
        m = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([0-9.eE+-]+)$', line.strip())
        if m:
            name, labels_str, val = m.groups()
            labels = {}
            for part in labels_str.split(","):
                k, v = part.split("=")
                labels[k.strip()] = v.strip().strip('"')
            metrics.setdefault(name, []).append((labels, float(val)))
        else:
            # handle _count and _sum without labels
            m2 = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([0-9.eE+-]+)$', line.strip())
            if m2:
                name, val = m2.groups()
                metrics.setdefault(name, []).append(({}, float(val)))
    return metrics


def counter_for(
    metrics: dict[str, list[tuple[dict[str, str], float]]],
    name: str,
    labels: dict[str, str],
) -> float:
    total = 0.0
    for lbs, val in metrics.get(name, []):
        ok = all(lbs.get(k) == v for k, v in labels.items())
        if ok:
            total += val
    return total


def main() -> None:
    client = httpx.Client(timeout=10.0)
    try:
        # Warm up + baseline metrics
        before = scrape_metrics(client)

        endpoints = ["/healthz", "/ready", "/state/summary"]
        for ep in endpoints:
            r = client.get(f"{BASE}{ep}")
            assert r.status_code == 200, f"{ep} failed: {r.status_code}"

        # Exercise POST
        r = client.post(f"{BASE}/graph/edge", params={"source":"S", "target":"T", "relation":"related_to"})
        assert r.status_code == 200, f"/graph/edge failed: {r.status_code}"

        # Scrape after
        time.sleep(0.5)
        after = scrape_metrics(client)

        # Validate counters increased for GET /healthz and /state/summary
        h_before = counter_for(before, "cb_http_requests_total", {"method":"GET","path":"/healthz","status":"200"})
        h_after  = counter_for(after,  "cb_http_requests_total", {"method":"GET","path":"/healthz","status":"200"})
        s_before = counter_for(before, "cb_http_requests_total", {"method":"GET","path":"/state/summary","status":"200"})
        s_after  = counter_for(after,  "cb_http_requests_total", {"method":"GET","path":"/state/summary","status":"200"})

        assert h_after >= h_before + 1, f"/healthz counter did not increase (before={h_before}, after={h_after})"
        assert s_after >= s_before + 1, f"/state/summary counter did not increase (before={s_before}, after={s_after})"

        print("[OK] Smoke run successful. Metrics counters increased as expected.")
        sys.exit(0)
    except Exception as e:
        print(f"[FAIL] {e}")
        sys.exit(2)
    finally:
        client.close()

if __name__ == "__main__":
    main()
