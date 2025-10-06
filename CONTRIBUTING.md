# Contributing Guide

Thanks for helping improve the Multi‑Agent Observability & Operations Platform.

## Core Principles

- **Predictable Operations**: Every change must preserve or improve reliability signals (SLO metrics, alerts, dashboards).
- **Automation First**: Prefer generated / derived artifacts over hand‑edited drift.
- **Least Surprise**: Follow existing patterns (metrics naming, file layout, env var style).
- **Security & Traceability**: Preserve request correlation (X-Request-ID) and do not weaken Basic Auth / rate limiting defaults.

## Repository Layout (Essentials)

- `OPERATIONS.md` – Authoritative runbook (TL;DR auto-generated between markers).
- `docs/runbook_sources.yml` – Source-of-truth for TL;DR generation.
- `scripts/generate_runbook_tldr.py` – Regenerates TL;DR block.
- `docker/` – Prometheus / Alertmanager / Grafana / gateway configs & rules.
- `autogen/` – Dynamic metrics & registry integration code.
- `agent_registry.json` – Per-agent latency & error SLO thresholds.
- `CHANGELOG.md` – Version history (Keep a Changelog format).

## Adding / Modifying Agents

1. Append agent entry with thresholds to `agent_registry.json`.
2. Ensure agent exports metrics & correlation headers.
3. Reload / restart the summary service or trigger its hot reload endpoint (if implemented).
4. Confirm new gauges & histograms appear in Prometheus (`/metrics`).
5. Update dashboard panels only if new unique metric dimensions are introduced.

## Dynamic SLO Thresholds

- Per-agent latency/error budgets live in `agent_registry.json`.
- Fleet error budget fraction configured via env: `FLEET_ERROR_BUDGET_FRACTION` (default `0.01`).
- Exposed as gauge: `agent_fleet_error_budget_fraction`.
- Alert rules reference gauges—avoid reintroducing hard‑coded fractions.

## Adaptive Synthetic Seeder

The adaptive seeder reduces noise by only stimulating agents whose organic traffic is below a configurable 5m RPS threshold. Key environment variables (see `scripts/synthetic_seed.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROMETHEUS_BASE` | `http://localhost:9090` (in-compose: `http://prometheus:9090`) | Prometheus API base for rate queries |
| `SEED_RPS_THRESHOLD` | `0.1` | Skip agents at/above this 5m RPS rate |
| `SEED_MAX_AGENTS` | `10` | Safety cap of agents stimulated each run |
| `SEED_DRY_RUN` | `0` | When `1`, only logs planned stimulations (used in CI) |
| `AGENT_REGISTRY` | `autogen/agents/agent_registry.json` | Override registry path |

Local dry-run example:

```powershell
$env:SEED_DRY_RUN=1; python scripts/synthetic_seed.py
```

Tuning tips:

- If synthetic traffic appears on moderately active services, lower `SEED_RPS_THRESHOLD`.
- To reduce dev noise, also reduce `SEED_MAX_AGENTS` (e.g. 3) while iterating.
- CI will execute a dry-run to ensure script integrity—avoid adding heavy runtime dependencies.

## TL;DR Regeneration

After editing `docs/runbook_sources.yml` run:

```bash
python scripts/generate_runbook_tldr.py
```

Commit both modified files. Never manually edit generated TL;DR content inside markers.

## Releasing

1. Update `CHANGELOG.md` under `[Unreleased]` → create new version section (e.g. `## [0.5.0] - YYYY-MM-DD`).
2. Ensure TL;DR regenerated & matches sources.
3. Sanity check alerts load: Prometheus config reload or container restart.
4. Tag commit: `git tag v0.5.0 && git push --tags`.
5. (Optional) Publish release notes referencing CHANGELOG diff.

## Coding Standards

- Python: type-friendly, prefer explicit imports. Keep functions small & side‑effect scoped.
- Metrics: `snake_case`, use consistent prefixes (`agent_`, `fleet_`). Counters `_total`, Histograms buckets standard.
- Alerts: Multi-window burn formulas must divide by the dynamic error budget gauge.
- Docs: Wrap at ~100 chars; list styles consistent (unordered for conceptual, ordered for procedures).

## Testing Changes Locally

- Start stack (example tooling will be added): docker compose up -d
- Visit Prometheus `/graph` to query new gauges.
- Intentionally induce errors (e.g. 500s) to validate alert firing in dev.

## Security Considerations

- Do not commit real credentials; Basic Auth users should be sample only.
- Preserve `X-Request-ID` propagation path (gateway → agents → logs / traces).

## Submitting a PR

1. Create a focused branch name: `feat/`, `fix/`, `docs/`, `ops/` prefix.
2. Include rationale & validation notes.
3. Confirm no markdown lint regressions (CI TODO).
4. Reference related issue / changelog line.

## Common Pitfalls

- Hard-coding numeric error fractions in rules (should use gauges).
- Forgetting TL;DR regeneration after source YAML edits.
- Adding agents without thresholds (leads to default fallbacks and noisy alerts).
- Introducing dashboards without variable scoping → panel explosion.

## Future Automation (Open for Contribution)

- Makefile & PowerShell ops scripts.
- CI markdown lint & rule test harness.
- Synthetic seeder adaptive tuning based on burn rate.

---

Thank you for contributing to a resilient and scalable platform.

---

## Test Coverage Ratchet Policy

We employ an incremental coverage ratchet to sustainably raise backend test coverage
without blocking early iteration.

### Current State

- Actual backend coverage (latest CI): ~43%
- Enforced threshold: 43%
- Next target: reach ≥49% actual, then raise threshold to 48–49% (leave 1–2 points headroom).

### Ratchet Rules

1. Start threshold near the real baseline instead of an aspirational number.
2. After a test addition, if actual coverage exceeds the threshold by ≥4–6 points,
  raise the threshold to sit 1–2 points below the new coverage.
3. Aim for ~+5 point increments; larger jumps allowed if stable.
4. Never decrease the threshold unless a documented refactor removes substantial code
  legitimately (open an issue referencing lines removed & rationale).
5. New feature PRs introducing logic should include tests or a follow-up issue labeled
  `coverage` before merge.

### High-Yield Areas Still Uncovered

- Bridge module persistence & error branches.
- Orchestrate endpoints (demo / delegate flows) with lightweight stubs.
- Control endpoints (`/control/*`) lifecycle responses.
- Latency sampler loop realistic branch (network success vs failure) with httpx mock.
- Error validation paths for latency target updates (bad body types / empty lists).

### Test Writing Guidelines

- Use `TestClient` context managers to run lifespan tasks.
- Patch or directly inject internal state instead of sleeping for background tasks.
- Avoid real outbound HTTP; mock httpx responses when exercising sampler logic.
- Keep tests deterministic; prefer explicit construction over shared global fixtures.

### Local Commands

Run fast tests:

```powershell
pytest -q
```

Run with coverage report:

```powershell
pytest --cov=backend --cov-report=term-missing
```

### Contributing to Coverage

When raising coverage, include in PR description:

- New % (from / to)
- New threshold (if changed)
- Key modules newly exercised
- Any intentionally skipped branches (and why)

---
