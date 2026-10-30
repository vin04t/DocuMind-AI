#!/usr/bin/env bash
# ==============================================================================
# DocuMind AI - Local Unified Service Launcher
# Launches FastAPI backend on :8000 and Next.js frontend on :3000
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "============================================================"
echo " Starting DocuMind AI (Evidence-Grounded Intelligence Platform)"
echo "============================================================"

# Check Python environment
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "Creating Python virtual environment in $BACKEND_DIR/venv..."
    python3 -m venv "$BACKEND_DIR/venv"
    "$BACKEND_DIR/venv/bin/pip" install --upgrade pip
    "$BACKEND_DIR/venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

# Check Node environment
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing Node.js dependencies in $FRONTEND_DIR..."
    (cd "$FRONTEND_DIR" && npm install)
fi

# Ensure storage directories exist
mkdir -p "$PROJECT_DIR/storage/pdfs"
mkdir -p "$PROJECT_DIR/storage/chroma"

# Export local environment defaults
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///$PROJECT_DIR/documind.db}"
export STORAGE_DIR="${STORAGE_DIR:-$PROJECT_DIR/storage/pdfs}"
export CHROMA_PERSIST_DIR="${CHROMA_PERSIST_DIR:-$PROJECT_DIR/storage/chroma}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export PYTHONPATH="$BACKEND_DIR"

echo "-> Starting Backend on http://127.0.0.1:8000..."
"$BACKEND_DIR/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir "$BACKEND_DIR" &
BACKEND_PID=$!

echo "-> Starting Frontend on http://127.0.0.1:3000..."
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "Stopping DocuMind AI services..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "============================================================"
echo " DocuMind AI is running!"
echo " -> Frontend: http://localhost:3000"
echo " -> Backend API: http://localhost:8000"
echo " -> Swagger Docs: http://localhost:8000/docs"
echo " Press Ctrl+C to terminate all services."
echo "============================================================"

wait
