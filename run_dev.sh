#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8020}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
VITE_API_URL="${VITE_API_URL:-http://localhost:${BACKEND_PORT}}"

cd "$ROOT"
export PYTHONPATH="${ROOT}:${ROOT}/backend:${PYTHONPATH:-}"
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACK_PID=$!

cd frontend
VITE_API_URL="${VITE_API_URL}" npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}"

# Cleanup: kill backend when frontend exits
trap "kill ${BACK_PID} 2>/dev/null || true" EXIT
kill "${BACK_PID}" 2>/dev/null || true
