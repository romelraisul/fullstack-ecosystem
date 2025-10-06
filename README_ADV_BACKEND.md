# Advanced Backend Enhancements

## Recent Hardening & Features

- Unified batch flush with atomic per-op error isolation.
- Full workflow persistence (definitions + steps) via `WorkflowsRepository`.
- Execution persistence now records `total_steps` and incremental progress updates.
- Optional per-request profiling middleware controlled by `ENABLE_PROFILING=true` and header `X-Profile: 1` or query `?profile=1`.
- Dedicated rate limit probe endpoint: `GET /api/v1/test/rate-limit` (3 req / 10s) for automated tests.
- Metrics cardinality safeguarded by using route templates in Prometheus labels.
- Base Docker image upgraded to `python:3.11-bookworm-slim`.
- Consolidated GitHub Actions CI workflow (`.github/workflows/ci.yml`).

## Profiling Usage

1. Set environment variable: `ENABLE_PROFILING=true`.
2. Send a request with either:
   - Header: `X-Profile: 1`, or
   - Query param: `?profile=1`.
3. Response headers returned:
   - `X-Profile-Duration-ms`: Wall time for the request.
   - `X-Profile-Top`: Top 5 memory diff frames (if `tracemalloc` active).

## Workflow Persistence

- Endpoints now persist workflows automatically when repository module is available.
- New endpoint added: `GET /api/v1/workflows/{workflow_id}` for single retrieval.
- Execution objects include `total_steps` for progress reporting.

## Rate Limit Testing

Use the new endpoint to assert 429 responses in CI:

```text
GET /api/v1/test/rate-limit
```

After 3 requests within 10 seconds a 429 response is expected.

### Forced Error & Anomaly Testing

Set `ENABLE_TEST_ENDPOINTS=true` to expose:

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/test/force-error` | Always returns HTTP 500 to raise error rate and trip anomaly gauge |

Use this in deterministic tests (see `test_anomaly_deterministic.py`).

## CI Overview

The CI pipeline performs:

- Dependency installation & caching
- Ruff lint checks
- Pytest execution
- Prometheus rule validation (if rule files present)
- Docker image build and size reporting
- OpenAPI schema diff (`openapi-diff` job) comparing generated schema to `openapi_schema_baseline.json` (flags removed paths)
- Bandit static security scan (fails build unless `ALLOW_VULNERABILITIES=true`)
- pip-audit dependency vulnerability scan (fails build unless `ALLOW_VULNERABILITIES=true`)
- Enforces failure on breaking OpenAPI path removals unless `ALLOW_OPENAPI_BREAKING=true` is set
- Granular OpenAPI diff now detects removed methods and schema properties (breaking)
- Performance smoke test exports JSON metrics artifact (`performance_smoke.json`)
- Manual baseline regeneration via `workflow_dispatch` input `update_openapi_baseline=true`
- SBOM generation with Syft (SPDX JSON) uploaded as artifact
- License scanning via `pip-licenses` (JSON + Markdown artifacts)
- Vulnerability severity threshold gating via external script (`scripts/vuln_gate.py`) honoring `VULN_SEVERITY_THRESHOLD`:
  - Fails only when vulnerabilities at or above threshold and `ALLOW_VULNERABILITIES` is not `true`.
  - Produces `pip-audit-report` artifact with raw JSON when findings exist.
  - Default threshold: `HIGH`.
  - Override (allow but log warning) by setting `ALLOW_VULNERABILITIES=true`.

### OpenAPI Additive Notice

If the schema diff detects only added paths (no removed paths, methods, or schema properties) CI emits a
GitHub Actions `::notice::` summarizing the count of additive paths. This provides visibility without
blocking merges.

### Performance Benchmark (Locust)

A manual `workflow_dispatch` performance benchmark job can be triggered with inputs:

| Input | Description | Default |
|-------|-------------|---------|
| `run_performance_benchmark` | Set to `true` to run job | false |
| `locust_users` | Concurrent virtual users | 25 |
| `locust_spawn_rate` | User spawn rate / sec | 5 |
| `locust_run_time` | Duration (e.g. 1m, 2m, 30s) | 1m |
| `perf_regression_tolerance_ms` | Allowed median latency increase before failing | 50 |
| `update_performance_baseline` | When `true`, update latency baseline from run | false |

Artifacts produced:

| Artifact | Contents |
|----------|----------|
| `performance-benchmark` | `locust_summary.json` (first lines of CSV stats) + raw Locust CSV outputs |

Locust script lives at `perf/locustfile.py` (currently exercises `/api/v1/health`). Extend with additional
tasks as endpoints stabilize.

## Environment Variables (Selected)

| Variable | Purpose | Default |
|----------|---------|---------|
| ENABLE_PROFILING | Enable profiling middleware | false |
| DB_PATH | SQLite DB path | data/platform.db |
| UVICORN_WORKERS | Gunicorn worker count in container | 2 |
| ENABLE_TEST_ENDPOINTS | Enable force-error test endpoints | false |
| VULN_SEVERITY_THRESHOLD | Minimum vulnerability severity that fails CI (LOW/MEDIUM/HIGH/CRITICAL) | HIGH |
| ALLOW_VULNERABILITIES | Allow vulnerabilities >= threshold (logs warning) | false |

## Read-Only Container Runtime (Optional)

For additional hardening you can run the container with a read-only filesystem and a writable temp volume:

```bash
docker run --read-only -v tmp-autogen:/tmp -p 8000:8000 autogen-advanced-backend:ci
```

Or docker-compose service snippet:

```yaml
      read_only: true
      volumes:
         - tmp-autogen:/tmp
```

## Next Suggestions

- Add load test harness for workflow execution concurrency.
- Introduce schema evolution policy (non-breaking additive changes auto-approved).
- Integrate vulnerability severity gating (fail only CVSS >= threshold).
- Automate baseline update PR creation instead of direct push.

## New Tests Added

| Test File | Purpose |
|-----------|---------|
| `test_workflow_cycle_error.py` | Ensures cyclic or unknown dependencies return 400 (topological validation) |
| `test_rate_limit_burst.py` | Validates multiple 429 responses under burst conditions & presence of `Retry-After` header |
| `test_performance_smoke.py` | Simple latency smoke test capturing avg & p95 bounds |
| `test_metrics_cardinality.py` | Guards against metrics label explosion by counting unique path labels |
| `test_anomaly_deterministic.py` | Deterministic anomaly trigger via forced-error endpoint |

## Governance Flags

| Env Var | Effect |
|---------|--------|
| `ALLOW_OPENAPI_BREAKING` | When `true`, CI will not fail on removed OpenAPI paths |
| `ALLOW_VULNERABILITIES` | When `true`, Bandit & pip-audit findings won't fail CI |
| `VULN_SEVERITY_THRESHOLD` | Minimum severity that fails build unless `ALLOW_VULNERABILITIES` set |
| `update_openapi_baseline` (dispatch input) | Triggers job to regenerate baseline when set to `true` |
| `run_performance_benchmark` (dispatch input) | Triggers Locust performance benchmark job |
| `perf_regression_tolerance_ms` (dispatch input) | Median latency regression tolerance in ms |
| `update_performance_baseline` (dispatch input) | Update and PR performance baseline |

### Vulnerability Severity Gating Logic

1. Run `pip-audit` to generate JSON (`pip_audit_report.json`).
2. Parse JSON in `scripts/vuln_gate.py`.
3. Collect vulnerabilities whose severities contain any level >= threshold ordering: LOW < MEDIUM < HIGH < CRITICAL.
4. Fail if such vulnerabilities exist and `ALLOW_VULNERABILITIES` is not `true`; otherwise emit warning.

### Extending Performance Coverage

Add new tasks to `perf/locustfile.py` for critical endpoints (workflow execution, conversation message
creation) to evolve beyond the simple health check baseline.

### Performance Regression & Baseline

The performance benchmark job extracts the first endpoint's median response time from `locust_stats.csv`.

Baseline file: `perf/performance_baseline.json`

Workflow:

1. Run benchmark with existing baseline present.
2. Compare new median vs baseline median.
3. If delta > `perf_regression_tolerance_ms` (default 50 ms), job fails with an error annotation.
4. To intentionally accept new (slower or improved) performance as the baseline, set
   `update_performance_baseline=true` in dispatch inputs.
5. A follow-on job `performance-baseline-pr` creates a PR updating the baseline file.

Override Options:

- Increase tolerance temporarily via dispatch input.
- Or update baseline to permanently adopt new metrics.

Artifacts:

- `performance-benchmark`: includes `locust_summary.json` with median / average and baseline delta info.
- `performance-baseline`: uploaded only when baseline updated.

Locust Tasks Implemented:

- Health check (`QuickHealthUser`).
- Conversation create + multiple message sends (`ConversationFlow`).
- Workflow create, execute, and poll until completion (`WorkflowExecutionUser`).

---
Generated on: 2025-10-05
