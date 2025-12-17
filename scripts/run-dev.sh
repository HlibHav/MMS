#!/usr/bin/env bash
set -euo pipefail

# Dev runner for backend (FastAPI) and frontend (Vite).
# Usage:
#   chmod +x scripts/run-dev.sh
#   ./scripts/run-dev.sh
#
# Optional env vars:
#   BACKEND_PORT   (default 8000)
#   FRONTEND_PORT  (default 5173)
#   DATABASE_URL   (default duckdb file under .tmp)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
mkdir -p "${ROOT}/.tmp"
export PYTHONPATH="${ROOT}:${ROOT}/backend:${PYTHONPATH:-}"
# Use SQLite by default to avoid DuckDB locking in dev
export DATABASE_URL="${DATABASE_URL:-sqlite://${ROOT}/.tmp/mms_data.db}"

echo "Starting backend on :${BACKEND_PORT} (DB=${DATABASE_URL})"
(
  cd "${ROOT}"
  uvicorn backend.api.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}"
) &
BACK_PID=$!

echo "Starting frontend on :${FRONTEND_PORT}"
(
  cd "${ROOT}/frontend"
  npm run dev -- --host --port "${FRONTEND_PORT}"
) &
FRONT_PID=$!

trap 'kill ${BACK_PID} ${FRONT_PID} 2>/dev/null || true' INT TERM
wait
