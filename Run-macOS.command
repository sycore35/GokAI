#!/usr/bin/env bash
# ========================================================================
# GÖKAI V1 — macOS Native Launcher (Inside gokai/)
# Double-click in Finder to launch GökAI Platform
# ========================================================================

set -e

cd "$(dirname "$0")"
GOKAI_DIR="$(pwd)"

echo "Starting GökAI Platform..."

PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ ! -f "$GOKAI_DIR/.env" ]; then
    cp "$GOKAI_DIR/.env.example" "$GOKAI_DIR/.env"
fi

if [ ! -d "$GOKAI_DIR/apps/frontend/node_modules" ]; then
    (cd "$GOKAI_DIR/apps/frontend" && npm install)
fi

cleanup() {
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$GOKAI_DIR/.." && $PYTHON_CMD -m uvicorn gokai.apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload) &
(cd "$GOKAI_DIR/apps/frontend" && npm run dev -- --port 3000 --host) &

sleep 3
open "http://localhost:3000" || true

wait
