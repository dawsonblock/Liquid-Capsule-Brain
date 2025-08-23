#!/usr/bin/env bash
set -euo pipefail
set -a
[ -f .env ] && . ./.env || true
set +a
uvicorn capsule_brain.api.server:app --host 0.0.0.0 --port ${CB_API_PORT:-8000} --reload
