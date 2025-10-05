[![Alerts Total](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-total.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Deprecated Ratio](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-deprecated.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![30d Churn](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-churn.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Risk Churn 30d](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-risk-churn.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Stability](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-stability.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Risk Stability](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-risk-stability.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Runbook Completeness](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-runbook-completeness.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Days Since Change](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-taxonomy-age.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Nightly Stability Refresh](https://github.com/romel/fullstack-ecosystem/actions/workflows/governance-stability-nightly.yml/badge.svg)](https://github.com/romel/fullstack-ecosystem/actions/workflows/governance-stability-nightly.yml)
[![Placeholder Streak](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/placeholder-streak-badge.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Governance Summary](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/governance-summary-badge.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Gov+Semver](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/governance-combined-badge.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)

# Full‑Stack Ecosystem (Fast Build)

![Prometheus Rules](https://github.com/romel/fullstack-ecosystem/actions/workflows/promtool.yml/badge.svg)
![Typing (mypy-fast)](https://github.com/romel/fullstack-ecosystem/actions/workflows/mypy-fast.yml/badge.svg)

A minimal, production‑leaning full‑stack skeleton with FastAPI + React, plus
Prometheus/Grafana for observability.

## Quick start

- Build & run with Docker Compose

```powershell
cd c:\Users\romel\fullstack-ecosystem
# Build and start
$env:COMPOSE_PROJECT_NAME="ecosystem"; docker compose up -d --build

# Open services
Start-Process http://localhost:5173
Start-Process http://localhost:8010/health
Start-Process http://localhost:8010/metrics
Start-Process http://localhost:3030
```

## Deployment & Operations Overview

This service now includes scaffolding for production deployment and observability:

### Structured JSON Logging

Enabled by default (env `JSON_LOGGING=true`). Each log line is a single JSON object containing
timestamp, level, logger, message, module, function, line number and (when available) a
`request_id` propagated from the `X-Request-ID` header (configurable via `REQUEST_ID_HEADER`).

Disable JSON format by setting `JSON_LOGGING=false` (falls back to human formatter). Control
verbosity with `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`.

When tracing is enabled, logs automatically include `trace_id` and `span_id` fields (OpenTelemetry context) allowing
direct correlation between distributed traces and structured log events.

### OpenTelemetry (Tracing)

Optional tracing setup via `ENABLE_TRACING=true` and (optionally) `TRACING_ENDPOINT` pointing
to an OTLP HTTP collector (e.g. Tempo / Jaeger collector gateway). If opentelemetry libraries
are not installed the app degrades gracefully and logs a skip notice.

### Async Postgres Migration Scaffold

`db_migrations_async.py` provides a minimal async migration runner using `asyncpg` when
`POSTGRES_DSN` is set AND `ENABLE_ASYNC_MIGRATIONS=true`. A `schema_migrations` table stores
applied migration names. Extend by adding new `Migration("0002_description", async def ...)` items
to `DEFAULT_MIGRATIONS` or your own list. If dependencies or DSN are absent the step is skipped.

#### Migration Autodiscovery

Place additional migration files under a `migrations/` directory named like `0002_add_table.py` exporting an
`async def upgrade(conn): ...` coroutine. These are auto-discovered and appended to the default set at startup
when migrations run. Naming ensures natural ordering; avoid renaming applied migrations.

### Helm Chart

Located under `deploy/helm/ultimate-summary/` (basic Deployment + Service). Install with:

```bash
helm upgrade --install ultimate-summary ./deploy/helm/ultimate-summary \
  --set image.repository=your-repo/ultimate-summary --set image.tag=sha-<commit>
```

Key values (override via `--set` or a values file):

- `env.SUMMARY_AUTH_SECRET` – JWT signing secret (or use multi-key registry file)
- `env.LOG_LEVEL`, `env.JSON_LOGGING`, `env.ENABLE_TRACING`

#### Helm Extensions Added

- Ingress (toggle via `ingress.enabled`)
- HorizontalPodAutoscaler (`hpa.*` values)
- PodDisruptionBudget (`pdb.enabled`)
- ServiceMonitor for Prometheus Operator (`serviceMonitor.enabled`)
- Secret templating (`secret.create`, `secret.data`) for lightweight secret injection (prefer external secret store in prod)

Add ingress, resources, HPA, network policies, and secrets integration as you evolve the chart.

### Terraform Skeleton

Under `infra/terraform/ultimate_summary/` a minimal module currently provisions a Kubernetes
namespace. Extend with providers for secret management (Vault / AWS / GCP / Azure), config maps,
service accounts, or external databases. Example:

```bash
cd infra/terraform/ultimate_summary
terraform init
terraform apply -auto-approve
```

### Smoke Test Script

`scripts/smoke_auth.py` performs a minimal end‑to‑end auth flow: login -> achievements -> refresh -> metrics.
Run after each deployment:

```bash
python scripts/smoke_auth.py --base http://localhost:8000 --user admin --password <pw>
```

### Recommended Next Hardening Steps

1. Add liveness + readiness routes distinct from `/metrics` if you need finer control.
2. Externalize secrets to a secret store (Vault / SSM / Secrets Manager / Kubernetes Secrets with encryption at rest).
3. Add rate limit configuration to ConfigMap + dynamic reload (currently env based).
4. Introduce migration autoload discovery (filesystem glob) with checksum validation.
5. Add trace & log correlation (inject trace/span ids into log formatter when tracing enabled).
6. Expand Helm chart with PodDisruptionBudget, HPA, resource tuning, and PodSecurityContext.
7. Add CI job to run `smoke_auth.py` against ephemeral preview environments.
8. Add structured trace/log correlation dashboards (Grafana Loki + Tempo).
9. Implement multi-environment config layering (base + env overlay values.yaml).

### Environment Variable Summary (New)

| Variable | Purpose |
|----------|---------|
| LOG_LEVEL | Logging level (INFO default) |
| JSON_LOGGING | Enable JSON logs (true/false) |
| ENABLE_TRACING | Toggle OpenTelemetry instrumentation |
| TRACING_ENDPOINT | OTLP HTTP endpoint (optional) |
| POSTGRES_DSN | Enables async migrations + future Postgres usage |
| ENABLE_ASYNC_MIGRATIONS | Run async migration scaffold when true |

### Test Suite & CI

Basic pytest coverage added for login + refresh + ETag caching and a rate-limit stress loop. CI workflow (`.github/workflows/smoke.yml`)
builds a minimal environment, starts the app via uvicorn, runs the smoke script and then pytest. Enhance by asserting
metrics exposure and adding negative-case tests (revoked token, lockout, rate-limit blocks) as you iterate.

### Security & Metrics Test Coverage (Expanded)

The test suite now includes dedicated negative-path and metric assertion specs:

- `tests/test_security_negative.py` – lockout, rate-limit saturation, refresh token reuse protection, revoked access token behavior, binding variance.
- `tests/test_auth_metrics_security.py` – parses `/metrics` exposition text to assert increments for:
  - `auth_login_total{result="fail"...}` and `auth_login_total{result="success"...}`
  - `auth_lockouts_total`
  - `auth_rate_limit_block_total{endpoint="login|refresh"}` after deliberate abuse.
- `tests/test_trace_log_correlation.py` – (conditional) verifies `trace_id` + `span_id` appear in structured logs when OpenTelemetry tracing is enabled.

Run a focused subset locally:

```bash
pytest -q tests/test_security_negative.py::test_refresh_token_rotation
```

### Layered Helm Values

Two overlay value files were added for environment layering:

- `values-dev.yaml` – debug logging, tracing disabled, reduced resources, migrations enabled for rapid iteration.
- `values-prod.yaml` – tracing on, higher resource requests/limits, HPA + PDB + ServiceMonitor enabled, ingress configured.

Deploy with overlay:

```bash
helm upgrade --install ultimate-summary ./deploy/helm/ultimate-summary -f deploy/helm/ultimate-summary/values-prod.yaml \
  --set image.repository=your-repo/ultimate-summary --set image.tag=sha-<commit>
```

Or for dev:

```bash
helm upgrade --install ultimate-summary-dev ./deploy/helm/ultimate-summary -f deploy/helm/ultimate-summary/values-dev.yaml \
  --set image.repository=your-repo/ultimate-summary --set image.tag=dev-latest
```

### Smoke Workflow Hardening

The original `smoke.yml` encountered YAML structural issues and has been replaced with a minimal validated `smoke-lite.yml` workflow. Next planned enhancement is to append:

1. Container image build (using commit SHA tag)
2. Vulnerability scan (e.g. Trivy) failing on HIGH/CRITICAL severities
3. Optional SBOM generation and artifact upload

Illustrative (future) steps snippet:

```yaml
  - name: Build image
    run: docker build -t $REGISTRY/ultimate-summary:${{ github.sha }} .
  - name: Trivy scan
    uses: aquasecurity/trivy-action@<pinned-sha>
    with:
      image-ref: $REGISTRY/ultimate-summary:${{ github.sha }}
      format: 'table'
      exit-code: '1'
      severity: 'HIGH,CRITICAL'
```

### Tracing & Log Correlation

When `ENABLE_TRACING=true`, each structured log line will attempt to include the current `trace_id` and `span_id`. The correlation test ensures at least one log entry contains both fields under a tracing-enabled environment (skipped otherwise). This enables unified pivoting in Grafana / Loki / Tempo.

### Quick Metrics Validation

After local stress testing you can manually inspect the key counters:

```bash
curl -s http://localhost:8000/metrics | grep -E 'auth_(login|refresh|lockouts|rate_limit_block)_'
```

Expected examples:

```
auth_login_total{result="success",reason="-"} 3
auth_login_total{result="fail",reason="bad_credentials"} 7
auth_lockouts_total 1
auth_rate_limit_block_total{endpoint="login"} 2
```

### Makefile Shortcuts

Use `make summary-run` to run the summary service locally or `make summary-smoke` after it’s up to validate core auth.
Existing targets already cover governance, Prometheus rule validation, and selective mypy checks.

If unset, tracing/migrations are skipped gracefully.

## What’s included

## Placeholder Streak Governance

The *Placeholder Streak* badge tracks how many consecutive governance runs produced only a
placeholder stability metrics file (i.e. real rolling stability metrics could not be
generated). A persistent placeholder typically indicates a silent failure *before* the
metrics script executes (for example: schema export error, diff script issue, or a commit
that altered workflow paths).

Badge color scale:

| Streak | Color        | Meaning |
|--------|--------------|---------|
| 0      | brightgreen  | Healthy – latest run produced full metrics |
| 1–2    | green        | Minor transient issue – watch but not urgent |
| 3–4    | yellow       | Degradation – investigate soon |
| >=5    | red          | Stalled metrics pipeline – action required |

An automated issue is opened once the streak reaches the configured alert threshold
(`placeholder_streak_alert_threshold`, default 5). The issue auto-creation stops when one
is already open.

### Common causes

- Upstream script changed name/path and workflow no longer finds it
- Dependency install failure preventing metrics generation
- Permissions issue writing to the `schemas` branch
- Intermittent network failure during dependency/tool download

### Remediation checklist

1. Open the latest failed `governance-openapi-export` workflow run logs.
2. Confirm whether `generate_stability_metrics.py` executed (search for its step header).
3. If it never ran, locate the first failure or early exit (e.g. diff gate fail, missing file).
4. If it ran but still produced placeholder, inspect `stability-metrics.json` content.
5. Verify the `schemas` branch HEAD advanced (lack of commits may indicate push failure).
6. Re-run the failed job *with debug logging* if necessary (enable step debug via repo settings or add temporary `set -x`).
7. After fixing, confirm the streak resets to 0 on the next successful run.

### Configuration knobs

- `placeholder_max_runs`: Hard fail if placeholder streak exceeds this many consecutive runs (guarding silent stagnation).
- `placeholder_streak_alert_threshold`: Open an alert issue when streak reaches this threshold (0 disables alerting).

### Extension field

The numeric streak is written into the metrics JSON under `extensions.placeholder_streak` so dashboards or
downstream automation can consume it without depending on badge scraping.

If you intentionally pause metrics generation (e.g. maintenance), consider temporarily raising
the alert threshold and documenting the reason in the open issue to avoid false emergency noise.

## API Stability Metrics

This section provides rolling insight into how frequently the exported OpenAPI
contract changes in a *non‑breaking* way versus introducing breaking changes or
failing to produce full metrics.

Key computed fields (in `stability-metrics.json`):

- `window_stability_ratio` – Percentage of runs in the configured rolling
  window that were stable (no breaking changes) and produced full metrics.
- `window_size` – Number of recent runs considered for the rolling window.
- `window_stable_count` / `window_total_count` – Numerator & denominator for
  the ratio.
- `current_stable_streak` – Current consecutive stable run count (resets on a
  breaking change or placeholder fallback).
- `longest_stable_streak` – Historical max stable streak observed.
- `overall_stability_ratio` – Lifetime stability ratio across all recorded
  runs.
- `window_mean_score` – Mean of per‑run stability scores over the window (if
  scoring logic evolves beyond binary signals).
- `placeholder` – Flag indicating the metrics object is a placeholder (real
  metrics generation failed earlier in the pipeline).
- `extensions.placeholder_streak` – Consecutive placeholder run count (mirrors
  the Placeholder Streak badge).

Operational behaviors:

1. A workflow exports the OpenAPI schema, diffs it, and classifies breaking vs
   non‑breaking changes.
2. Each run appends a history line (JSONL) and regenerates
   `stability-metrics.json` on the `schemas` branch.
3. Shields endpoint JSON badges (stability + placeholder streak) surface state
   in the README.
4. Alerts
   - Stability degradation issue opens if `window_stability_ratio` < threshold.
   - Placeholder streak alert opens if consecutive placeholders >= configured
     threshold.
5. Auto‑close logic: Once a placeholder streak alert exists it closes after
   metrics recover unless a suppression label (e.g. `governance-hold`) is
   applied.

Consumption patterns:

- Dashboards: poll `status/stability-metrics.json` (and optionally
  `status/governance-summary.json`).
- Machine checks: use a minimal summary JSON (streak + ratio) instead of
  parsing the full metrics.
- Humans: view the composite HTML status page (`status/index.html`) for quick
  triage.

Future extensions (ideas):

- Per‑category change counters (additions/removals/deprecations) for richer
  scoring.
- Semantic version bump validation tied to breaking detection.
- Anomaly detection for sudden stability ratio drops.

If you arrived here from an alert: first confirm whether the metrics file is a
placeholder. If yes, follow the Placeholder Streak remediation steps; if not,
inspect the recent breaking diff and validate it matches versioning policy.

## Semantic Versioning & Stability Policy

This project enforces a lightweight semantic version alignment between the published
OpenAPI contract and detected breaking changes. A validator step generates
`semver-validation.json` (stored under `status/`) with a status of `ok`, `warn`, or
`fail`.

Policy rules:

1. Breaking change present => Major version MUST increase (fail otherwise).
2. Major version increased but no breaking change => Fail (avoid artificial major churn).
3. Minor bumped with no breaking change => Warn (allowed; patch MAY have sufficed).
4. Patch bumps are always acceptable if no breaking change.

Rationale:

- Prevents accidental silent breaking changes under a stable major.
- Discourages premature major releases that fragment early adopters.
- Provides gentle guidance (warning) when a minor bump might oversignal.

Artifact shape (`status/semver-validation.json`):

```jsonc
{
  "status": "ok|warn|fail",
  "current_version": "2025.09.17+abc1234", // date+build metadata form
  "previous_version": "2025.09.16+def5678",
  "breaking": false,
  "messages": ["Human readable policy evaluations"],
  "recommendations": ["Actionable next-step hints"]
}
```

Downstream usage:

- CI / Release tooling can fail early on `status == fail`.
- Dashboards can surface `status/semver-validation.json` alongside
  `status/governance-summary.json` for a holistic view (stability ratio + policy fit).

Live composite status (HTML auto-refreshes every 5m):

<https://romel.github.io/fullstack-ecosystem/index.html>

Embed snippet (governance summary badge + quick ratio + semver status fetch):

```html
<img alt="Governance" src="https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/governance-combined-badge.json" />
<script>
async function renderGovernance(){
  try {
    const d = await fetch('https://romel.github.io/fullstack-ecosystem/governance-summary.json',{cache:'no-store'}).then(r=>r.json());
    console.log('Stability ratio', d.stability_ratio, 'SemVer policy', d.semver_policy_status);
    const host = document.getElementById('gov-host');
    if(host){
      host.innerHTML = `<strong>API Stability:</strong> ${(d.stability_ratio*100).toFixed(2)}% &middot; <strong>SemVer Policy:</strong> ${d.semver_policy_status}`;
    }
  } catch(e){ console.warn('Governance summary fetch failed', e); }
}
renderGovernance();
</script>
<div id="gov-host" style="font:14px system-ui,Arial;margin-top:4px;color:#444"></div>
```

Future enhancements (planned):

- Include `semver_policy_status` field in `governance-summary.json` for single-fetch dashboards.
- Optional webhook on `fail` to accelerate remediation feedback loops.
- Per-operation change classification to differentiate “breaking but safe to auto-migrate” vs hard removals.
- Signed SHA256 checksum of schema + summary bundle for enterprise audit trails.

### Webhook & Checksum (Planned)

Planned automation will emit a slim JSON webhook payload on:

- Breaking change detection
- Stability ratio crossing below alert threshold
- SemVer policy failure

Payload draft (subject to refinement):

```jsonc
{
  "event": "api.governance.breaking", // or stability.degradation, semver.policy.fail
  "at": "2025-09-17T10:23:45Z",
  "commit": "abc1234",
  "stability_ratio": 0.872,
  "semver_policy_status": "fail",
  "breaking_changes_count": 3,
  "schema_checksum_sha256": "<hex>"
}
```

Checksum generation will hash the canonical OpenAPI schema and `governance-summary.json` concatenated
to support downstream integrity verification (e.g. store alongside artifact in an append-only log or
transmit via signed headers).

## Governance Webhook Payload (Implemented)

When certain governance conditions are met on `main`, a JSON webhook is POSTed (if `GOVERNANCE_WEBHOOK` secret is configured).

### Trigger Reasons (Failure Conditions)

- `semver_fail` – Semantic version policy validation returned `fail`.
- `stability_drop` – Rolling stability ratio (`window_stability_ratio`) fell below the configured alert threshold.
- `placeholder_streak` – Metrics file is a placeholder and placeholder streak >= configured threshold.

### Trigger Reasons (Recovery Conditions)

Recovery reasons are emitted once when a previously failing condition returns to a
healthy state, reducing alert fatigue and enabling automated resolution workflows:

- `semver_recovered` – Previous run(s) had `semver_fail`; current run status is now `ok|warn`.
- `stability_recovered` – Stability ratio has risen back to or above the configured threshold after a `stability_drop` alert.
- `placeholder_recovered` – Placeholder streak cleared (a real metrics file replaced
  the placeholder after crossing the alert threshold).

Multiple reasons (failure and/or recovery) can appear together. Example: a run could
simultaneously fix a placeholder streak (`placeholder_recovered`) but newly violate
semantic versioning (`semver_fail`).

### Current Payload Shape

```jsonc
{
  "event": "governance_notice",
  "version": 1,
  "sha": "abc1234",                // Short commit SHA
  "semver_status": "ok|warn|fail",
  "stability_ratio": 0.93,          // window_stability_ratio (0 if missing)
  "reasons": ["semver_fail"],       // Failure and/or recovery reasons
  "operations": {                   // Per-operation delta (from operations-classification.json)
    "added": 2,
    "removed": 0
  }
}
```

Field notes:

- `stability_ratio` falls back to 0 if the metrics file wasn't present (rare – early failure before metrics generation).
- `operations.added/removed` reflect counts, not arrays (arrays live in the published `status/operations-classification.json`).
- Future additions (non-breaking) will use new top-level keys; consumers should ignore unknown keys.

### Minimal JSON Schema (Snapshot)

Canonical, always up-to-date schema: `docs/governance_webhook.schema.json` (validated
in tests). The excerpt below is a snapshot (trimmed) including the new recovery reasons:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GovernanceWebhookPayload",
  "type": "object",
  "required": ["event","version","sha","semver_status","stability_ratio","reasons","operations"],
  "properties": {
    "event": {"const": "governance_notice"},
    "version": {"type": "integer", "minimum": 1},
    "sha": {"type": "string", "minLength": 7, "maxLength": 40},
    "semver_status": {"type": "string", "enum": ["ok","warn","fail","unknown"]},
    "stability_ratio": {"type": "number", "minimum": 0},
    "reasons": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "semver_fail",
          "stability_drop",
          "placeholder_streak",
          "semver_recovered",
          "stability_recovered",
          "placeholder_recovered"
        ]
      },
      "uniqueItems": true
    },
    "operations": {
      "type": "object",
      "required": ["added","removed"],
      "properties": {
        "added": {"type": "integer", "minimum": 0},
        "removed": {"type": "integer", "minimum": 0}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": true
}
```

### Versioning / Consumer Guidance

- Payload version is an integer (`version`) starting at 1. Increment only on **breaking** changes
  (removals of fields or semantic meaning changes). Additive fields or new reason values do *not* bump.
- Treat unknown top-level keys as optional enhancements.
- Avoid failing hard if `reasons` contains an unfamiliar value – future reasons may still be introduced; prefer WARN + ignore.
- If strict validation is required, pin to an allowlist of known enums but log (not
  fail) on unknown ones to ease forward compatibility.

### Example Recovery Payloads

Single recovery event (stability ratio back above threshold):

```json
{
  "event": "governance_notice",
  "version": 1,
  "sha": "d3adb33",
  "semver_status": "ok",
  "stability_ratio": 0.91,
  "reasons": ["stability_recovered"],
  "operations": {"added": 0, "removed": 0}
}
```

Mixed failure + recovery (placeholder fixed, but semantic version failure introduced):

```json
{
  "event": "governance_notice",
  "version": 1,
  "sha": "51gn3d1",
  "semver_status": "fail",
  "stability_ratio": 0.89,
  "reasons": ["placeholder_recovered", "semver_fail"],
  "operations": {"added": 1, "removed": 0}
}
```

### Correlating With Artifacts

Artifacts pushed to the `schemas` branch under `status/` correspond to the same commit SHA:

- `status/governance-summary.json` – stability ratio, placeholder info, semver policy status, operation counts.
- `status/operations-classification.json` – full arrays of added/removed operations (method + path).
- `status/stability-metrics.json` – full rolling metrics window and streak info.

These can be fetched by downstream systems for richer dashboards keyed by the webhook's `sha`.

### Checksum Bundle

Integrity artifacts are generated each run:

- `checksums.json` – SHA256 per governance artifact (schema, summary, metrics,
  operations classification, semver validation, milestone summary) plus an aggregate
  hash (lexicographically ordered join of individual hashes).
- `checksums-badge.json` – Shields endpoint summarizing the aggregate digest (for visual drift detection).

Use case examples:

- Downstream audit pipeline can re-hash fetched artifacts and compare to `checksums.json`.
- Future enhancement will sign the aggregate hash (detached signature) for tamper-evidence.

### Signature (Experimental)

If a signing key is configured (`GOV_SIGNING_PRIVATE_KEY` secret with a base64 Ed25519 32-byte seed),
each run produces:

- `checksums-signature.json` – Signature metadata and signature over canonical payload
  `{aggregate_sha256,count}` (sorted, compact JSON) using Ed25519.
- `checksums-pubkey.txt` – Base64 public key (for simple copy/paste verification).

Webhook payload version badge: once published, a badge `payload-version-badge.json` reflects current webhook payload
contract version (e.g. `v1`). Consumers can quickly detect required parsing logic.

Extended signature format (v2): signature now covers the explicit list of artifact path + hash pairs
in addition to the aggregate hash and count. Field `signature_format_version` distinguishes formats (legacy v1 lacked
the `artifacts` array in canonical payload). Verification tooling auto-detects.

Generate a new keypair locally:

```powershell
python scripts/generate_signing_keypair.py
```

Emit JSON for automation pipelines:

```powershell
python scripts/generate_signing_keypair.py --json > new_keypair.json
```

Verify locally (PowerShell example after cloning `schemas` branch contents):

```powershell
pip install pynacl
python scripts/verify_checksums_signature.py --checksums status/checksums.json --signature status/checksums-signature.json
```

Expected output: `VERIFY_OK` (non-zero exit + stderr details on failure).

Rotation guidance:

1. Generate new keypair offline.
2. Update secret; deploy.
3. Keep old public key available to verifiers until prior signed artifact retention window expires.
4. Optionally add a `previous_public_keys` array in signature JSON in a future schema if overlapping trust windows needed.

Threat model notes:

- Signature binds only the aggregate hash + count; altering individual artifact file while recomputing hash breaks signature.
- Attackers with write access to both artifacts and signature plus key compromise defeat this layer (treat key as sensitive).
- For stronger assurance, publish public key fingerprint out-of-band (e.g. release notes, security page) and consider a
  hardware-backed signer.

---

## Adding New Projects / Subsystems

See `docs/ADDING_PROJECTS.md` for a step-by-step guide (inventory, events, governance wiring, tests, metrics & alerting integration).

## Research Bridge (now usable)

- Submit research inputs from the frontend (title, problem, hypothesis optional, tags, owner optional, impact score)
- Filter inputs by owner / tag / status; assign owner; transition status; approve to experiments
- Metrics exposed at `/metrics`:
  - `bridge_inputs_total` — total inputs created
  - `bridge_experiments_total` — total experiments approved
  - `bridge_inputs_by_status{status}` — current inputs count by status label
  - `bridge_inputs_by_owner{owner}` — current inputs count by owner
  - `app_request_duration_seconds_bucket` — API latency histogram buckets
- Grafana dashboards:
  - API Overview: basic app health and request rate
  - API Overview: latency (P95/P99) from histogram
  - Bridge Overview: totals, rates, inputs by status, inputs by owner

## Ops add-ons

- Route-level metrics:
  - `app_requests_total_by_route{method,route,status}`
  - `app_request_duration_seconds_by_route{method,route,status}`
- Alerts (Prometheus):
  - HighLatencyP95 (>700ms for 10m)
  - LowSuccessRatio (<99% for 10m)
  - NoExperimentsIn1h
  - HighRejectedShare (>50% for 15m)

### Unified Operations Dashboard (HTML)

An aggregated HTML view with live health checks + embedded Grafana dashboards is
served by the gateway at:

- `http://localhost:5125/dashboard-ops.html`

Features:

- Auto-refresh (configurable 15s/30s/60s/2m) service health table (API, Prometheus,
  Alertmanager, Grafana, exporters, Qdrant, Autogen backend)
- Inline latency + up/down status indicators
- Kiosk-mode embedded Grafana dashboards (API Overview, Alerts Overview, Agent
  Fleet)
- Quick links to PromQL explorer, metrics endpoints, existing 5099 dashboard

Recent enhancements:

- Per-service latency sparkline (last 30 samples)
- Latency cell color coding (<150ms green, <500ms amber, >=500ms red)
- Live firing alert count + severity breakdown via Alertmanager API

Backend latency sampler (new):

- Background task in API samples internal service health URLs every 15s (configurable via `LATENCY_SAMPLE_INTERVAL`).
- Targets configurable with `LATENCY_SAMPLE_TARGETS` env var (comma-separated `name:url`).
  Default includes: api, gateway, prometheus, grafana, alertmanager.
- History retained in-memory (200 samples per service) and exposed at:
  - `http://localhost:8010/api/service-latencies`
- Response shape:
  - `updatedAt`: ISO8601 timestamp
  - `services[]`: object with fields:
    - `name`, `url`, `samples[]`
    - `stats{ latest_ms, min_ms, max_ms, p50_ms, p90_ms, p99_ms, attempts, ok, failure_rate_pct, latest_class }`
  - Each sample: `{ ts, ms, status, ok, cls }` (`cls` ∈ good|warn|high|na)
- Threshold classes:
  - good: ≤150ms
  - warn: 151–400ms
  - high: >400ms
  - na: most recent attempt failed
- Dashboard section “Backend Latency Samples” renders server-side trends independent of browser refresh cadence.

Prometheus metrics emitted by sampler (names stable, labels versioned via service name):

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `internal_service_latency_seconds` | Histogram | `service`, `success` ("true"/"false") | Distribution of sampled internal service latency (seconds). Includes failures recorded with observed duration prior to error. |
| `internal_service_latency_last_ms` | Gauge | `service` | Most recent successful latency in milliseconds (omitted / unchanged on failure). |
| `internal_service_latency_class` | Gauge | `service` | Numeric classification of latest sample: good=0, warn=1, high=2, na=3. Enables alerting without PromQL case logic. |
| `internal_service_latency_attempts_total` | Counter | `service` | Total sampling attempts (success + failure). |
| `internal_service_latency_ok_total` | Counter | `service` | Total successful sampling attempts. |

Failure rate can be derived:

`1 - (sum by(service)(rate(internal_service_latency_ok_total[5m])) / sum by(service)(rate(internal_service_latency_attempts_total[5m])))`

Or directly from JSON field `failure_rate_pct` for UI.

Example PromQL (alert idea):

```promql
# High p99 internal latency (>800ms for 10m)
histogram_quantile(0.99, sum by (service, le)(rate(internal_service_latency_seconds_bucket[10m]))) > 0.8

# Internal sampler failure rate >10% for 5m
(1 - (sum by(service)(rate(internal_service_latency_ok_total[5m])) / sum by(service)(rate(internal_service_latency_attempts_total[5m])))) > 0.10
```

UI toggle (Latency View selector):

- "Both" (default) shows browser-sampled health table and server-sampled backend latency table.
- "Browser-Sampled Only" hides the server table (useful when focusing on external availability & edge path).
- "Server-Sampled Only" hides the browser table (focus on internal dependency performance / headless trend continuity).

New columns in backend latency table: `p99` and `Failure %` sourced from JSON stats; `Failure %` rendered with one decimal.

Use it as a single “morning glance” page; open full Grafana for deeper drill‑down.

### Internal Latency Dashboard & Burn Alerts

New dedicated Grafana dashboard: `Internal Latency Overview` (auto‑provisioned) featuring:

- State timeline (discrete): `internal_service_latency_class` per service (good=green, warn=amber, high=red, na=gray)
- p99 latency timeseries (derived from histogram buckets)
- Failure rate timeseries (5m rolling derived from attempts/ok counters)
- Attempts vs OK stacked comparison for quick success ratio intuition

Prometheus alert rules (internal-sampler scope):

| Alert | Purpose | Trigger (abridged) | Severity |
|-------|---------|--------------------|----------|
| InternalServiceP99LatencyHigh | Absolute p99 breach | p99 > 800ms (10m) | medium |
| InternalServiceFailureRateHigh | Elevated failure rate | failure% > 10% (5m) | medium |
| InternalServiceP99LatencyBurnFast | Rapid p99 spike (fast burn) | (5m p99 > 1.3×30m) & 5m p99 >0.8s | high |
| InternalServiceP99LatencyBurnSlow | Sustained elevated p99 (slow burn) | (30m p99 >1.2×6h) & 30m p99 >0.8s | medium |

Runbooks (see `alerts_taxonomy.json`):

- Fast burn: investigate recent deploys, infra saturation, cascading dependency errors; consider rollback or emergency scale.
- Slow burn: examine capacity trends, memory/GC pressure, gradual demand growth;
  plan right‑sizing before user latency SLOs erode.
- Failure rate: inspect service logs, upstream dependency health, DNS/network; confirm health endpoint logic validity.

Persistence precedence (latency targets):

On startup the API now prefers a persisted `backend/app/data/latency_targets.json`
(if present & non‑empty) over the `LATENCY_SAMPLE_TARGETS` environment variable.
This enables runtime reconfiguration via `POST /admin/latency-targets { persist: true }`
that survives restarts without image rebuild or env churn.

An event `latency.targets.init` is emitted (viewable via `/events/recent`) indicating
`source` = `persisted` or `env` and the loaded target count.

Operational workflow:

1. Adjust targets via admin endpoint with `persist=true`.
2. Confirm new targets appear in `/api/service-latencies` & Grafana panels.
3. Persisted file becomes canonical for subsequent restarts, reducing drift.

Alert evolution guidance:

- Fast burn should page (high severity) — quick spike implies acute regression.
- Slow burn should create a ticket — gives buffer before user-facing SLIs degrade.
- Tune multipliers (1.3 fast, 1.2 slow) and absolute floor (0.8s) as baseline stabilizes.

Example burn rule (fast):

```promql
histogram_quantile(0.99, sum by(service, le)(rate(internal_service_latency_seconds_bucket[5m]))) > 1.3 * histogram_quantile(0.99, sum by(service, le)(rate(internal_service_latency_seconds_bucket[30m])))
and histogram_quantile(0.99, sum by(service, le)(rate(internal_service_latency_seconds_bucket[5m]))) > 0.8
```

Use the slow burn to catch creeping regressions; fast burn acts as early-warning tripwire.

### Gauge: internal_service_latency_targets

This gauge exposes how many internal latency sampler targets are currently active and the provenance
of that configuration. It is labeled by `source` with two possible values:

> Full catalog of all metrics & recording rules: see [METRICS.md](./METRICS.md)
> (authoritative reference; update it when adding metrics or recording rules).

| source | Meaning |
|--------|---------|
| `persisted` | Targets loaded from `backend/app/data/latency_targets.json` (written via admin API with `persist=true`). |
| `env` | Targets derived from `LATENCY_SAMPLE_TARGETS` environment variable (default fallback set). |

Scrape example:

```text
# HELP internal_service_latency_targets Current number of configured internal latency sampler targets
# TYPE internal_service_latency_targets gauge
internal_service_latency_targets{source="persisted"} 5
```

Operational notes:

- If both a non-empty persisted file and env var exist, the file wins (long-term stability & drift avoidance).
- After updating targets through the admin endpoint with `persist=true`, the `persisted` series should update
  immediately; confirm via `/metrics` or the “Configured Targets (by source)” stat panel in the
  Internal Latency Overview dashboard.
- Absence of the `persisted` label (only `env` present) means no persisted file is currently applied.
- Sudden drop in value may indicate a malformed file or regression in parsing logic; consult API logs / events.

PromQL quick check (current active count regardless of source):

```promql
sum(internal_service_latency_targets)
```

Distinct source counts (should be 1 active source typically):

```promql
count(internal_service_latency_targets)
```

### Microsoft Teams alerts (optional)

- This stack includes a prometheus-msteams bridge and routes Alertmanager to it by default.
- Configure your Teams incoming webhook URL in `docker/msteams-config.yml` (replace `<PUT_YOUR_TEAMS_WEBHOOK_URL_HERE>`).
- Services involved:
  - `alertmanager` (port 9093)
  - `msteams` bridge (port 2000) — Alertmanager posts to `http://msteams:2000/alertmanager`.

## Security hardening (now enabled)

This stack ships with pragmatic web security defaults so you don't have to wait weeks:

### Frontend Nginx

- Security headers: X-Frame-Options=DENY, X-Content-Type-Options=nosniff, Referrer-Policy=no-referrer
- CSP baseline: self-only for scripts/styles, data: for images/fonts, no object/frame ancestors
- `server_tokens off`, `client_max_body_size 1m`, gzip enabled, caching tuned for static assets

### Backend API (FastAPI)

- In-memory rate limit middleware (10 r/s, burst 20)
- CORS defaults narrowed to common headers/methods

### Notes

- HSTS is commented by default (enable only when TLS is terminated in front)
- COEP is commented (can break 3rd‑party embeds); enable when appropriate
- For production, prefer a reverse proxy/ingress to enforce TLS and secrets

## Project notes

- Images are not pin‑digested for speed; pin later for prod.

## Operational Tooling Additions

The observability/operations enhancements include:

- Prometheus rule unit tests (`docker/prometheus_rules.test.yml`) runnable locally via:
  - `make prom-rules` (syntax check)
  - `make prom-rules-test` (unit test scenarios)
  - `make promtool-install` (bootstrap pinned promtool binary if you don't have it globally)
  - Windows fallback (no make): `pwsh scripts/promtool-install.ps1 -Version 2.55.1`
- Synthetic traffic seeder dry-run:
  - `make seeder-dry-run` (uses `SEED_DRY_RUN=1`)
  - `make seed-fleet` (executes real stimulation logic)
- Dynamic SLO thresholds & gauges (see `OPERATIONS.md` sections 13–23)
- CI executes: markdown lint, promtool rule check + tests, pytest (SLO & seeder tests), seeder dry-run smoke.

### Quick Commands

```powershell
# Validate & unit test Prometheus alert rules
make prom-rules
make prom-rules-test

# Dry-run synthetic seeder (no network stimulation)
make seeder-dry-run

# Run real seeding once
make seed-fleet

# Regenerate TL;DR in operations guide
make tldr
```

#### Benchmark & Aggregation

```powershell
# Run quantile benchmark (stdout only)
make benchmark-quantiles

# Run benchmark writing JSON artifact (POSIX shell style shown; PowerShell use Get-Date)
BENCH_OUT=artifacts/quantile_bench_$(date +%Y%m%d_%H%M%S).json make benchmark-quantiles

# Aggregate benchmarks into JSON + Markdown (configure glob as needed)
make aggregate-benchmarks INPUT_GLOB="artifacts/quantile_bench_*.json" JSON_OUT=artifacts/aggregate.json MD_OUT=artifacts/aggregate.md

# Prepare environment after reboot (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/prepare_env.ps1
```

For deeper operational details and environment variables consult `OPERATIONS.md`.

See also `docs/benchmarking.md` for performance benchmarking rationale, rolling averages,
sparklines, and CI PR comment integration.

## Local Development Utilities (New)

### Metrics Test Helpers

Reusable Prometheus metric assertions live in `tests/utils/metrics.py`:

```python
from tests.utils.metrics import assert_metric_present

def test_latency_targets():
  assert_metric_present(
    'internal_service_latency_targets',
    predicate=lambda lines: any('source="env"' in l for l in lines)
  )
```

Key features:

- Optional `registry` parameter lets you assert against an isolated `CollectorRegistry` you
  construct inside a unit test (synthetic counters / histograms) without perturbing the
  process global.
- Predicate hook supports flexible label/value checks while keeping test bodies terse.

Extended capabilities (new):

- `get_single_sample` – assert exactly one series (with optional label filter) and retrieve its parsed value.
- `approximate_histogram_quantile` – quick pXX approximation for unit tests
  from `_bucket` cumulative counts (linear within bucket).
- `metrics_diff` – compute deltas between two registry snapshots (enable `strict_counters=True` to fail on counter regressions).
- `filter_metrics_diff` – refine diff output by name prefix and/or label predicate to keep assertions focused.

### Per‑Test Registry Isolation

Pytest fixtures swap in a fresh Prometheus default registry per test (see `conftest.py`).
This prevents duplicate time series errors (`duplicated timeseries in CollectorRegistry`) when
modules defining metrics are imported repeatedly. Use the helper above for asserting presence;
avoid manual `generate_latest` parsing.

### PYTHONPATH Enforcement

`sitecustomize.py` ensures the repository root is always importable, eliminating brittle
relative path hacks. Validate locally via:

```powershell
make ensure-pythonpath
```

CI also exports `PYTHONPATH` defensively and imports the utilities to fail fast if path regressions occur.

### Unified Dashboard Wrapper

`scripts/start_unified_dashboard.py` wraps launching the FastAPI unified operations dashboard
(health + embedded Grafana). Options:

```powershell
python scripts/start_unified_dashboard.py --port 5125 --reload
```

Flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | 5125 | Listening port |
| `--host` | 0.0.0.0 | Bind interface |
| `--reload` | disabled | Enable auto-reload (dev only) |
| `--workers` | 1 | Uvicorn workers (omit with --reload) |

This consolidates prior ad‑hoc uvicorn invocation commands and standardizes local ops workflows.

### Quick Reference

| Concern | Command |
|---------|---------|
| Verify path + helpers | `make ensure-pythonpath` |
| Run latency targets unit tests only | `pytest -q tests/unit/test_latency_targets_unit.py` |
| Launch dashboard (dev reload) | `python scripts/start_unified_dashboard.py --reload` |
| Launch dashboard (prod style) | `python scripts/start_unified_dashboard.py --workers 2` |

### Resource Usage Trend Enhancements (New)

The `scripts/resource_usage_trend.py` tool now supports:

- Rolling tail parsing of an existing JSONL file (specify `--jsonl <path>`; it appends new samples and emits trend metrics).
- Sequence numbering (`seq`) for each emitted row to enable idempotent downstream processing.
- Delta computation fields: `delta_net_in`, `delta_net_out`, `delta_mem_used` (first sample has zero deltas).
- Histogram bucket emission (opt‑in) for CPU and memory percentage via `--hist-cpu` / `--hist-mem` with customizable boundaries.
- Per-container gauges plus rolling window aggregates (avg/max) across the
  window (default window size 120; override with `--window N`).

Example (local quick snapshot):

```powershell
python scripts/resource_usage_trend.py --jsonl trends/resource_usage.jsonl --prom trends/resource_usage.prom --window 150 --hist-cpu "0,10,25,50,75,90,100" --hist-mem "0,25,50,75,90,100"
```

Prometheus metric families introduced:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `resource_trend_cpu_pct` | Gauge | `container` | Latest sampled CPU percent per container |
| `resource_trend_mem_pct` | Gauge | `container` | Latest sampled memory percent per container |
| `resource_trend_net_rx_bytes` | Gauge | `container` | Latest cumulative RX bytes (for delta analysis) |
| `resource_trend_net_tx_bytes` | Gauge | `container` | Latest cumulative TX bytes |
| `resource_trend_cpu_pct_bucket` | Histogram | `le` | CPU percent distribution across window (if `--hist-cpu`) |
| `resource_trend_mem_pct_bucket` | Histogram | `le` | Memory percent distribution (if `--hist-mem`) |
| `resource_trend_cpu_pct_count/sum` | Histogram suffix | | Standard histogram counters (if hist enabled) |
| `resource_trend_mem_pct_count/sum` | Histogram suffix | | Standard histogram counters (if hist enabled) |
| `resource_trend_window_size` | Gauge |  | Actual samples considered (may be < window on cold start) |

Use histogram percentiles with standard `histogram_quantile` queries; example p95 CPU across window:

```promql
histogram_quantile(0.95, sum by (le)(rate(resource_trend_cpu_pct_bucket[5m])))
```

### Severity / Runbook Coverage Dashboard (New)

`scripts/severity_runbook_dashboard.py` generates both an HTML summary and
Prometheus metrics for alert severity distribution and runbook completeness
derived from `alerts_taxonomy.json`.

Usage:

```powershell
python scripts/severity_runbook_dashboard.py --taxonomy alerts_taxonomy.json --html severity_runbook_dashboard.html --prom taxonomy_dashboard_metrics.prom
```

Emitted metrics (sample):

| Metric | Labels | Meaning |
|--------|--------|---------|
| `taxonomy_alerts_total` | `severity` | Count of alerts per severity (active + deprecated) |
| `taxonomy_alerts_runbook_missing` |  | Count of active alerts missing non‑placeholder runbook |
| `taxonomy_alerts_runbook_coverage_percent` |  | Percentage (0‑100) runbook completeness |

The HTML artifact is published in QA CI (see below) and can be attached to governance dashboards or PR comments.

### Slack Notification Blocks (Optional)

`notify_taxonomy_drift.py` now supports Slack Block Kit formatting. Enable by setting:

```powershell
$env:TAXONOMY_SLACK_BLOCKS = "1"
python scripts/notify_taxonomy_drift.py --prev prev_taxonomy.json --curr alerts_taxonomy.json --webhook $env:SLACK_WEBHOOK_URL
```

If disabled (default), the original plain text payload is sent. Block mode adds
structured sections for adds/removals/severity transitions while retaining a
concise fallback `text` field.

### QA Profile CI Job (New)

A new GitHub Actions workflow job `qa-profile` (added to
`prometheus-live-test-reusable.yml`) spins up a reduced QA stack using the
Docker Compose `qa` profile, runs smoke tests, produces taxonomy + resource
trend artifacts, and uploads them.

Artifacts emitted:

- `smoke_results.json` / `smoke_metrics.prom`
- `severity_runbook_dashboard.html`
- `taxonomy_dashboard_metrics.prom`
- `resource_usage.prom` + rolling `resource_usage.jsonl`

Trigger: same conditions as live tests unless `skip_live_tests` input is set to `'true'`.

Fast local reproduction:

```powershell
docker compose --profile qa up -d api prometheus grafana qa-smoke qa-orchestrator
python scripts/smoke_test.py
python scripts/severity_runbook_dashboard.py --taxonomy alerts_taxonomy.json --html severity_runbook_dashboard.html --prom taxonomy_dashboard_metrics.prom
python scripts/resource_usage_trend.py --jsonl trends/resource_usage.jsonl --prom trends/resource_usage.prom --window 120
docker compose --profile qa down -v
```

Integrators can now inspect QA artifacts early in PRs to catch alert coverage or
resource regression signals before full live tests.

## Focused Integration Test Mode (Traefik + Single Service)

When iterating on edge concerns (TLS routing, security headers) you can spin up
only Traefik and one platform service (e.g. the blockchain service) instead of

the full stack.

```powershell
cd c:\Users\romel\fullstack-ecosystem
# Build only what you need
docker compose -f docker-compose.platforms.yml up -d --build traefik blockchain-platform

# Run the HTTPS security headers integration test
python -m pytest tests\integration\test_security_headers.py::test_security_headers_present -q
```

### Why headers are now only in Traefik

Originally the FastAPI app also injected security headers. To avoid configuration
drift and duplicate logic, headers are now enforced exclusively at the edge via
Traefik middleware:

- Single source of truth for CSP / HSTS / framing / MIME sniffing protections.
- Easier to extend (e.g. add Permissions-Policy) without touching every service.
- Simplifies application code and reduces per-response overhead.

If a service must emit additional application-specific headers you can still
add narrow middleware there—keep global security posture centralized.

### Adding Another Service to the Minimal Set

Just append the service name(s):

```powershell
docker compose -f docker-compose.platforms.yml up -d --build traefik mlops-platform
```

### Common Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 404 with only X-Content-Type-Options | Router rule mismatch (Host / PathPrefix) | Ensure `Host(\`localhost\`) && PathPrefix(\`/blockchain\`)` label present |
| Missing CSP / HSTS | Wrong middleware chain | Verify `traefik.http.routers.<svc>.middlewares=security-headers,rate-limit` |
| TLS errors in test | Self-signed cert & requests verify | Test disables verification; ensure port 8445 (remapped from 8444) maps to entrypoint `websecure` |

### Future Hardening Ideas

- Pin base image digests post vulnerability scan workflow.
- Add automated header regression test for each onboarded service path.
- Introduce security headers versioning label to track changes over time.

## CI / Security Automation Additions

Recent automation added to enforce supply‑chain & edge security posture:

| Workflow | File | Purpose |
|----------|------|---------|
| Security Headers Matrix | `.github/workflows/security-headers-matrix.yml` | Verifies required headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) across multiple service paths in both direct (raw uvicorn) and Traefik edge modes. |
| Trivy Scan | `.github/workflows/trivy-scan.yml` | Builds platform image and fails PRs on HIGH/CRITICAL vulnerabilities (unfixed ignored). SARIF uploaded for code scanning UI. |
| Base Image Digest Pin | `.github/workflows/pin-base-image.yml` | Nightly job resolves the latest digest for `python:3.11-slim-bookworm`, updates `Dockerfile.platform` via automated PR. |
| Taxonomy Governance (enhanced) | `.github/workflows/taxonomy.yml` | Now includes concurrency guard + pip caching + externalized runbook completeness enforcement script. |

### Environment Variables (Security Headers Test)

`SECURITY_HEADER_URLS` – comma separated list of full URLs under test. Example
(direct mode):

```bash
SECURITY_HEADER_URLS="http://localhost:5205/blockchain,http://localhost:5208/mlops" pytest tests/integration/test_security_headers.py
```

### Adding Another Path To Header Coverage

1. Ensure service exposes a simple root (e.g. `/analytics`).
2. Add Traefik router + middleware chain labels (`security-headers,rate-limit`).
3. Append the new URL to `SECURITY_HEADER_URLS` in CI (or rely on future dynamic discovery logic).

### Vulnerability Noise Management

If Trivy flags vendor or base image issues you accept temporarily, add
identifiers to `.trivyignore` (created with commented examples). Always prefer
upgrading dependencies over ignoring.

### Negative Header Assertions

To prevent leaking framework/toolchain fingerprints, a negative test asserts
absence of headers like `Server`, `X-Powered-By` (unless intentionally
exposed). Extend `tests/integration/test_security_headers_negative.py` if new
disallowed headers are discovered.

### Supply Chain Flow

1. Nightly digest pin PR updates base image if digest changed & passes scan.
2. Trivy scan blocks HIGH/CRITICAL on PR branches.
3. Matrix header test guarantees edge + direct parity.
4. (Future) SCA dependency scan layer (e.g. pip-audit) can be added alongside
  Trivy.

### Quick Reference

| Concern | Tooling | Fails Build On |
|---------|---------|----------------|
| Edge Security Headers | Matrix workflow | Missing required header on any URL / mode |
| Vulnerabilities | Trivy | HIGH/CRITICAL (fix or ignore explicitly) |
| Base Image Drift | Digest pin workflow | (Informational PR, not blocking) |
| Alert Governance | Taxonomy workflow | Schema / lint / runbook completeness < threshold |

---
For deeper operational and governance details, see sections above and scripts under `scripts/`.

## Enterprise Readiness Snapshot

Status: ~90% functionally complete; remaining ~10% is polish & automation
hardening.

[![Alert Taxonomy Updated](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-taxonomy.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)

[![Alerts Total](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-total.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Deprecated Ratio](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-deprecated.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![30d Churn](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-alerts-churn.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)
[![Days Since Change](https://img.shields.io/endpoint?url=https://romel.github.io/fullstack-ecosystem/badge-taxonomy-age.json&cacheSeconds=300)](https://romel.github.io/fullstack-ecosystem/)

[View Full Alert Taxonomy (HTML)](https://romel.github.io/fullstack-ecosystem/)

### Delivered Pillars

- Canonical alert taxonomy (`alerts_taxonomy.json`) with JSON Schema validation.
- Coverage + scaffold + lint tooling (`sync_alert_taxonomy.py`) integrated in CI.
- Deprecation lifecycle: deprecated alerts removed from active Prometheus rules
  but preserved in taxonomy & dashboard (clearly marked).
- Multi-format artifact emission (Markdown, JSONL, HTML) via workflow.
- Advanced SLO / burn multi-window alert rules & supporting recording rules.
- Grafana dashboard: live JSON API table, severity color encoding, deprecated-only panel.
- Robust script behavior for empty rule groups (deprecation cleanup safe).

### In-Progress / Polishing Targets

- Enforce non-placeholder runbook & description (now lints; fill remaining
  TODOs).
- Add unit tests around taxonomy lint edge cases (optional hardening).
- Expand README linking to generated HTML taxonomy artifact (artifact published
  by CI as `taxonomy-docs`).
- (Optional) Add aging policy: warn if deprecated alert remains > N days.

### Success Criteria (Met)

- All active Prometheus alerts represented in taxonomy (CI `--check` passes).
- No invalid scope/category/severity values (enforced in lint).
- Deprecated alerts annotated in description and absent from active rule groups.
- Schema validation passes in workflow.

### Fast Follow Recommendations

1. Replace any remaining `TODO:` runbooks with actionable escalation steps.
2. Introduce a small pytest asserting placeholder detection (guards future regressions).
3. Publish HTML taxonomy to a static docs site (if desired) or link artifact badge here.
4. Add a churn metric (count new/removed alerts per commit) to surface alert noise.

This section will evolve as final polish steps are closed out.

## Alert Governance & Automation

The alert taxonomy lifecycle is continuously validated and published via automated workflows:

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| `taxonomy.yml` | Lint + schema validate + coverage check + changelog generation (artifact + optional commit append) | Pull Requests touching taxonomy or rules |
| `taxonomy-pages.yml` | Builds HTML taxonomy + Shields endpoint badges (last update, total, deprecated ratio) and publishes to `gh-pages` | Push to `main` affecting taxonomy/rules; manual dispatch |
| `taxonomy-weekly-audit.yml` | Strict aging audit (deprecated alerts past policy threshold fail) | Scheduled weekly cron |

### Lint Rules (Hard Fail vs Warning)

Hard fail conditions:

- Invalid scope / category / severity
- Placeholder description/runbook for active alerts
- Deprecated alert missing deprecation mention in description
- For/Windows mismatch
- Deprecated alert beyond age threshold when `TAXONOMY_DEPRECATION_STRICT=1`

Warning conditions (do not fail unless strict):

- Deprecated alert age > `TAXONOMY_DEPRECATION_MAX_DAYS` (when strict not enabled)

### Environment Variables

| Variable | Meaning | Default |
|----------|---------|---------|
| `TAXONOMY_DEPRECATION_MAX_DAYS` | Days before deprecated alert triggers warning/error | `0` (disabled) |
| `TAXONOMY_DEPRECATION_STRICT` | Treat aging over max days as hard error | `0` |

### Badges

Badges are generated via Shields endpoint mode and published on `gh-pages`:

- Last update: `badge-taxonomy.json`
- Total alerts: `badge-alerts-total.json`
- Deprecated ratio: `badge-alerts-deprecated.json`
- 30d churn (net add/remove set difference over last 30 days): `badge-alerts-churn.json`
- Risk churn (severity-weighted adds/removes; critical=5, high=3, medium=2, low=1): `badge-alerts-risk-churn.json`
- Stability (1 - churn/total): `badge-alerts-stability.json`
- Risk stability (severity-weighted stability): `badge-alerts-risk-stability.json`
- Runbook completeness (active alerts with non-placeholder runbook): `badge-runbook-completeness.json`
- Days since taxonomy change: `badge-taxonomy-age.json`

Badges are generated from JSON endpoints on GitHub Pages:

- Last update: `badge-taxonomy.json`
- Total alerts: `badge-alerts-total.json`
- Deprecated ratio: `badge-alerts-deprecated.json`

### Changelog

`generate_alerts_changelog.py` diffs current taxonomy vs prior commit and records:

- Added / removed alerts
- Modified core fields (group, severity, scope, category, description)
- Severity transitions (separate section)

Changes append to `ALERTS_CHANGELOG.md` on merge to main for durable history.

### Deprecation Lifecycle

1. Mark alert with `"deprecated": true` and `deprecated_since` (ISO8601 UTC)
2. Remove it from active Prometheus rule files (kept in taxonomy & dashboard)
3. Aging warnings remind cleanup or final removal after policy window

### Future Enhancements (Planned)

- Time-to-runbook-complete SLA tracking
- Automated risk anomaly detection (alert if risk churn exceeds threshold)

### New Governance Automation

- Daily history snapshots: `taxonomy-metrics-history.json` (plus per-day files
  under `metrics-history/`) enable Grafana time-series panels for churn, risk
  churn, runbook completeness.
- PR Delta Bot: `taxonomy-pr-delta.yml` comments on pull requests touching the
  taxonomy with additions, removals, modified fields, severity transitions,
  runbook delta, and risk churn weight.
- Runbook completeness enforcement: CI fails if `< 90%` completeness
  (configurable via `RUNBOOK_MIN_PERCENT`).
- Risk-weighted metrics: severity weights (critical=5/high=3/medium=2/low=1)
  drive risk-adjusted churn & stability, exposing noisy changes concentrated in
  higher-severity alerts.

### Repository Secrets Configuration

For enhanced CI/CD control, configure these repository secrets (fallbacks provided if unset):

| Secret Name | Purpose | Default |
|-------------|---------|---------|
| `RUNBOOK_MIN_PERCENT` | Minimum runbook completeness % required to pass CI | `90` |
| `MAX_CHURN_DELTA` | Maximum allowed churn_30d increase in trend regression tests | `5` |
| `MAX_RISK_CHURN_DELTA` | Maximum allowed risk_churn_30d increase in trend regression tests | `10` |
| `RISK_CHURN_SPIKE_THRESHOLD` | Fold-change threshold for risk churn anomaly detection | `2.0` |
| `RISK_CHURN_SPIKE_FAIL` | Whether anomaly detection exits non-zero (1) or warns (0) | `0` |

Configure via: Repository Settings → Secrets and variables → Actions → New repository secret.

### Live Recording Rule Test (Local)

To verify Prometheus recording rules materialize locally:

1. Start only the API and Prometheus services (faster than full stack):

   ```powershell
   cd c:\Users\romel\fullstack-ecosystem
   docker compose up -d --build api prometheus
   ```

2. Wait ~10–20s for initial rule evaluation cycles.

3. Run the focused integration test:

   ```powershell
   pytest -q tests/integration/test_prometheus_recording_rules_live.py
   ```

4. (Optional) Inspect series manually in Prometheus UI (<http://localhost:9090>) with queries:

   ```promql
   internal_service:failure_rate_5m
   internal_service:p99_latency_seconds_5m
   ```

5. Tear down when done:

   ```powershell
   docker compose down
   ```

Troubleshooting:

- If metrics are reported missing, ensure API `/metrics` is reachable and wait an extra evaluation
  interval (default scrape 15s). Re-run the test.
- Use `curl http://localhost:9090/api/v1/rules` to confirm rule groups loaded.
- Check API logs for internal sampler activity.
