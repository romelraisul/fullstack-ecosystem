# Full-Stack Ecosystem (concise)

This repository contains a production-lean full-stack skeleton (FastAPI + React) with observability
and security workflow scaffolding. The README was normalized during an interactive rebase to remove
merge conflicts and keep the project landing page concise.

Quick start (Docker Compose):

1. cd to the repo root
2. docker compose up -d --build

Open services:

- Frontend: <http://localhost:5173>
- API health: <http://localhost:8010/health>
- Metrics: <http://localhost:8010/metrics>

For developer notes, CI workflows, and security scanning config see `.github/workflows/` and
the `security/` and `scripts/` directories.

---
*Note: The full, detailed README.md can be found in the repository history. This version has been condensed to resolve a merge conflict.*
