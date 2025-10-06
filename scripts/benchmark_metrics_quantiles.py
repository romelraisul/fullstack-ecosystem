"""Benchmark histogram quantile approximation helpers with and without cache.

This script exercises the approximate_histogram_quantile(s) utilities in
`tests.utils.metrics` to provide a quick local signal on performance impact
of the caching layer. It purposefully avoids external benchmark frameworks
(pytest-benchmark) to stay dependency‑light for CI / ad‑hoc runs.

Usage (PowerShell examples):
  python scripts/benchmark_metrics_quantiles.py
  $env:DISABLE_METRIC_CACHE="1"; python scripts/benchmark_metrics_quantiles.py; remove-item Env:DISABLE_METRIC_CACHE

It will run two phases automatically:
  1. Warm phase (cache enabled) unless DISABLE_METRIC_CACHE=1
  2. Forced disabled cache phase (env override) in-process for comparison

Outputs a small JSON blob with timings and relative speedups.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any

from prometheus_client import CollectorRegistry, Histogram

# Optional .env loading (best-effort, avoids dependency on python-dotenv)
try:  # pragma: no cover - simple convenience
    from scripts.load_env import load_env as _load_env

    _load_env()
except Exception:  # noqa: BLE001
    pass

# Import helpers (runtime import path relies on project layout). If this fails
# user likely needs to adjust PYTHONPATH or run from repo root.
from tests.utils.metrics import (
    approximate_histogram_quantile,
    approximate_histogram_quantiles,
    clear_metric_cache,
)


@dataclass
class PhaseResult:
    label: str
    iterations: int
    samples_per_iteration: int
    quantiles_requested: int
    total_seconds: float
    min_seconds: float
    max_seconds: float
    mean_seconds: float
    median_seconds: float
    variance_seconds: float
    stdev_seconds: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float


@dataclass
class BenchmarkSummary:
    cache_env_initial: str
    phases: list[PhaseResult]
    relative_speedup_vs_disabled: dict[str, float]
    commit_hash: str | None = None


def _detect_commit_hash() -> str | None:
    """Attempt to obtain a commit hash.

    Precedence:
      1. BENCH_COMMIT env var
      2. GITHUB_SHA env var (GitHub Actions)
      3. `git rev-parse --short HEAD`
    Returns None if all attempts fail.
    """
    for key in ("BENCH_COMMIT", "GITHUB_SHA"):
        v = os.environ.get(key)
        if v:
            return v[:12]
    try:  # pragma: no cover - depends on git availability
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        if out:
            return out
    except Exception:  # noqa: BLE001 - broad by design
        return None
    return None


def _build_registry(num_observations: int, buckets: list[float]) -> CollectorRegistry:
    reg = CollectorRegistry()
    h = Histogram(
        "benchmark_latency_seconds",
        "Synthetic latency histogram for benchmark",
        buckets=buckets,
        registry=reg,
    )
    # Populate some values across bucket ranges.
    for i in range(num_observations):
        # Distribute linearly across buckets range for simplicity.
        v = buckets[0] + (buckets[-2] * (i / max(1, num_observations - 1)))  # exclude +Inf sentinel
        h.observe(v)
    return reg


def _time_once(reg: CollectorRegistry, quantiles: list[float], batch: bool) -> None:
    # We call generate_latest only once per timing run so parsing overhead is representative.
    # (approximate_histogram_quantile* functions accept registry and will call generate_latest internally.)
    # Force clear cache between iterations for the disabled phase only by env variable toggling externally.
    if batch:
        approximate_histogram_quantiles(reg, "benchmark_latency_seconds", quantiles)
    else:
        for q in quantiles:
            approximate_histogram_quantile(reg, "benchmark_latency_seconds", q)


def _run_phase(
    label: str, iterations: int, reg: CollectorRegistry, quantiles: list[float], batch: bool
) -> PhaseResult:
    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        _time_once(reg, quantiles, batch=batch)
        timings.append(time.perf_counter() - start)
    timings_sorted = sorted(timings)

    def _percentile(p: float) -> float:
        if not timings_sorted:
            return 0.0
        k = (len(timings_sorted) - 1) * p
        f = int(k)
        c = min(f + 1, len(timings_sorted) - 1)
        if f == c:
            return timings_sorted[f]
        return timings_sorted[f] + (timings_sorted[c] - timings_sorted[f]) * (k - f)

    variance = statistics.pvariance(timings) if len(timings) > 1 else 0.0
    stdev = variance**0.5
    return PhaseResult(
        label=label,
        iterations=iterations,
        samples_per_iteration=1,
        quantiles_requested=len(quantiles) if batch else 1,
        total_seconds=sum(timings),
        min_seconds=min(timings),
        max_seconds=max(timings),
        mean_seconds=statistics.fmean(timings),
        median_seconds=statistics.median(timings),
        variance_seconds=variance,
        stdev_seconds=stdev,
        p50_ms=_percentile(0.50) * 1000.0,
        p90_ms=_percentile(0.90) * 1000.0,
        p95_ms=_percentile(0.95) * 1000.0,
        p99_ms=_percentile(0.99) * 1000.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark histogram quantile approximation helpers"
    )
    parser.add_argument(
        "--iterations", type=int, default=25, help="Iterations per phase (default: 25)"
    )
    parser.add_argument(
        "--json-out", type=str, default=None, help="If set, write JSON summary to this path"
    )
    args = parser.parse_args()

    initial_env = os.environ.get("DISABLE_METRIC_CACHE", "0")
    buckets = [0.01, 0.02, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]
    reg = _build_registry(num_observations=5000, buckets=buckets)

    quantiles = [0.5, 0.75, 0.9, 0.95, 0.99]

    iterations = args.iterations

    phases: list[PhaseResult] = []

    # Phase 1: whatever the user started with (likely cache enabled)
    clear_metric_cache()
    phases.append(_run_phase("initial_batch", iterations, reg, quantiles, batch=True))
    clear_metric_cache()
    phases.append(_run_phase("initial_individual", iterations, reg, quantiles[:1], batch=False))

    # Phase 2: force disabled cache for comparison (in same process)
    os.environ["DISABLE_METRIC_CACHE"] = "1"
    clear_metric_cache()
    phases.append(_run_phase("disabled_batch", iterations, reg, quantiles, batch=True))
    clear_metric_cache()
    phases.append(_run_phase("disabled_individual", iterations, reg, quantiles[:1], batch=False))

    # Restore original env state
    if initial_env == "0":
        os.environ.pop("DISABLE_METRIC_CACHE", None)
    else:
        os.environ["DISABLE_METRIC_CACHE"] = initial_env

    # Compute relative speedups vs disabled forms for analogous modes.
    # We match 'initial_batch' vs 'disabled_batch', etc.
    lookup = {p.label: p for p in phases}
    speedups: dict[str, float] = {}

    def _ratio(faster: float, slower: float) -> float:
        return slower / faster if faster > 0 else 0.0

    if "initial_batch" in lookup and "disabled_batch" in lookup:
        speedups["batch_speedup"] = _ratio(
            lookup["initial_batch"].mean_seconds, lookup["disabled_batch"].mean_seconds
        )
    if "initial_individual" in lookup and "disabled_individual" in lookup:
        speedups["individual_speedup"] = _ratio(
            lookup["initial_individual"].mean_seconds, lookup["disabled_individual"].mean_seconds
        )

    summary = BenchmarkSummary(
        cache_env_initial=initial_env,
        phases=phases,
        relative_speedup_vs_disabled=speedups,
        commit_hash=_detect_commit_hash(),
    )

    # Pretty print + JSON line for programmatic ingestion.
    print("\nBenchmark summary (approximate histogram quantiles):")
    for p in phases:
        print(
            f"  {p.label:20s} mean={p.mean_seconds * 1e3:7.3f} ms p90={p.p90_ms:7.3f} ms p99={p.p99_ms:7.3f} ms "
            f"stdev={p.stdev_seconds * 1e3:7.3f} ms min={p.min_seconds * 1e3:7.3f} ms max={p.max_seconds * 1e3:7.3f} ms"
        )
    if speedups:
        for k, v in speedups.items():
            print(f"  {k}: {v:.2f}x (mean time disabled / enabled)")
    print("\nJSON:")
    as_json: dict[str, Any] = asdict(summary)
    # Serialize dataclasses inside
    as_json["phases"] = [asdict(p) for p in phases]
    json_text = json.dumps(as_json, indent=2)
    print(json_text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            f.write(json_text + "\n")
        print(f"Wrote JSON summary to {args.json_out}")


if __name__ == "__main__":  # pragma: no cover - manual benchmark tool
    main()
