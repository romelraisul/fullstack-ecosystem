# Docker Deployment Guide (Advanced Backend)

## Overview

This guide explains how to build and run the Advanced FastAPI backend (`autogen.advanced_backend:app`) using the new multi-stage Dockerfile and optional docker-compose service `advanced-backend`.

## Quick Start (Direct Docker)

1. Build image:
   docker build -t advanced-backend:latest .
2. Run container:
   docker run -d --name advanced-backend -p 8011:8000 \
     -e UVICORN_WORKERS=2 -e LOG_LEVEL=info \
     advanced-backend:latest
3. Test health:
   curl <http://localhost:8011/health>
4. Metrics (Prometheus format):
   curl <http://localhost:8011/metrics>

## Using docker-compose

From repository root:
  docker compose up -d advanced-backend

The service maps host port 8011 -> container port 8000.

## Environment Variables

Key runtime variables (override with `-e` or in compose):

- APP_MODULE (default autogen.advanced_backend:app)
- UVICORN_HOST (default 0.0.0.0)
- UVICORN_PORT (default 8000)
- UVICORN_WORKERS (default 2)
- LOG_LEVEL (info, debug, warning, error)
- ENVIRONMENT (development|production) affects security behavior

## Image Structure

Multi-stage build:

- Stage builder: installs dependencies into /opt/venv
- Stage runtime: copies virtual env + source, runs as non-root user `appuser`

## Healthcheck & Metrics

- /health basic status, version, uptime
- /metrics Prometheus exposition (request counts, latency, errors, anomaly flag)
- /api/v1/performance memory/cpu snapshot

## Rebuilding After Code Changes

If only Python source changed:
  docker build -t advanced-backend:latest . --no-cache
Or with compose:
  docker compose build advanced-backend && docker compose up -d advanced-backend

## Logs

Follow logs:
  docker logs -f advanced-backend

## Stopping & Removing

  docker stop advanced-backend && docker rm advanced-backend

## Production Tips

- Increase UVICORN_WORKERS based on CPU cores (generally 2 * cores)
- Add a reverse proxy (nginx / traefik) for TLS termination & caching
- Mount persistent volume if enabling SQLite persistence (map ./data)
- Use dedicated Postgres for scale (adjust code paths accordingly)

## Security Hardening

- Runs as non-root user
- Minimal base image (python:3.11-slim)
- Add vulnerability scanning (e.g., Trivy) in CI pipeline
- Set ENVIRONMENT=production to disable interactive docs

## Future Enhancements

- Add optional Postgres service override
- Multi-arch build (linux/arm64) via buildx
- Image SBOM export & signing

---
Generated automatically to accompany new containerization setup.
