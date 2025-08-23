#!/usr/bin/env bash
set -euo pipefail
export $(grep -v '^#' .env | xargs) || true
uvicorn capsule_brain.api.server:app --host 0.0.0.0 --port ${CB_API_PORT:-8000} --reload
