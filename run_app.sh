#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run backend (uvicorn) and frontend (Vite) together.
# Usage:
#   ./run_app.sh            # uses default ports 8000 (api) and 5173 (ui)
#   UVICORN_PORT=9000 ./run_app.sh   # override backend port
#   VITE_PORT=3000 ./run_app.sh      # override frontend port

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v python >/dev/null 2>&1 || { echo "python is required on PATH" >&2; exit 1; }
command -v uvicorn >/dev/null 2>&1 || { echo "uvicorn is required (pip install -r backend/requirements.txt)" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required (install Node.js)" >&2; exit 1; }

export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"
export UVICORN_HOST="${UVICORN_HOST:-0.0.0.0}"
export UVICORN_PORT="${UVICORN_PORT:-8000}"
export VITE_HOST="${VITE_HOST:-0.0.0.0}"
export VITE_PORT="${VITE_PORT:-5173}"

cleanup() {
  trap - INT TERM EXIT
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup INT TERM EXIT

echo "Starting backend on ${UVICORN_HOST}:${UVICORN_PORT}..."
(
  cd "${ROOT_DIR}"
  python -m uvicorn backend.api.main:app --host "${UVICORN_HOST}" --port "${UVICORN_PORT}" --reload
) &
BACKEND_PID=$!

echo "Starting frontend on ${VITE_HOST}:${VITE_PORT}..."
(
  cd "${ROOT_DIR}/frontend"
  if [[ ! -d node_modules ]]; then
    echo "Installing frontend deps (npm install)..."
    npm install
  fi
  npm run dev -- --host "${VITE_HOST}" --port "${VITE_PORT}"
) &
FRONTEND_PID=$!

wait -n "${BACKEND_PID}" "${FRONTEND_PID}"

