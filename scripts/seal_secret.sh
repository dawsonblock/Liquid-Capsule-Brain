#!/usr/bin/env bash
set -euo pipefail
NS="${1:-capsule-brain}"
IN="${2:-cb-secret.yaml}"
OUT="${3:-cb-sealed.yaml}"
kubeseal --controller-namespace sealed-secrets --controller-name sealed-secrets -n "$NS" -o yaml < "$IN" > "$OUT"
echo "Wrote $OUT"
