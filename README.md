# Capsule Brain Supreme AGI — Full Build (v1.0.1)
Liquid core + IIT Φ analyzer + Self-Wirer + Overseer + GUI + document Q&A.

## Features
- **Dynamic belief networks** with recursive self-modification
- **AI overseer** for ethical alignment and policy enforcement
- **Multi-modal integration** (text, code, eventually vision/audio)
- **Self-wiring cognition** with emergent behavior patterns
- **FastAPI + WebSocket GUI** for real-time interaction

## Quick Start

### Prerequisites
Run the build validation script to check your environment:
```bash
python3 validate_build.py
```

### Setup
```bash
cp .env.example .env  # Configure your settings
make dev-setup        # Install dependencies
make dev              # Start development server
```

For detailed build configuration, see [BUILD_CONFIG.md](BUILD_CONFIG.md).

## Admin Authentication
Capsule Brain now enforces an administrator token on sensitive endpoints such as `/healthz`, `/ready`, `/state/summary`, and `/graph/edge`.

- Set `ADMIN_TOKEN` in your environment (for example in `.env`).
- Clients must send the header `x-admin-token: <your-token>` when calling protected routes.
- In local development profiles (`APP_ENV=development`, `APP_PROFILE=local`, etc.) the header is optional so you can iterate quickly.

## Observability & Metrics
Prometheus metrics are exposed at `GET /metrics` via `prometheus-fastapi-instrumentator` and are safe to scrape without authentication.

Example Prometheus configuration targeting the Docker Compose service:

```yaml
scrape_configs:
  - job_name: capsule-brain
    static_configs:
      - targets: ["capsule-brain:8000"]
    metrics_path: /metrics
```

The `grafana/` directory ships dashboards that visualise request performance and engine internals.

## Docker Compose Healthchecks
Docker Compose definitions include healthchecks for the API, Prometheus, and Grafana. During local runs you can rely on Compose waiting for services before reporting success:

```bash
ADMIN_TOKEN=local-token docker compose up --build --wait
```

The API healthcheck automatically supplies the admin header, so your stack will report healthy status only when protected endpoints accept the configured token.

## Testing & Dependency Overrides
- Unit and integration tests now cover the admin header enforcement and the Prometheus metrics endpoint (`pytest -q`).
- Dependency overrides can be exercised in tests with `app.dependency_overrides[get_engine]`—see `tests/test_di_overrides.py` for a working example.

## Continuous Integration
GitHub Actions runs the following on every push and pull request:
- `lint`: Ruff style checks.
- `type-check`: MyPy static typing.
- `test`: Pytest suite.
- `build-and-scan`: Docker image build plus Trivy filesystem and image scans.
- `compose-smoke`: Brings the stack up with Docker Compose, waits for health, and curls `/healthz`, `/ready`, and `/metrics`.
