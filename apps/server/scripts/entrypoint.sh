#!/usr/bin/env bash
set -euo pipefail

MODE="${DB_REFRESH_MODE:-incremental}"
echo "[entrypoint] Refreshing database (mode: ${MODE})..."

# Run migrations using the managed virtualenv when present.
if [[ -x "/app/.venv/bin/python" ]]; then
  /app/.venv/bin/python scripts/manage_db.py
else
  python scripts/manage_db.py
fi

echo "[entrypoint] Starting API server..."
FASTAPI_BIN="/app/.venv/bin/fastapi"
if [[ ! -x "${FASTAPI_BIN}" ]]; then
  FASTAPI_BIN="fastapi"
fi

exec "${FASTAPI_BIN}" run main.py --host 0.0.0.0 --port "${PORT:-8000}"
