# Quantile Benchmark & Metrics Cache Performance

This document describes how to run, persist, and interpret the histogram quantile
benchmark tooling that evaluates the caching optimization layers.

## Components

| File | Purpose |
|------|---------|
| `scripts/benchmark_metrics_quantiles.py` | Runs two phases (cache enabled vs disabled) and records timings |
| `scripts/aggregate_quantile_benchmarks.py` | Aggregates multiple JSON runs, producing Markdown + JSON summary |
| `scripts/load_env.py` | Minimal .env loader so no external dependency required |
| `.env.example` | Template for configuring cache toggle, artifacts directory, speedup thresholds |
| `scripts/prepare_env.ps1` | Quick rehydration script after restart |
| `.github/workflows/benchmark-comment.yml` | PR workflow posting benchmark summary comment |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISABLE_METRIC_CACHE` | Force-disable cache when `1` for disabled timing phase comparisons | `0` |
| `BENCH_COMMIT` | Override commit hash for local runs (else auto-detect via git) | _auto_ |
| `BENCH_ARTIFACT_DIR` | Directory for JSON outputs | `artifacts` |
| `BENCH_MIN_SPEEDUP` | Optional gating threshold (not enforced by default) | `1.05` |
| `BENCH_ROLLING_WINDOW` | Rolling window size for aggregation smoothing | `5` |

## Running Locally (PowerShell)

```powershell
# Prepare environment (loads .env and creates artifacts dir)
powershell -ExecutionPolicy Bypass -File scripts/prepare_env.ps1

# Run a benchmark and store JSON
$ts = Get-Date -Format yyyyMMdd_HHmmss
python scripts/benchmark_metrics_quantiles.py --json-out artifacts/quantile_bench_$ts.json

# Aggregate all runs
python scripts/aggregate_quantile_benchmarks.py --input-glob "artifacts/quantile_bench_*.json" --json-out artifacts/aggregate.json --markdown-out artifacts/aggregate.md
```

## Interpreting Results

- `batch_speedup`: (disabled_mean / enabled_mean) for batch quantile path. >1 indicates cache + batch path is faster.
- Rolling means help smooth out outliers in CI.
- Sparklines show trend evolution visually; flat = stable performance.
- Per-phase distribution statistics (mean, median, variance, stdev, percentiles) help distinguish systematic
  regressions (shift of p50 & p90) from noise (only stdev increase) or tail-only issues (p95/p99 spike while
  p50 remains stable).

### Phase Statistical Fields

Each phase object in the raw per-run JSON now includes:

| Field | Units | Meaning |
|-------|-------|---------|
| `mean_seconds` | seconds | Arithmetic mean of samples |
| `median_seconds` | seconds | 50th percentile (same as p50) |
| `min_seconds` | seconds | Fastest observed sample |
| `max_seconds` | seconds | Slowest observed sample |
| `variance_seconds` | seconds^2 | Population variance (not sample) |
| `stdev_seconds` | seconds | Standard deviation (sqrt of population variance) |
| `p50_ms` | milliseconds | 50th percentile (alias of median) in ms for convenient reading |
| `p90_ms` | milliseconds | 90th percentile latency |
| `p95_ms` | milliseconds | 95th percentile latency |
| `p99_ms` | milliseconds | 99th percentile latency |

Notes:

- Percentile values are computed via linear interpolation over the sorted sample list.
- `variance_seconds` uses the population definition (dividing by N) because we treat the collected samples as the
  full set for the run context.

## Persisting History

- Individual JSON artifacts are gitignored to prevent repository bloat.
- Curate important milestones by copying selected files into a tracked folder (e.g., `benchmarks_history/`).
- For long-lived trending across PRs, add an Actions cache to restore prior artifacts (already scaffold-ready).

### Public Badges & Published Artifacts

Nightly CI publishes machine-readable badge JSON and aggregation outputs to the `gh-pages` branch under `benchmark/`.

Replace `<user_or_org>` and `<repo>` below with your GitHub namespace and repository name.

Embed these Shields badges in your README (a third badge for the best observed batch speedup is also available):

```markdown
![Batch Speedup](https://img.shields.io/endpoint?url=https://<user_or_org>.github.io/<repo>/benchmark/batch_speedup_badge.json)
![Individual Speedup](https://img.shields.io/endpoint?url=https://<user_or_org>.github.io/<repo>/benchmark/individual_speedup_badge.json)
![Best Batch Speedup](https://img.shields.io/endpoint?url=https://<user_or_org>.github.io/<repo>/benchmark/best_speedup_badge.json)
```

Raw endpoints:

```text
https://<user_or_org>.github.io/<repo>/benchmark/batch_speedup_badge.json
https://<user_or_org>.github.io/<repo>/benchmark/individual_speedup_badge.json
https://<user_or_org>.github.io/<repo>/benchmark/best_speedup_badge.json
https://<user_or_org>.github.io/<repo>/benchmark/aggregate.json
https://<user_or_org>.github.io/<repo>/benchmark/aggregate.md
```

Notes:

- Shields may cache responses; append a dummy query like `?t=YYYYMMDDHH` if forcing a refresh.
- `aggregate.json` includes the latest measurements and historical series for external tooling.
- `aggregate.md` is a rendered snapshot (rolling averages + sparklines) for quick manual inspection.
- `best_speedup_badge.json` reflects the maximum historical batch speedup observed in retained artifacts.

### aggregate.json Structure (Schema Snippet)

Below is an informal JSON Schema-style fragment describing `aggregate.json` (simplified for readability). Newly
added fields for per-phase statistics are included. Backward compatibility is preserved; consumers can
feature-detect `phase_stats_by_run`.

```json
{
  "latest": { ... },
  "entries": [ { ... } ],
  "rolling_window": 5,
  "count": 23,
  "batch_sparkline": "string",
  "individual_sparkline": "string",
  "phase_stats_by_run": [
    {
      "source_file": "artifacts/quantile_bench_20250918_101500.json",
      "commit_hash": "abc1234",
      "timestamp": "2025-09-18T10:15:00Z",
      "phases": {
        "initial_batch": {
          "mean_ms": 1.23,
          "median_ms": 1.20,
          "min_ms": 1.10,
          "max_ms": 1.40,
          "variance_ms2": 0.0045,
          "stdev_ms": 0.067,
          "p50_ms": 1.20,
          "p90_ms": 1.32,
          "p95_ms": 1.35,
          "p99_ms": 1.39
        },
        "disabled_batch": { "...": "same structure" },
        "initial_individual": { "...": "same structure" },
        "disabled_individual": { "...": "same structure" }
      }
    }
  ],
  "latest_phase_stats": { "...": "shortcut to last element of phase_stats_by_run" }
}
```

Recent additions:

- `rolling_phase_percentiles`: Rolling mean of p50/p90/p95/p99 (ms) for each phase using the configured rolling window.
- `guardrails`: Array of evaluated guardrail checks (present only when guardrail flags are used).
- `svg_percentiles`: Filename of generated percentile trend SVG if `--svg-out` was used.

Example guardrail entry:

```json
{
  "type": "p95_increase",
  "phase": "initial_batch",
  "latest_ms": 1.34,
  "rolling_mean_ms": 1.22,
  "max_allowed_ms": 1.342,  
  "factor": 1.10,
  "status": "pass"
}
```

Field Notes:

- `phase_stats_by_run` order matches `entries` order (chronological after sorting by timestamp / filename
  heuristics).
- `latest_phase_stats` is a convenience alias to avoid linear scans client-side.
- `variance_ms2` is variance in (ms)^2 — multiply stdev squared to verify.

### Using Percentiles Effectively

Common regression signatures:

- Mean & p50 stable, p95/p99 increase: emerging tail latency issue (watch for intermittent contention or GC
  pauses).
- Mean increases, p50 & p95 both shift: broad regression likely from algorithmic change or disabled optimization.
- Variance & stdev spike while percentiles mostly stable: noisy environment (CPU throttling / noisy neighbor);
  re-run before acting.

Suggested lightweight guardrails (future enhancements):

- Alert if `latest.initial_batch.p95_ms` > (rolling_p95 * 1.10) over last N runs.
- Track a rolling stdev and flag if it doubles (instability indicator).

### Guardrail Flags

The aggregator supports optional guardrail exit codes (non-zero) to fail early in CI when latency distribution degrades:

| Flag | Exit Code on Fail | Description |
|------|-------------------|-------------|
| `--max-p95-increase <factor>` | 3 | Fail if latest p95 > rolling_p95 * factor |
| `--max-p99-increase <factor>` | 4 | Fail if latest p99 > rolling_p99 * factor |
| `--max-stdev-multiplier <mult>` | 5 | Fail if latest stdev > rolling_stdev * mult |
| `--guardrail-phase <label>` | n/a | Phase label (default `initial_batch`) |

Multiple guardrails can be combined; first failure determines exit code.

### Percentile Trend SVG

Add `--svg-out artifacts/percentiles.svg` to produce an embeddable inline SVG plot (lines for p50/p90/p95/p99)
used in the PR comment (base64 data URI). This is lightweight (no external deps) and intended for quick
visual tail-drift inspection.

### Rolling Percentiles

`rolling_phase_percentiles` object:

```json
{
  "initial_batch": {
    "p95": { "latest_ms": 1.35, "rolling_mean_ms": 1.29 },
    "p99": { "latest_ms": 1.42, "rolling_mean_ms": 1.38 }
    // p50, p90 similar structure
  },
  "disabled_batch": { "...": "..." }
}
```

Use these to compare instantaneous vs smoothed distribution shifts.

## CI PR Comment

The workflow posts a table with:

- Commit hash (short)
- Current speedups and deltas
- Rolling averages
- Full sparkline trend
- Link to published dashboard (nightly)

### PR Badge & Best Speedup in Comment

During PR runs, three badge JSON artifacts are generated (batch, individual, best) and attached as
workflow artifacts. The PR comment also lists:

- Latest batch speedup (current run)
- Best historical batch speedup (max across cached artifacts)
- Individual speedup explicitly

Once the nightly job publishes badges to `gh-pages`, the embedded README / comment markdown badge URLs will render automatically.

## Adding a Speedup Gate

Add `--min-speedup-warn <value>` to the aggregate step and optionally fail the job if exit code `2`.

Example snippet:

```yaml
- name: Aggregate with gate
  run: |
    python scripts/aggregate_quantile_benchmarks.py --input-glob "artifacts/quantile_bench_*.json" \
      --json-out artifacts/aggregate.json \
      --markdown-out artifacts/aggregate.md \
      --min-speedup-warn 1.05
```

### Nightly Regression Gate

The nightly workflow also enforces a regression gate (default threshold `1.05`, overridable via repository
variable `BENCH_MIN_SPEEDUP`). If the latest `batch_speedup` falls below the threshold the job fails, providing
early detection outside of PR context. This helps surface performance drift from background changes or
dependency updates.

## Restart Checklist

1. Run `scripts/prepare_env.ps1`.
2. (Optional) Activate virtual environment.
3. Run benchmark and aggregation.
4. Review `artifacts/aggregate.md` for regressions.

## Safe Shutdown Helper

Use `scripts/safe_shutdown.ps1` to capture a snapshot before powering off:

```powershell
# Dry run (no write, no shutdown)
powershell -ExecutionPolicy Bypass -File scripts/safe_shutdown.ps1 -DryRun

# Aggregate benchmarks, commit & push, then prompt for shutdown
powershell -ExecutionPolicy Bypass -File scripts/safe_shutdown.ps1 -Aggregate -Commit -Push

# Non-interactive (force) with aggregation + commit only
powershell -ExecutionPolicy Bypass -File scripts/safe_shutdown.ps1 -Aggregate -Commit -Force
```

Options:

| Flag | Effect |
|------|--------|
| `-Aggregate` | Runs aggregation if benchmark artifacts exist |
| `-Commit` | Stages & commits changes if any present |
| `-Push` | Pushes current branch when a commit was just created |
| `-BackupDir <dir>` | Location for ZIP snapshots (default `backups/`) |
| `-DryRun` | Log actions only, skip writes & shutdown |
| `-Force` | Skip confirmation prompt before shutdown |

The script creates a ZIP like `backups/snapshot_YYYYMMDD_HHMMSS.zip` containing key directories.

## Troubleshooting

| Symptom | Possible Cause | Fix |
|---------|----------------|-----|
| `ImportError: prometheus_client` | Dependency missing | `pip install -r requirements.txt` |
| Empty aggregation | Glob pattern mismatch | Verify `artifacts/quantile_bench_*.json` exists |
| All speedups ~1.00x | Cache disabled globally | Ensure `DISABLE_METRIC_CACHE=0` in `.env` |
| Sparklines flat zeros | Missing or single data point | Generate more benchmark runs |
| Percentiles all null | Older run file (pre-upgrade) | Re-run benchmark to populate new fields |

## Next Ideas

- Persist history via GitHub Cache or a dedicated branch
- Generate SVG chart from JSON (optional enhancement)
- Multi-metric support if more benchmarks are added
- Add percentile-based regression guards (p95 / p99)
