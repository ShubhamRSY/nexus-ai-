#!/usr/bin/env bash
# Restart local Nexus dev server on port 8001 with current code.
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${APP_PORT:-8001}"

echo "Stopping anything on :${PORT}..."
pkill -f "uvicorn src.main:app.*${PORT}" 2>/dev/null || true
sleep 1

export DEMO_MODE="${DEMO_MODE:-true}"
export AUTH_REQUIRED="${AUTH_REQUIRED:-false}"
export HF_HOME="${HF_HOME:-./data/hf_cache}"
export SENTENCE_TRANSFORMERS_HOME="${SENTENCE_TRANSFORMERS_HOME:-./data/hf_cache}"

mkdir -p data/hf_cache

echo "Starting Nexus on :${PORT}..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT}" --reload
