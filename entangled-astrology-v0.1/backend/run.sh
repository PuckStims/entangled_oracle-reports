#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -z "${EO_ENGINE_ROOT:-}" ]; then
  EO_ENGINE_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
  export EO_ENGINE_ROOT
fi

PYTHON_BIN="${EO_ENGINE_ROOT}/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=python
fi

"$PYTHON_BIN" -m uvicorn entangled_mobile_backend.main:app \
  --app-dir "$SCRIPT_DIR" \
  --host "${EO_API_HOST:-127.0.0.1}" \
  --port "${EO_API_PORT:-8000}"
