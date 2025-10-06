# Advanced Backend Recent Enhancements (Oct 2025)

## New Execution Persistence Features

- Workflow executions are now fully persisted in SQLite (table: `workflow_executions`) with step states in
  `workflow_execution_steps`.
- Added `step_order` persistence for deterministic historical reconstruction.
- Retention pruning after each execution completion (env: `WORKFLOW_EXECUTION_RETENTION`, default 1000; set <=0 to
  disable).

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workflows/{workflow_id}/execute` | Start a new execution (persisted) |
| GET | `/api/v1/workflows/executions/{execution_id}` | Retrieve execution + step states |
| GET | `/api/v1/workflows/{workflow_id}/executions?limit&offset` | List executions for a workflow |
| GET | `/api/v1/workflows/executions?limit&offset` | List all executions |
| POST | `/api/v1/workflows/executions/{execution_id}/replay` | Replay (re-run) a finished or failed execution |

Replay now persists lineage via `replay_of` column plus an `input_snapshot` (original workflow definition steps) for
reproducibility and audit.

## Performance Regression Tooling (Multi-endpoint + p95)

`scripts/perf_regression.py` upgraded:

- Baseline schema version 2: `{ "version":2, "endpoints": { "GET /api/v1/ping": { "median_ms": 40.0, "p95_ms": 85.0 } } }`
- Supports gating on both median (`REG_TOL_MEDIAN_MS`) and p95 (`REG_TOL_P95_MS`).
- Optional endpoint filtering via `TRACK_ENDPOINTS` (comma-separated substrings).
- `UPDATE_BASELINE=true` overwrites baseline with current run metrics for tracked endpoints.

## SLO Alerting / Error & Latency Webhook

Middleware tracks rolling error rates (overall, 5xx-only, 4xx-only) over a window (`SLO_ERROR_RATE_WINDOW`, default
300s) and rolling latency distribution over `SLO_LATENCY_WINDOW` (default 300s). Breach conditions:

- Overall error rate >= `SLO_ERROR_RATE_THRESHOLD` (default 0.05)
- 5xx error rate >= `SLO_ERROR_RATE_5XX_THRESHOLD` (defaults to overall threshold if unset)
- 4xx error rate >= `SLO_ERROR_RATE_4XX_THRESHOLD` (default 0.10)
- p95 latency >= `SLO_LATENCY_P95_THRESHOLD` (default 0.750s)

On breach a JSON POST is sent to `SLO_ALERT_WEBHOOK_URL` (if set) observing `SLO_ALERT_COOLDOWN_SECONDS` (default 300s).

Payload example:

```json
{
  "type": "slo_error_rate_breach",
  "error_rate": 0.12,
  "threshold": 0.05,
  "window_seconds": 300,
  "timestamp": "2025-10-05T12:34:56Z",
  "path": "https://service/api/v1/workflows/executions/abc"
}
```

## Failure-path Tests

Added `tests/test_backend_failures.py` covering:

- Repository failure during execution start (ensures client still receives 200 launch response).
- DB batching queue overflow behavior (enqueue returns False without raising).

## Environment Variables Summary

| Variable | Default | Purpose |
|----------|---------|---------|
| `WORKFLOW_EXECUTION_RETENTION` | 1000 | Max executions kept (global) |
| `SLO_ERROR_RATE_THRESHOLD` | 0.05 | Overall (4xx+5xx) error rate breach threshold |
| `SLO_ERROR_RATE_5XX_THRESHOLD` | (overall) | 5xx-only error rate threshold |
| `SLO_ERROR_RATE_4XX_THRESHOLD` | 0.10 | 4xx-only error rate threshold |
| `SLO_ALERT_WEBHOOK_URL` | (unset) | Webhook endpoint for SLO alerts |
| `SLO_ALERT_COOLDOWN_SECONDS` | 300 | Cooldown between alerts |
| `SLO_ERROR_RATE_WINDOW` | 300 | Rolling window length (seconds) |
| `SLO_LATENCY_P95_THRESHOLD` | 0.750 | p95 latency breach threshold (seconds) |
| `SLO_LATENCY_WINDOW` | 300 | Latency percentile evaluation window (seconds) |
| `REG_TOL_MEDIAN_MS` | 50 | Median latency tolerance per endpoint |
| `REG_TOL_P95_MS` | 80 | p95 latency tolerance per endpoint |
| `TRACK_ENDPOINTS` | (all) | Comma substrings of endpoints to enforce |
| `UPDATE_BASELINE` | false | Overwrite baseline with current metrics |
| `PERF_JUNIT` | false | Emit JUnit XML perf report (`perf/performance_junit.xml`) |
| `WORKFLOW_STEP_DURATION_BUCKETS` | (preset) | Comma list of float bucket upper bounds for step duration histogram |

## Migration Notes

- Existing `workflow_executions` table is ALTERed to add `step_order` automatically on first repository instantiation
  (best-effort, ignored on failure).
- Old single-metric performance baseline (version 1) remains compatible only if you keep previous script. After upgrade,
  set `UPDATE_BASELINE=true` once to generate schema version 2 baseline.

## New Metrics

- `workflow_step_duration_seconds{workflow_id,step_name}` Histogram for step runtimes.
- `workflow_step_errors_total{workflow_id,step_name}` Counter for step-level failures.

Failure simulation: add `"fail": true` inside a workflow step definition to force that step to raise a simulated
failure (useful for testing error counters and FAILED overall execution states).

## JUnit Performance Report

When `PERF_JUNIT=true` the regression script writes `perf/performance_junit.xml` allowing CI test report surfaces to
display per-endpoint performance cases (failures correspond to regressions beyond tolerance).

## Completed Roadmap Items

- Persist `replay_of` and original parameter snapshot.
- Per-step duration & error metrics exported to Prometheus.
- Distinct 5xx vs 4xx error rate tracking and latency p95 SLO alerts.
- Manual purge CLI (`python -m scripts.purge_executions [retention]`).
- SLO webhook alert test (`tests/test_slo_webhook_alert.py`).

---

Generated by automated assistant refactor session.
