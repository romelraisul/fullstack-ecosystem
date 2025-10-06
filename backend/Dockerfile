## Backend service Dockerfile (hardened)
# Pin by digest after verification (replace sha256:DEADBEEF...)
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN set -eux; \
    pip install --upgrade pip; \
    pip install --no-cache-dir -r requirements.txt; \
    find /usr/local -name "__pycache__" -type d -exec rm -rf {} +; \
    date -u > /image-build-date.txt

COPY app ./app

# Ensure ownership (in some base images uid 1000 already exists but we declare explicitly)
RUN groupadd -g 1000 appgroup 2>/dev/null || true; \
    useradd -u 1000 -g 1000 -M appuser 2>/dev/null || true; \
    chown -R 1000:1000 /app
USER 1000:1000

EXPOSE 8000

# Health check probes application health endpoint; tolerant to transient failures via retries at orchestrator level
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8000/health || curl -fsS http://127.0.0.1:8000/health || exit 1

ENV UVICORN_WORKERS=2

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop uvloop --http httptools --workers ${UVICORN_WORKERS:-2}"]
