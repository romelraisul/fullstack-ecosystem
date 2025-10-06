# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (<https://keepachangelog.com/en/1.1.0/>) and this project adheres (prospectively) to Semantic Versioning.

## [Unreleased]

### Added (Unreleased)

- Placeholder for upcoming improvements (auto gateway correlation injection, fleet-level error budget gauge, dashboard provisioning automation).

## [0.4.0] - 2025-09-29

### Added (0.4.0)

- Dynamic per-agent SLO thresholds (latency + error budget) via `agent_registry.json` hot-reload.
- Prometheus gauge exports for thresholds and generic alert refactor (latency, error, multi-window burn, error budget burn fast/slow).
- Adaptive synthetic traffic seeder querying Prometheus to skip organically active agents.
- Basic Auth enforcement and rate limiting in nginx for observability & agent routes.
- Correlation ID middleware across agents with structured logs.
- Expanded Grafana dashboard panels (dynamic p95, fast/slow burn, latency vs thresholds, error vs budget).
- Operations guide Sections 22–26 and Runbook TL;DR.

### Changed (0.4.0)

- Replaced static per-agent alert rules with generic join-based expressions.
- Updated documentation formatting and consolidated guidance.

### Security (0.4.0)

- Introduced Basic Auth + request rate limiting to mitigate unauthorized access & brute force.

## [0.3.0] - 2025-09-28

### Added (0.3.0)

- Error-rate SLO recording rules (5m & 30m) per agent and fleet.
- Error SLO alert group (high, critical, burn acceleration, fleet error rate).
- Initial error panels in dashboard (error % & burn ratio).

### Changed (0.3.0)

- Enhanced remediation and tuning guidance for error conditions.

## [0.2.0] - 2025-09-27

### Added (0.2.0)

- Latency SLO recording rules (p95) per agent.
- Latency alert rules (warning & critical) with `for` durations.
- Grafana p95 latency visualization.

### Changed (0.2.0)

- Standardized histogram usage across agents.

## [0.1.0] - 2025-09-26

### Added (0.1.0)

- Baseline multi-agent FastAPI services with metrics endpoints.
- Prometheus + Grafana + Alertmanager stack wiring.
- Initial synthetic traffic seeding (non-adaptive).
- Basic gateway reverse proxy and agent UI list.

---

## Release Process Notes

1. Update this file under [Unreleased].
2. Decide semantic bump (major/minor/patch) based on changes.
3. Replace [Unreleased] entries with a new version heading + date.
4. Commit with message: `chore(release): vX.Y.Z`.
5. Tag the commit: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and push tags.

