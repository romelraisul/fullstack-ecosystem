"""Aggregate multiple quantile benchmark JSON artifacts into summary outputs.

This script ingests the JSON output artifacts produced by
`scripts/benchmark_metrics_quantiles.py --json-out <file>` and produces:
  * A consolidated JSON summary (chronological) with per-run speedups and deltas
  * (Optionally) a Markdown table for quick human review / PR comments

It is intentionally dependency‑light (stdlib only) for CI friendliness.

Example (PowerShell):
  python scripts/aggregate_quantile_benchmarks.py \
    --input-glob "artifacts/quantile_bench_*.json" \
    --json-out artifacts/quantile_bench_aggregate.json \
    --markdown-out artifacts/quantile_bench_aggregate.md \
    --min-speedup-warn 1.05

Columns in Markdown table:
  date / tag | batch_mean_enabled_ms | batch_mean_disabled_ms | batch_speedup | individual_mean_enabled_ms | individual_mean_disabled_ms | individual_speedup | batch_speedup_delta_vs_prev | individual_speedup_delta_vs_prev

Speedup definition mirrors the benchmark script: disabled_mean / enabled_mean.

If --min-speedup-warn is provided and the most recent batch speedup falls below
that threshold, an exit code of 2 is returned (soft signal for CI).

Exit codes:
  0 success
  1 no matching input files
  2 below speedup threshold (soft warning)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import math

# Attempt to load .env for defaults like BENCH_ROLLING_WINDOW (best-effort)
try:  # pragma: no cover - convenience
    from scripts.load_env import load_env as _load_env
    _load_env()
except Exception:  # noqa: BLE001
    pass


@dataclass
class RunEntry:
    source_file: str
    timestamp: Optional[str]  # ISO8601 or None if not derivable
    commit_hash: Optional[str]
    # Raw replicated pieces
    batch_mean_enabled_ms: float
    batch_mean_disabled_ms: float
    batch_speedup: float
    individual_mean_enabled_ms: float
    individual_mean_disabled_ms: float
    individual_speedup: float
    # Deltas versus previous entry (filled after sorting)
    batch_speedup_delta_vs_prev: Optional[float] = None
    individual_speedup_delta_vs_prev: Optional[float] = None
    # Rolling averages (filled later)
    batch_speedup_rolling_mean: Optional[float] = None
    individual_speedup_rolling_mean: Optional[float] = None


def _derive_timestamp(path: str) -> Optional[str]:
    """Attempt to derive a timestamp from filename or file mtime.

    Strategy: If filename contains an obvious YYYYMMDD_HHMMSS pattern use that,
    else fall back to fs modified time.
    """
    base = os.path.basename(path)
    # Look for 14 digit date + '_' + 6 digit time (e.g., 20250916_095045)
    for token in base.replace('-', '_').split('_'):
        if len(token) == 14 and token.isdigit():  # e.g., 20250916 095045 concatenated
            try:
                dt = datetime.strptime(token, "%Y%m%d%H%M%S")
                return dt.isoformat()
            except ValueError:
                pass
        if len(token) == 15 and token.count('.') == 0 and token[:8].isdigit() and token[9:].isdigit():
            # Potential variant with embedded '_' removed earlier – ignore for simplicity
            pass
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.isoformat()
    except OSError:
        return None


def _ms(seconds: float) -> float:
    return seconds * 1000.0


def _load_file(path: str) -> Optional[RunEntry]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"WARN: failed to parse {path}: {exc}", file=sys.stderr)
        return None

    # Expected keys from benchmark script
    phases = {p['label']: p for p in data.get('phases', [])}
    speed = data.get('relative_speedup_vs_disabled', {})

    def _mean(label: str) -> Optional[float]:
        p = phases.get(label)
        return p.get('mean_seconds') if p else None

    required = [
        'initial_batch', 'disabled_batch', 'initial_individual', 'disabled_individual'
    ]
    if not all(k in phases for k in required):
        print(f"WARN: {path} missing required phases; skipping", file=sys.stderr)
        return None

    batch_speed = float(speed.get('batch_speedup', 0.0))
    individual_speed = float(speed.get('individual_speedup', 0.0))

    commit_hash = data.get('commit_hash') or data.get('commit')

    return RunEntry(
        source_file=path,
        timestamp=_derive_timestamp(path),
        commit_hash=commit_hash,
        batch_mean_enabled_ms=_ms(float(_mean('initial_batch'))),
        batch_mean_disabled_ms=_ms(float(_mean('disabled_batch'))),
        batch_speedup=batch_speed,
        individual_mean_enabled_ms=_ms(float(_mean('initial_individual'))),
        individual_mean_disabled_ms=_ms(float(_mean('disabled_individual'))),
        individual_speedup=individual_speed,
    )


def _sparkline(values: List[float], width: int = 18) -> str:
    """Generate a very small ASCII sparkline (no external deps).

    We bucket values into unicode block characters. Scales to min/max of provided list.
    """
    if not values:
        return ''
    # Unicode blocks (increasing)
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return blocks[0] * min(len(values), width)
    # Downsample if necessary
    if len(values) > width:
        step = len(values) / width
        sampled = []
        i = 0.0
        while len(sampled) < width:
            sampled.append(values[int(i)])
            i += step
        values = sampled
    out = []
    for v in values:
        idx = int((v - lo) / (hi - lo) * (len(blocks) - 1))
        out.append(blocks[idx])
    return ''.join(out)


def _format_md(rows: List[RunEntry]) -> str:
    header = (
        "| run | commit | batch_speedup | batch_roll | batch_delta | indiv_speedup | indiv_roll | indiv_delta | batch_spark | indiv_spark |\n"
        "|-----|--------|--------------:|-----------:|-----------:|-------------:|-----------:|-----------:|------------:|------------:|"
    )
    lines = [header]
    batch_vals = [r.batch_speedup for r in rows]
    indiv_vals = [r.individual_speedup for r in rows]
    batch_spark = _sparkline(batch_vals)
    indiv_spark = _sparkline(indiv_vals)
    for idx, r in enumerate(rows):
        lines.append(
            f"| {idx+1} | { (r.commit_hash or '')[:8]:8s} | {r.batch_speedup:6.2f}x | "
            f"{(r.batch_speedup_rolling_mean if r.batch_speedup_rolling_mean is not None else 0):6.2f} | "
            f"{(r.batch_speedup_delta_vs_prev if r.batch_speedup_delta_vs_prev is not None else 0):+6.2f} | "
            f"{r.individual_speedup:6.2f}x | "
            f"{(r.individual_speedup_rolling_mean if r.individual_speedup_rolling_mean is not None else 0):6.2f} | "
            f"{(r.individual_speedup_delta_vs_prev if r.individual_speedup_delta_vs_prev is not None else 0):+6.2f} | "
            f"{batch_spark:10s} | {indiv_spark:10s} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate quantile benchmark JSON runs")
    parser.add_argument("--input-glob", required=True, help="Glob pattern for input JSON artifacts")
    parser.add_argument("--json-out", help="Write consolidated JSON here")
    parser.add_argument("--markdown-out", help="Write Markdown table here")
    parser.add_argument("--min-speedup-warn", type=float, default=None, help="If latest batch speedup < threshold return exit code 2")
    parser.add_argument("--sort", choices=["mtime", "name"], default="mtime", help="Sort order (mtime or name)")
    parser.add_argument("--rolling-window", type=int, default=5, help="Window size for rolling mean (default 5)")
    # Guardrail thresholds (percent increase allowed relative to rolling mean of ENABLED phases)
    parser.add_argument("--max-p95-increase", type=float, default=None,
                        help="Fail (exit 3) if latest enabled initial_batch p95 exceeds rolling mean by this factor (e.g. 1.10)")
    parser.add_argument("--max-p99-increase", type=float, default=None,
                        help="Fail (exit 4) if latest enabled initial_batch p99 exceeds rolling mean by this factor")
    parser.add_argument("--max-stdev-multiplier", type=float, default=None,
                        help="Fail (exit 5) if latest enabled initial_batch stdev exceeds rolling mean stdev * multiplier")
    parser.add_argument("--guardrail-phase", default="initial_batch",
                        help="Phase label to apply guardrails against (default initial_batch)")
    parser.add_argument("--svg-out", help="Optional path to write percentile trend SVG (initial_batch p50/p90/p95/p99)")
    args = parser.parse_args()

    paths = sorted(glob.glob(args.input_glob))
    if not paths:
        print("No input files matched", file=sys.stderr)
        return 1

    # Sorting
    if args.sort == 'mtime':
        paths.sort(key=lambda p: os.path.getmtime(p))
    else:
        paths.sort()

    entries: List[RunEntry] = []
    for p in paths:
        e = _load_file(p)
        if e:
            entries.append(e)

    if not entries:
        print("No valid benchmark entries after parsing", file=sys.stderr)
        return 1

    # Compute deltas + rolling means
    prev: Optional[RunEntry] = None
    window: List[RunEntry] = []
    rw = max(1, args.rolling_window)
    for e in entries:
        if prev:
            e.batch_speedup_delta_vs_prev = e.batch_speedup - prev.batch_speedup
            e.individual_speedup_delta_vs_prev = e.individual_speedup - prev.individual_speedup
        window.append(e)
        if len(window) > rw:
            window.pop(0)
        # Rolling means
        e.batch_speedup_rolling_mean = sum(w.batch_speedup for w in window) / len(window)
        e.individual_speedup_rolling_mean = sum(w.individual_speedup for w in window) / len(window)
        prev = e

    # Collect phase stats (variance, percentiles) from each file if present.
    phase_stats_by_run: List[Dict[str, Any]] = []
    phase_keys = ["initial_batch", "initial_individual", "disabled_batch", "disabled_individual"]
    for e in entries:
        try:
            with open(e.source_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception:
            phase_stats_by_run.append({"source_file": e.source_file, "phases": {}})
            continue
        phases_raw = {p.get('label'): p for p in raw.get('phases', [])}
        phases_out: Dict[str, Any] = {}
        for k in phase_keys:
            p = phases_raw.get(k)
            if not p:
                continue
            # Extract extended stats if present
            phases_out[k] = {
                "mean_ms": p.get('mean_seconds', 0.0) * 1000.0,
                "median_ms": p.get('median_seconds', 0.0) * 1000.0,
                "min_ms": p.get('min_seconds', 0.0) * 1000.0,
                "max_ms": p.get('max_seconds', 0.0) * 1000.0,
                "variance_ms2": (p.get('variance_seconds', 0.0) or 0.0) * 1_000_000.0,
                "stdev_ms": (p.get('stdev_seconds', 0.0) or 0.0) * 1000.0,
                "p50_ms": p.get('p50_ms'),
                "p90_ms": p.get('p90_ms'),
                "p95_ms": p.get('p95_ms'),
                "p99_ms": p.get('p99_ms'),
            }
        phase_stats_by_run.append({
            "source_file": e.source_file,
            "commit_hash": e.commit_hash,
            "timestamp": e.timestamp,
            "phases": phases_out,
        })

    latest_phase_stats = phase_stats_by_run[-1] if phase_stats_by_run else {}

    # Rolling percentile summaries per phase (p50/p90/p95/p99) using same rolling window size.
    def _collect_percentile_series(label: str, key: str) -> List[Optional[float]]:
        out: List[Optional[float]] = []
        for run in phase_stats_by_run:
            ph = run.get('phases', {}).get(label)
            out.append(ph.get(key) if ph else None)
        return out

    def _rolling_mean(values: List[Optional[float]], window: int) -> Optional[float]:
        recent = [v for v in values[-window:] if isinstance(v, (int, float))]
        if not recent:
            return None
        return sum(recent) / len(recent)

    rolling_phase_percentiles: Dict[str, Any] = {}
    for phase_label in ["initial_batch", "disabled_batch", "initial_individual", "disabled_individual"]:
        phase_block: Dict[str, Any] = {}
        for pct_key in ["p50_ms", "p90_ms", "p95_ms", "p99_ms"]:
            series = _collect_percentile_series(phase_label, pct_key)
            latest_val = series[-1] if series else None
            roll_mean = _rolling_mean(series, args.rolling_window)
            phase_block[pct_key.replace('_ms', '')] = {
                "latest_ms": latest_val,
                "rolling_mean_ms": roll_mean,
            }
        rolling_phase_percentiles[phase_label] = phase_block

    # JSON aggregate
    aggregate: Dict[str, Any] = {
        "count": len(entries),
        "rolling_window": args.rolling_window,
        "entries": [asdict(e) for e in entries],
        "latest": asdict(entries[-1]),
        "batch_sparkline": _sparkline([e.batch_speedup for e in entries]),
        "individual_sparkline": _sparkline([e.individual_speedup for e in entries]),
        "phase_stats_by_run": phase_stats_by_run,
        "latest_phase_stats": latest_phase_stats,
        "rolling_phase_percentiles": rolling_phase_percentiles,
    }

    # Guardrail evaluation
    guardrail_results: List[Dict[str, Any]] = []
    exit_code_override: Optional[int] = None
    phase_target = args.guardrail_phase
    # Build rolling means for percentiles & stdev for target phase
    if phase_stats_by_run:
        pct_series = {k: [] for k in ["p95_ms", "p99_ms"]}
        stdev_series: List[Optional[float]] = []
        for run in phase_stats_by_run:
            ph = run.get('phases', {}).get(phase_target, {})
            pct_series["p95_ms"].append(ph.get('p95_ms'))
            pct_series["p99_ms"].append(ph.get('p99_ms'))
            stdev_series.append(ph.get('stdev_ms'))
        def _rolling(values: List[Optional[float]]) -> Optional[float]:
            recent = [v for v in values[-args.rolling_window:] if isinstance(v, (int, float))]
            return sum(recent)/len(recent) if recent else None
        latest = phase_stats_by_run[-1]['phases'].get(phase_target, {}) if phase_stats_by_run else {}
        latest_p95 = latest.get('p95_ms')
        latest_p99 = latest.get('p99_ms')
        latest_stdev = latest.get('stdev_ms')
        roll_p95 = _rolling(pct_series['p95_ms'])
        roll_p99 = _rolling(pct_series['p99_ms'])
        roll_stdev = _rolling(stdev_series)

        # Evaluate each configured guardrail
        if args.max_p95_increase and latest_p95 and roll_p95:
            allowed = roll_p95 * args.max_p95_increase
            passed = latest_p95 <= allowed
            guardrail_results.append({
                "type": "p95_increase",
                "phase": phase_target,
                "latest_ms": latest_p95,
                "rolling_mean_ms": roll_p95,
                "max_allowed_ms": allowed,
                "factor": args.max_p95_increase,
                "status": "pass" if passed else "fail",
            })
            if not passed and exit_code_override is None:
                exit_code_override = 3
        if args.max_p99_increase and latest_p99 and roll_p99:
            allowed = roll_p99 * args.max_p99_increase
            passed = latest_p99 <= allowed
            guardrail_results.append({
                "type": "p99_increase",
                "phase": phase_target,
                "latest_ms": latest_p99,
                "rolling_mean_ms": roll_p99,
                "max_allowed_ms": allowed,
                "factor": args.max_p99_increase,
                "status": "pass" if passed else "fail",
            })
            if not passed and exit_code_override is None:
                exit_code_override = 4
        if args.max_stdev_multiplier and latest_stdev and roll_stdev:
            allowed = roll_stdev * args.max_stdev_multiplier
            passed = latest_stdev <= allowed
            guardrail_results.append({
                "type": "stdev_multiplier",
                "phase": phase_target,
                "latest_stdev_ms": latest_stdev,
                "rolling_stdev_ms": roll_stdev,
                "max_allowed_stdev_ms": allowed,
                "multiplier": args.max_stdev_multiplier,
                "status": "pass" if passed else "fail",
            })
            if not passed and exit_code_override is None:
                exit_code_override = 5

    if guardrail_results:
        aggregate["guardrails"] = guardrail_results


    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(aggregate, f, indent=2)
            f.write('\n')
        print(f"Wrote JSON aggregate to {args.json_out}")

    # SVG generation (simple polyline chart for target phase percentiles)
    if args.svg_out and phase_stats_by_run:
        target = args.guardrail_phase
        # Collect percentile series
        series_map: Dict[str, List[float]] = {k: [] for k in ["p50_ms", "p90_ms", "p95_ms", "p99_ms"]}
        for run in phase_stats_by_run:
            ph = run.get('phases', {}).get(target, {})
            for k in series_map:
                v = ph.get(k)
                if v is None:
                    # If missing, replicate last or 0
                    series_map[k].append(series_map[k][-1] if series_map[k] else 0.0)
                else:
                    series_map[k].append(float(v))
        # Determine bounds
        all_vals = [v for lst in series_map.values() for v in lst]
        if not all_vals:
            print("SVG: No percentile values to chart", file=sys.stderr)
        else:
            pad = 0.05
            lo = min(all_vals)
            hi = max(all_vals)
            if hi - lo < 1e-9:
                hi = lo + 1.0  # avoid div by zero
            w, h, margin = 480, 200, 30
            colors = {
                "p50_ms": "#2c7bb6",
                "p90_ms": "#abd9e9",
                "p95_ms": "#fdae61",
                "p99_ms": "#d7191c",
            }
            def scale_x(i: int, n: int) -> float:
                return margin + (w - 2*margin) * (i / max(1, n-1))
            def scale_y(v: float) -> float:
                return h - margin - (v - lo) / (hi - lo) * (h - 2*margin)
            n = len(next(iter(series_map.values())))
            polylines = []
            for k, vals in series_map.items():
                pts = " ".join(f"{scale_x(i, n):.2f},{scale_y(v):.2f}" for i, v in enumerate(vals))
                polylines.append(f"<polyline fill='none' stroke='{colors[k]}' stroke-width='2' points='{pts}' />")
            # Axes + labels minimal
            svg_parts = [
                f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='monospace' font-size='10'>",
                f"<rect x='0' y='0' width='{w}' height='{h}' fill='white' stroke='#ddd' />",
                f"<text x='{w/2}' y='14' text-anchor='middle'>Percentile Trend {target}</text>
<text x='{w - margin}' y='{h - margin/4}' text-anchor='end'>{n} runs</text>",
            ]
            # Y-axis ticks (5)
            for t in range(6):
                val = lo + (hi - lo) * t / 5
                y = scale_y(val)
                svg_parts.append(f"<line x1='{margin-5}' y1='{y:.2f}' x2='{w-margin}' y2='{y:.2f}' stroke='#eee' />")
                svg_parts.append(f"<text x='{margin-7}' y='{y+3:.2f}' text-anchor='end'>{val:.2f}ms</text>")
            svg_parts.extend(polylines)
            # Legend
            lx, ly = margin, margin
            for idx, k in enumerate(series_map.keys()):
                svg_parts.append(f"<rect x='{lx}' y='{ly + idx*14}' width='10' height='10' fill='{colors[k]}' />")
                svg_parts.append(f"<text x='{lx+14}' y='{ly + idx*14 + 9}'>{k.replace('_ms','')}</text>")
            svg_parts.append("</svg>")
            svg = "\n".join(svg_parts)
            try:
                with open(args.svg_out, 'w', encoding='utf-8') as fsvg:
                    fsvg.write(svg)
                print(f"Wrote SVG percentile trend to {args.svg_out}")
                aggregate['svg_percentiles'] = os.path.basename(args.svg_out)
            except Exception as exc:  # pragma: no cover
                print(f"WARN: failed writing SVG: {exc}", file=sys.stderr)

    if args.markdown_out:
        md = _format_md(entries)
        with open(args.markdown_out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"Wrote Markdown table to {args.markdown_out}")

    # Speedup threshold check (applies to batch only as main signal)
    if args.min_speedup_warn is not None:
        latest = entries[-1]
        if latest.batch_speedup < args.min_speedup_warn:
            print(
                f"WARN: latest batch_speedup {latest.batch_speedup:.2f}x < threshold {args.min_speedup_warn:.2f}x",
                file=sys.stderr,
            )
            return 2

    if exit_code_override is not None:
        # Emit summary lines for failing guardrails
        for gr in guardrail_results:
            if gr["status"] == "fail":
                print(f"GUARDRAIL FAIL [{gr['type']}]: phase={gr['phase']} latest={gr.get('latest_ms', gr.get('latest_stdev_ms'))} rolling={gr.get('rolling_mean_ms', gr.get('rolling_stdev_ms'))}", file=sys.stderr)
        return exit_code_override

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())
