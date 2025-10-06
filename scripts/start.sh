#!/usr/bin/env sh
set -e

: "${APP_MODULE:=autogen.advanced_backend:app}"
: "${UVICORN_HOST:=0.0.0.0}"
: "${UVICORN_PORT:=8000}"
: "${UVICORN_WORKERS:=2}"
: "${LOG_LEVEL:=info}"

echo "[start.sh] Launching Uvicorn: module=$APP_MODULE host=$UVICORN_HOST port=$UVICORN_PORT workers=$UVICORN_WORKERS log_level=$LOG_LEVEL"
exec uvicorn "$APP_MODULE" --host "$UVICORN_HOST" --port "$UVICORN_PORT" --workers "$UVICORN_WORKERS" --log-level "$LOG_LEVEL"
