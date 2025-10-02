# Multi-stage Dockerfile for governance_app
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (add git if we ever need to read local repo metadata inside container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for layer caching. We rely on the legacy requirements for now until migration is complete.
COPY governance-app/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy application code
COPY governance_app /app/governance_app
COPY governance_app/sample_push_event.py /app/governance_app/sample_push_event.py

EXPOSE 8081

# Non-root for safety
RUN useradd -u 10001 appuser
USER appuser

ENV WEBHOOK_SECRET=devsecret

CMD ["uvicorn", "governance_app.app:app", "--host", "0.0.0.0", "--port", "8081"]
