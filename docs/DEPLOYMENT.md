# Deployment Guide

## 1. Environment
- Python 3.11+ recommended
- GPU optional; CPU-only works
- Outbound internet required if using external LLMs

## 2. Configuration
Copy `.env.example` to `.env` and set:
- `CB_API_HOST`, `CB_API_PORT`
- `OPENAI_API_KEY` or vendor equivalents
- `ALLOW_ORIGINS` (comma-separated)
- `ADMIN_TOKEN` for overseer actions
- `TELEMETRY_ENABLE` (true/false)

## 3. Run Modes
### Local Dev
```
make dev
```

### Docker
```
docker build -t capsule-brain:latest .
docker run --env-file .env -p 8000:8000 capsule-brain:latest
```

### Docker Compose (with monitoring)
```
docker compose up --build
```

### Kubernetes (basic example)
```
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 4. Backups
- Persist logs to volume or external collector (Loki, Cloud Logging)
- Version the `overseer_config.yaml` and `core_principles/`

## 5. Scaling
- Stateless API; scale horizontally.
- Use Redis or Postgres to persist memory if needed (future module).
