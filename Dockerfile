#############################################
# Multi-stage Dockerfile for Advanced Backend
# Stage 1: Builder - install dependencies
#############################################
FROM python:3.11-bookworm-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal manifest files first for caching
# Copy manifest files individually if they exist (ignore missing)
COPY requirements.txt /app/requirements.txt
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
COPY setup.cfg /app/setup.cfg

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && if [ -f requirements.txt ]; then /opt/venv/bin/pip install -r requirements.txt; fi \
    && if [ -f poetry.lock ]; then pip install poetry && poetry export -f requirements.txt --output /tmp/poetry-req.txt --without-hashes && /opt/venv/bin/pip install -r /tmp/poetry-req.txt; fi

#############################################
# Stage 2: Runtime - slim image with app code
#############################################
FROM python:3.11-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_MODULE="autogen.advanced_backend:app" \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=2 \
    LOG_LEVEL=info

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source (keep context lean with .dockerignore)
COPY . /app

EXPOSE 8000

# Basic HTTP healthcheck against /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request,os,sys;\nurl=f'http://127.0.0.1:{os.getenv('UVICORN_PORT','8000')}/health';\nprint('Pinging',url);\nurllib.request.urlopen(url).read()" || exit 1

# Non-root execution for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# (Optional) Switch filesystem to read-only at runtime by adding: --read-only via docker run or compose.
# Launch via uvicorn (workers configurable via env)
CMD ["sh", "-c", "uvicorn $APP_MODULE --host $UVICORN_HOST --port $UVICORN_PORT --workers $UVICORN_WORKERS --log-level $LOG_LEVEL"]
