# Packaging and Build Documentation

## Overview

This document covers the packaging and build process for the advanced backend application, including
special modes for development, testing, and production deployments.

## Build Modes and Environment Variables

### SAFE_MODE

Purpose: Disables complex security and authentication imports that may fail in frozen PyInstaller
environments.

Usage: `SAFE_MODE=1` (or `true`, `on`).

Effects:

- Stubs out autogen security middleware, JWT auth, rate limiting.
- Uses fallback implementations for complex auth flows.
- Enables basic health endpoints without full feature initialization.

### MINIMAL_MODE

Purpose: Avoids heavy ML/LLM library imports for fast startup and lean builds.

Usage: `MINIMAL_MODE=1` (or `true`, `on`).

Effects:

- Skips torch, tensorflow, sklearn, langchain, openai, anthropic imports.
- Stubs out heavy dependencies in backend modules.
- Maintains basic FastAPI functionality with early health endpoints.
- Dramatically reduces startup time and memory usage.

### TDigest Fallback

Purpose: Handles missing Cython extensions gracefully.

Mechanism: Detects when `accumulation_tree.abctree` is unavailable and swaps to a pure Python
adaptive reservoir percentile tracker.

Status Flag: `/health` returns `fallback_tdigest: true` when active.

## Trimmed Dependency Groups

| Group | Scope | Example Packages | When Needed | Excluded In Lean |
|-------|-------|------------------|-------------|------------------|
| Core | HTTP + Metrics + Auth Stubs | fastapi, uvicorn, pydantic, tdigest, prometheus_client, passlib, bcrypt | Always | No |
| ML | Local training / analytics | torch, numpy, scikit-learn, pandas | Model training & anomaly detection | Yes |
| LLM | External model orchestration | langchain, langchain_openai, langchain_anthropic, openai | Prompt / agent features | Yes |
| Vector / DB | Embeddings & stores | qdrant-client, redis | Semantic / cache features | Yes (optional) |
| Optional UX | YAML / file magic | pyyaml, python-magic / python-magic-bin | Dynamic registry & file type detection | Yes |

Build Matrix (illustrative):

| Mode | Core | ML | LLM | Vector | Optional |
|------|------|----|-----|--------|----------|
| Lean (MINIMAL_MODE=1) | ✅ | ❌ | ❌ | ❌* | ❌ |
| Full (dev) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prod API (no models) | ✅ | ❌ | ❌ | Optional | Optional |
| Hybrid (LLM only) | ✅ | ❌ | ✅ | Optional | Optional |

*Vector layer can be reintroduced without full ML stack if embeddings are remote.

## ML Mode Validation Steps

To verify a full (non-lean) ML + LLM environment:

1. Ensure MINIMAL_MODE is unset: `set MINIMAL_MODE=0` (Windows) or `unset MINIMAL_MODE`.
2. Install extras: `pip install .[ml,llm]` or both requirements files.
3. Start service: `python -m autogen.advanced_backend` or packaged exe (without MINIMAL_MODE).
4. Check logs for `HEAVY_DEPENDENCIES_STATUS { ... }` line — all `true` for expected modules.
5. Hit `/__phase` (should show `minimal_mode: false`).
6. Trigger a simple endpoint using LLM features (if exposed) or run an internal import probe:

   ```bash
   python -c "import torch, sklearn, langchain, openai; print('ML MODE OK')"
   ```

7. (Optional) Confirm memory footprint increase relative to lean build.

Failure Handling:

- A missing heavy module logs a JSON status with `false` for that key.
- You can selectively re-install a category (e.g., `pip install torch --upgrade`).

## Build Process

### Standard Build

```bash
pip install -r requirements.txt
pyinstaller --onefile bootstrap_entry.py --name advanced_backend_boot \
  --add-data "executive_dashboard.html;." \
  --hidden-import tdigest --hidden-import accumulation_tree
```

### Lean Build (Recommended)

```bash
python -m venv venv_lean
venv_lean\Scripts\activate
pip install fastapi uvicorn pydantic python-multipart tdigest prometheus_client passlib bcrypt
pyinstaller --onefile bootstrap_entry.py --name advanced_backend_lean \
  --add-data "executive_dashboard.html;." \
  --hidden-import tdigest --hidden-import accumulation_tree \
  --hidden-import prometheus_client --hidden-import passlib --hidden-import bcrypt \
  --exclude-module torch --exclude-module tensorflow --exclude-module sklearn \
  --exclude-module langchain --exclude-module openai --exclude-module anthropic
```

### Optional Dependencies

```bash
# ML group
pip install -r requirements-ml.txt

# LLM group
pip install -r requirements-llm.txt

# Unified (pyproject extras)
pip install .[ml,llm]
```

## Build Files

### bootstrap_entry.py

Purpose: Minimal PyInstaller entrypoint.

Features:

- Sets SAFE_MODE early.
- Avoids heavy top-level imports.
- Runs Uvicorn programmatically.
- Handles frozen executable detection.

### advanced_backend.py

Purpose: Main FastAPI application with all features.

Architecture:

- Early health endpoints before heavy imports.
- Conditional import structure based on SAFE_MODE/MINIMAL_MODE.
- TDigest fallback implementation.
- Dashboard HTML serving.
- Heavy dependency probe logging: `HEAVY_DEPENDENCIES_STATUS {...}`.

## Diagnostic Endpoints

### /health

Purpose: Basic health check.

Response: `{"status": "ok", "phase": "early" | "runtime", "minimal": bool, "fallback_tdigest": bool}`

Availability: Always responds, even during heavy import delays.

### /__phase

Purpose: Detailed system state.

Response: Mode flags, TDigest status, tracked endpoints.

Usage: Debug startup issues and mode detection.

## Testing Builds

### Smoke Test Commands

```bash
# Standard build
advanced_backend_boot.exe
curl http://localhost:8000/health
curl http://localhost:8000/__phase

# Lean build
set MINIMAL_MODE=1
advanced_backend_lean.exe
curl http://localhost:8000/health
```

### Validation Checklist

- [ ] Executable builds without errors
- [ ] /health responds < 5s
- [ ] /__phase shows correct mode flags
- [ ] Dashboard serves at /executive_dashboard.html
- [ ] No silent crashes
- [ ] Memory usage appropriate (lean ~50MB, full ~200MB+)

## Troubleshooting

### Common Issues

**"Module not found" errors**: Add `--hidden-import` for missing dependencies
**Silent crashes**: Enable SAFE_MODE=1 and check logs

---

## (Added) Current Build Results Snapshot (2025-10-05)

| Variant | Path | Type | Approx Size | HEAVY_DEPENDENCIES_STATUS Seen | Notes |
|---------|------|------|-------------|--------------------------------|-------|
| Lean | `dist/advanced_backend_lean.exe` | onefile | ~17 MB | (probe skipped – MINIMAL_MODE) | Fast startup, excludes ML/LLM libs |
| Full (onefile) | `dist/advanced_backend_full.exe` | onefile | ~27.5 MB | All false (torch/tf/sklearn/langchain/openai/anthropic) | Large libs not bundled; SAFE_MODE auth fallback |
| Full (onedir) | `dist/advanced_backend_full_onedir/advanced_backend_full_onedir/advanced_backend_full_onedir.exe` | onedir | Hundreds MB (full libs) | {"torch": true, "tensorflow": false, "sklearn": true, "langchain": true, "openai": true, "anthropic": true} | Recommended for ML/LLM features |

### Interpretation

- The single-file approach did not successfully embed heavy ML libraries; use onedir for feature-complete distribution.
- TensorFlow remains absent (not installed or intentionally excluded); add it only if required (large footprint).
- `jwt` / `jwt_auth_service` missing triggered SAFE_MODE (auth & rate limit skipped). Install / include JWT components to
  enable security stack.
- TDIGEST fallback engaged due to missing `accumulation_tree.abctree` – acceptable unless precise quantiles needed.

### Rebuild Reference Commands

Lean:

```powershell
pyinstaller --onefile bootstrap_entry.py --name advanced_backend_lean --add-data "executive_dashboard.html;." `
  --hidden-import tdigest --hidden-import accumulation_tree --hidden-import prometheus_client `
  --hidden-import passlib --hidden-import bcrypt `
  --exclude-module torch --exclude-module tensorflow --exclude-module sklearn `
  --exclude-module langchain --exclude-module openai --exclude-module anthropic
```

Full (onefile attempt):

```powershell
pyinstaller --onefile bootstrap_entry.py --name advanced_backend_full --add-data "executive_dashboard.html;." `
  --hidden-import accumulation_tree --hidden-import prometheus_client --hidden-import passlib `
  --hidden-import bcrypt --hidden-import magic
```

Full (onedir – recommended):

```powershell
pyinstaller bootstrap_entry.py --name advanced_backend_full_onedir --add-data "executive_dashboard.html;." `
  --hidden-import accumulation_tree --hidden-import torch --hidden-import sklearn --hidden-import langchain `
  --hidden-import openai --hidden-import anthropic --hidden-import tiktoken --hidden-import transformers `
  --distpath dist/advanced_backend_full_onedir --noconfirm
```

### Suggested Next Enhancements

- Add a `/ml-capabilities` endpoint returning the probe JSON.
- Provide a PowerShell script `scripts/package_full_ml.ps1` automating onedir build & optional pruning.
- Bundle JWT auth libs (e.g., `pyjwt`) to eliminate SAFE_MODE fallback when security features are required.
- Optionally compile / include `accumulation_tree` Cython module for production percentile accuracy.

### New: /ml-capabilities Endpoint

The backend now exposes `GET /ml-capabilities` which returns:

```json
{
  "minimal_mode": false,
  "safe_mode": false,
  "include_tensorflow_flag": null,
  "heavy_dependencies": {
     "torch": true,
     "sklearn": true,
     "langchain": true,
     "openai": true,
     "anthropic": true,
     "tensorflow": false
  },
  "tdigest_fallback": false,
  "tdigest_tracked_endpoints": []
}
```

Use this to verify a deployed package has required ML/LLM capabilities without tailing stderr for the PHASE line.

### New: PowerShell Build Script

`scripts/package_full_ml.ps1` automates a full onedir build with optional TensorFlow.

Examples:

```powershell
# Clean rebuild without TensorFlow
./scripts/package_full_ml.ps1 -Clean

# Include TensorFlow (large!)
./scripts/package_full_ml.ps1 -IncludeTensorFlow

# Custom name
./scripts/package_full_ml.ps1 -Name enterprise_full -Clean
```

Outputs the exe at `dist/<Name>/<Name>.exe`. After running, hit:

```powershell
Invoke-RestMethod http://localhost:8000/ml-capabilities | ConvertTo-Json -Depth 5
```

TensorFlow is intentionally omitted unless `-IncludeTensorFlow` or environment variable `INCLUDE_TENSORFLOW=1` is set.

### New: Automated Capability Test Script

`scripts/test_ml_capabilities.ps1` will:

1. Auto-select a full onedir exe, lean exe, or fall back to uvicorn.
2. Wait for `/health` (default port 8070 or override with `-Port`).
3. Fetch `/ml-capabilities` and pretty-print JSON (if available).
4. Optionally write JSON to file with `-OutputJson path`.

Examples:

```powershell
# Default auto-detect (port 8070)
./scripts/test_ml_capabilities.ps1

# Specify executable & port
./scripts/test_ml_capabilities.ps1 -ExePath dist/advanced_backend_full_onedir/advanced_backend_full_onedir.exe -Port 9001

# Save JSON
./scripts/test_ml_capabilities.ps1 -OutputJson capabilities.json
```

Return codes:

- 0 success (health ok, capabilities retrieved or gracefully skipped in lean)
- 2 health never became ready

---

**Slow startup**: Use MINIMAL_MODE=1 or lean build approach
**Large executable size**: Exclude heavy modules or use lean environment

### Debug Mode

```bash
set SAFE_MODE=1
set MINIMAL_MODE=1
advanced_backend_boot.exe
```

### Import Analysis

```bash
pip install pipdeptree
pipdeptree --packages torch,langchain,sklearn
```

## Production Deployment

### Recommended Configuration

- Lean build for containers/serverless.
- SAFE_MODE for security middleware isolation.
- MINIMAL_MODE for API-only deployments.
- Full build only when ML/LLM features are required.

### Container Builds

```dockerfile
FROM python:3.13-slim
COPY advanced_backend_lean.exe /app/
ENV MINIMAL_MODE=1
ENV SAFE_MODE=1
CMD ["/app/advanced_backend_lean.exe"]
```

## Performance Characteristics

| Mode | Startup Time | Memory Usage | Executable Size | Features |
|------|-------------|--------------|-----------------|----------|
| Full | 10-30s | 200-500MB | 400MB+ | All features |
| MINIMAL_MODE | 2-5s | 50-100MB | 400MB+ | Core API only |
| Lean Build | 1-3s | 30-80MB | 50-100MB | Core API + metrics |

## Development Workflow

1. Feature Development: full env.
2. Testing: MINIMAL_MODE for fast iteration.
3. Staging: lean build to simulate production.
4. Production: lean or hybrid depending on feature set.

## PowerShell Helper Commands

```powershell
# Lean rebuild
python -m venv venv_lean
venv_lean\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic python-multipart tdigest prometheus_client passlib bcrypt
pyinstaller --onefile bootstrap_entry.py --name advanced_backend_lean \
  --add-data "executive_dashboard.html;." \
  --hidden-import tdigest --hidden-import accumulation_tree \
  --hidden-import prometheus_client --hidden-import passlib --hidden-import bcrypt \
  --exclude-module torch --exclude-module tensorflow --exclude-module sklearn \
  --exclude-module langchain --exclude-module openai --exclude-module anthropic

# Run lean exe
set MINIMAL_MODE=1
dist\advanced_backend_lean.exe

# Full ML/LLM install (from project root)
pip install .[ml,llm]
set MINIMAL_MODE=0
python -m autogen.advanced_backend
```

## Newly Added Operational Enhancements (2025-10-06)

### Endpoints

| Endpoint | Method | Purpose | Auth | Notes |
|----------|--------|---------|------|-------|
| `/ml-capabilities` | GET | Report heavy dependency availability & mode flags | None | Lean build may omit or show all false. |
| `/__phase` | GET | Unified phase / mode diagnostics (minimal, safe, tdigest) | None | De-duplicated from earlier dual implementation. |
| `/startup/heartbeat` | GET | Returns recent startup PHASE events ring buffer | None | Useful for container cold-start observability. |
| `/admin/adaptive/reset` | POST | Clears ALL adaptive latency state & t-digests | Admin or token | Supports fallback token in SAFE_MODE (see below). |
| `/api/v2/latency/quantiles` | GET | Empirical p50/p90/p95/p99 for adaptive window | None | Populated only after adaptive samples accrue. |
| `/api/v2/latency/distribution` | GET | Distribution + EMA p95 + class proportions | None | Adaptive SLO engine required. |

#### Admin Reset Security Model

In normal mode, `/admin/adaptive/reset` requires admin auth (FastAPI dependency `require_admin`).
If `SAFE_MODE` is active or JWT auth unavailable, you can still protect the reset via:

```
set ADMIN_RESET_TOKEN=supersecret
```

Then invoke:

```
curl -X POST "http://localhost:8000/admin/adaptive/reset?secret=supersecret"
```

If token mismatch, HTTP 401 is returned. Omit the env var to allow open (development-only) resets.

### Phase / Heartbeat Buffer

The application now records up to the last 200 PHASE events in-memory. `/startup/heartbeat` exposes the most recent N (default 50). This enables:

- Post-mortem analysis for slow starts
- Confirming whether TDIGEST fallback or SAFE_MODE triggered
- Container readiness dashboards

Example:

```json
{
  "events": [ { "t_ms": 12.7, "msg": "INIT: MINIMAL_MODE active" }, ... ],
  "count": 50,
  "uptime_seconds": 34.228,
  "minimal_mode": true,
  "safe_mode": false
}
```

### New Scripts

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `scripts/package_full_ml.ps1` | Full onedir ML build | `-IncludeTensorflow`, `-Name` |
| `scripts/test_ml_capabilities.ps1` | Health + `/ml-capabilities` probe | `-ExePath`, `-Port`, `-OutputJson` |
| `scripts/license_cve_scan.ps1` | License inventory + CVE scan | `-FailOnHigh` |
| `scripts/package_full_onefile_experiment.ps1` | Experimental single-file heavy build | `-IncludeTensorflow`, `-Name` |
| `scripts/load_test_latencies.ps1` | Burst + steady latency sampling | `-DurationSeconds`, `-Concurrency` |
| `scripts/smoke_replay_failures.ps1` | Replay core endpoints & capture failures | `-BaseUrl` |

### CI Workflow

`.github/workflows/capabilities.yml` executes a lean build on `ubuntu-latest` and
`windows-latest`, launches the executable, probes `/health`, and captures
`/ml-capabilities` (soft-failing if absent in lean). Artifacts include
`capabilities.json` per OS.

To extend with a nightly heavy build, uncomment the `full-ml-capabilities` job
and ensure heavy dependencies are cached or installed (cost & time trade-offs).

### CI Scheduled Scan

We added a scheduled workflow that runs daily to collect license and CVE reports.
It is available at `.github/workflows/license_cve_scan.yml` and executes
`scripts/license_cve_scan.ps1` on a Windows runner. The workflow uploads the
`build-reports/` directory as an artifact named `license-cve-scan-reports`.

How to interpret the reports:

- `build-reports/licenses.json` contains `piplicenses` output with package
  licenses and versions.

- `build-reports/safety_report.json` contains `safety` scan JSON with CVE
  information. Use `-FailOnHigh` to make the workflow fail on high-severity
  findings.

You can run the scan manually from the Actions UI using `workflow_dispatch` or
inspect the artifacts from scheduled runs.

### Load & Smoke Testing

1. Start service (lean or full).
2. Run: `./scripts/load_test_latencies.ps1 -DurationSeconds 30 -Concurrency 16`.
3. Inspect `load_test_summary.json` for quantiles and success rates.
4. Optionally clear adaptive state between runs: `curl -X POST http://localhost:8000/admin/adaptive/reset`.
5. Run smoke: `./scripts/smoke_replay_failures.ps1` (produces `smoke_failures.json`).

### Onefile Full ML Experiment

Heavy ML stacks often exceed practical limits for single-file embedding. Extraction
time can be long and some AV products may interfere. The script attempts the
experiment, but prefer `onedir` for production stability:

```powershell
./scripts/package_full_onefile_experiment.ps1 -IncludeTensorflow
```

Review `experiment_onefile_full_ml.log` and verify `/ml-capabilities` before adopting.

### Security Notes

- Always set `ADMIN_RESET_TOKEN` in any shared or remote environment when SAFE_MODE or unauthenticated mode is in effect.
- Consider integrating `license_cve_scan.ps1` into nightly CI with `-FailOnHigh` once baseline vulnerabilities are triaged.
- For production packaging, include PyJWT to avoid SAFE_MODE auth fallback and ensure rate limiting middleware loads.

### Future Ideas (Post Enhancement Set)

- Export heartbeat events to Prometheus as a gauge + info metric.
- Include a rolling error rate in the dashboard sourced from middleware hooks.
- Add structured logging toggle for JSON output (`STRUCTURED_LOG=1`).
