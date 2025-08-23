# Capsule Brain Supreme AGI — Extended README (Ops Edition)

## Overview
This extends the root README with **deployment, operations, monitoring, and security** specifics for running Capsule Brain in real environments (local, Docker, Compose, or Kubernetes).

## Components
- **FastAPI API**: `capsule_brain/api/server.py` (REST + WebSocket)
- **Overseer**: `teacher/ai_overseer.py` (policy gates, review)
- **GUI**: `capsule_brain/gui/gui.py` (+ static assets)
- **Core**: `capsule_brain/core/*` (belief state, alignment, self-wiring)
- **Planner/Retrieval/Tools**: structured utilities for tasks and memory

## Quickstart (Local)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill values
python launch_capsule_brain.py
# API: http://127.0.0.1:8000  GUI: python -m capsule_brain.gui.gui
```

## Quickstart (Docker Compose)
```bash
cp .env.example .env   # fill secrets
docker compose up --build
# API: http://127.0.0.1:8000  Grafana: http://127.0.0.1:3000  Prometheus: http://127.0.0.1:9090
```

## Ports
- **8000**: API/GUI backend
- **9090**: Prometheus (metrics)
- **3000**: Grafana (dashboards)

## Health + Metrics
- **Liveness**: `GET /healthz`
- **Readiness**: `GET /ready`
- **Metrics**: `GET /metrics` (Prometheus format)

## Logging
- Structured JSON logs via Python `logging` with `uvicorn.access` combined. Customize in `logging_config.json`.

## Secrets
- Local: `.env` file (never commit). CI/Prod: inject via environment or secret manager (GCP Secret Manager, AWS SM, Vault).
