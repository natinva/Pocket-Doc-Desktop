#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [ -x ".venv/bin/uvicorn" ]; then
  UVICORN=".venv/bin/uvicorn"
else
  UVICORN="uvicorn"
fi

RELOAD_ARGS=""
if [ "${POCKETDOC_RELOAD:-0}" = "1" ]; then
  RELOAD_ARGS="--reload"
fi

"$UVICORN" backend.pocketdoc_desktop.app:app --host "${POCKETDOC_HOST:-0.0.0.0}" --port "${POCKETDOC_PORT:-8765}" $RELOAD_ARGS
