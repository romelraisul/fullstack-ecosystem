# Fullstack Ecosystem Architecture Overview

## 🏗️ System Architecture

The Fullstack Ecosystem is a comprehensive governance, security, and validation platform designed for modern software development workflows. This document provides an architectural overview of the system's components, data flows, and operational patterns.

```text
                          +-------------------------------+
                          |   GitHub Actions Workflows    |
                          | (governance-openapi-export,   |
                          |  taxonomy, security, etc.)    |
                          +---------------+---------------+
                                          |
                  Schema / Status Branch  |  Commit JSON artifacts
                         (schemas)        v
+------------------+     +---------------------------------------------+
|  FastAPI App     |     |   status/ (GitHub Pages via schemas branch) |
|  (governance &   |-->--|   - stability-metrics.json                  |
|  platform APIs)  |     |   - governance-summary.json                 |
+---------+--------+     |   - operations-classification.json          |
          ^              |   - semver-validation.json                  |
          |              |   - milestone-summary.json                  |
          | Prometheus   |   - checksums.json                          |
          | scrape       |   - index.html (composite status)           |
          |              +---------------------------------------------+
          |
  +-------+--------+
  |  Prometheus    |<-- Sample + Exporter metrics (API, internal sampler)
  +-------+--------+
          |
          v
     +---------+            +----------------+
     | Alert   |-- routes -->|  Webhook /     |
     | Manager |             |  Slack/Teams   |
     +---------+             +----------------+
```

## Core Components

### 1. Governance Pipeline (CI)

- Exports OpenAPI schema, diffs against previous.
- Detects breaking changes and enforces semantic version policy.
- Generates stability metrics & placeholder streak tracking.
- Classifies per-operation additions/removals.
- Emits webhook notifications on degradation, failures, and recoveries.
- Publishes artifacts + badges to `schemas` branch (consumed via GitHub Pages).

### 2. FastAPI Application

- Hosts primary API endpoints and governance header middleware.
- Exposes metrics (request latency, per-route counters, internal service latency sampler).
- Roadmap interest endpoint with spam/rate limiting.

### 3. Observability Stack

- Prometheus scrapes API + internal sampler metrics.
- Alertmanager evaluates SLO / burn alerts.
- Grafana dashboards visualize stability, latency, taxonomy, and internal sampler trends.

### 4. Automation / Governance Artifacts

- `stability-metrics.json` – Rolling ratios, streaks, placeholder state.
- `governance-summary.json` – Concise snapshot (ratio, semver status, op deltas).
- `operations-classification.json` – Added/removed operations.
- `semver-validation.json` – Policy outcome (ok/warn/fail).
- `milestone-summary.json` – Weighted completion of project milestones.
- `checksums.json` – Cryptographic integrity for key governance artifacts.

### 5. Integrity & Trust

- Deterministic SHA256 hashes per artifact plus aggregate hash.
- Intended future extension: optional signing (e.g., minisign or cosign) to assert provenance.

### 6. Webhook Event Model

Reasons emitted (trigger OR recovery):

- Failure: `semver_fail`, `stability_drop`, `placeholder_streak`
- Recovery: `semver_recovered`, `stability_recovered`, `placeholder_recovered`

### 7. Milestone Tracking

- Weighted JSON milestone file → summary + badge for progress transparency.
- Enables objective “% complete” badge decoupled from subjective README statements.

### 8. Security & Compliance Hooks

- Container / dependency scanning workflows (lite & deep planned).
- Rate limiting + security headers (edge via Traefik).
- Planned SBOM / advanced scanning (milestone placeholder).

## Data Flow Summary

1. Developer pushes -> CI workflow exports & analyzes schema.
2. Workflow updates `schemas` branch with fresh artifacts.
3. GitHub Pages serves JSON + HTML status from `schemas` branch.
4. Webhook fires to external systems (chat, orchestrators) with reasons or recovery signals.
5. Dashboards poll JSON & Prometheus for continuous health/stability insight.

## Extensibility Points

- Add new artifact producers (drop script + integrate into commit step) → automatically hashed & published.
- Add new webhook reasons without breaking consumers (payload tolerant of unknown reason strings).
- Plug additional milestone categories by editing `project_milestones.json` (badge auto-updates next run).

## Future Hardening Ideas

- Signed artifact manifest (aggregate hash + signature file).
- Drift detector comparing README documented fields vs live JSON schema.
- Webhook delivery retries with exponential backoff + dead letter queue simulation.

## Quick Reference File Map

| Area | Key Files |
|------|-----------|
| Governance CI | `.github/workflows/governance-openapi-export.yml` |
| Stability Scripts | `scripts/generate_stability_metrics.py`, `scripts/placeholder_streak_guard.py` |
| Diff / Classification | `scripts/diff_openapi_schema.py`, `scripts/classify_operation_changes.py` |
| Integrity | `scripts/generate_checksums.py` |
| Milestones | `project_milestones.json`, `scripts/generate_milestone_badge.py` |
| Webhook Schema | `docs/governance_webhook.schema.json` (planned) |
| Architecture | `docs/ARCHITECTURE.md` |

## Updating the Diagram

Update this file when introducing *new persistent artifact types*, *new webhook reasons*, or *structural
components* (e.g., signature service, SBOM generator).
