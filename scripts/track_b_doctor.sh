#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

cd "$BACKEND_DIR"
PYTHONPATH=. "$PYTHON_BIN" -m track_b.cli doctor
