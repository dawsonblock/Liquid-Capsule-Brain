# Monitoring & Observability

## Prometheus
- Scrapes `/metrics` on port 8000
- Default job: `capsule_brain`

## Grafana
- Preconfigured to use Prometheus at `http://prometheus:9090`
- Suggested panels:
  - Request rate/latency (p50, p95, p99)
  - Error ratio
  - Token usage per minute
  - Queue depth (planner)
  - Overseer approvals vs rejections

## Alerts (examples)
- `5xx_error_ratio > 5% for 5m`
- `latency_p95 > 2s for 5m`
- `planner_queue_depth > 50 for 10m`
