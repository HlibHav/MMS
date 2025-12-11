#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/Glebazzz/MMS_clean"
BACKEND_PORT="${BACKEND_PORT:-8020}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
VITE_API_URL="${VITE_API_URL:-http://localhost:${BACKEND_PORT}}"

cd "$ROOT"
PYTHONPATH=./backend:. uvicorn backend.api.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACK_PID=$!

cd frontend
VITE_API_URL="${VITE_API_URL}" npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}"

kill "${BACK_PID}"
