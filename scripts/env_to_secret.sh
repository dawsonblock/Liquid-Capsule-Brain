#!/usr/bin/env bash
set -euo pipefail
NS="${1:-capsule-brain}"
OUT="${2:-cb-secret.yaml}"
kubectl create secret generic cb-env --from-env-file=.env -n "$NS" --dry-run=client -o yaml > "$OUT"
echo "Wrote $OUT"
