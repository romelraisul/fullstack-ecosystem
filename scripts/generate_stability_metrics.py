#!/usr/bin/env python3
"""Generate rolling API stability metrics and badges.

Inputs (env / args):
  --history  Path to history JSONL file (each line: {timestamp, breaking: bool, score?: int})
  --current-status JSON file with breaking-status (fields may include breaking, incompatible, deleted_or_removed)
  --output-metrics JSON file to write aggregated metrics
  --badge-json Stability badge JSON output (Shields schema)
  --window N (int) optional sliding window size (default 30 lines)

If history file does not exist, metrics initialize from current status.
Stable score heuristic:
 - If provided in current status (score), use it
 - Else compute: 100 - (incompatible*10 + deleted_or_removed*5), clamped [0,100]
Aggregations:
 - total_runs
 - breaking_runs
 - stability_ratio (stable runs / total)
 - rolling ratios over window (same fields prefixed with window_)
 - last_score

The script will append the current status line into history (with calculated score) BEFORE computing metrics so that metrics reflect this run.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Any


def load_lines(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    lines = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                lines.append(json.loads(ln))
            except Exception:
                # skip malformed line
                continue
    return lines


def compute_score(status: dict[str, Any]) -> int:
    if "score" in status and isinstance(status["score"], int):
        return max(0, min(100, status["score"]))
    incompatible = int(status.get("incompatible", 0) or 0)
    deleted_removed = int(status.get("deleted_or_removed", 0) or 0)
    score = 100 - incompatible * 10 - deleted_removed * 5
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score


def badge_color(score: int) -> str:
    if score >= 90:
        return "brightgreen"
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    if score >= 25:
        return "orange"
    return "red"


def ratio(n: int, d: int) -> float:
    return round((n / d) if d else 0.0, 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", required=True)
    ap.add_argument("--current-status", required=True)
    ap.add_argument("--output-metrics", required=True)
    ap.add_argument("--badge-json", required=True)
    ap.add_argument("--window", type=int, default=30)
    args = ap.parse_args()

    try:
        with open(args.current_status, encoding="utf-8") as f:
            current = json.load(f)
    except FileNotFoundError:
        print("Missing current status file", file=sys.stderr)
        return 1

    current_score = compute_score(current)
    current_breaking = bool(current.get("breaking", False))

    # read history, append this record
    history = load_lines(args.history)
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    new_record = {"timestamp": now, "breaking": current_breaking, "score": current_score}
    # ensure directory exists
    os.makedirs(os.path.dirname(args.history) or ".", exist_ok=True)
    with open(args.history, "a", encoding="utf-8") as hf:
        hf.write(json.dumps(new_record) + "\n")
    history.append(new_record)

    total_runs = len(history)
    breaking_runs = sum(1 for h in history if h.get("breaking"))
    stable_runs = total_runs - breaking_runs

    # rolling window
    window = max(1, args.window)
    recent = history[-window:]
    recent_total = len(recent)
    recent_breaking = sum(1 for h in recent if h.get("breaking"))
    recent_stable = recent_total - recent_breaking

    # compute streaks (current stable streak, longest stable streak overall)
    current_stable_streak = 0
    for rec in reversed(history):
        if rec.get("breaking"):
            break
        current_stable_streak += 1
    longest_stable_streak = 0
    streak = 0
    for rec in history:
        if not rec.get("breaking"):
            streak += 1
            if streak > longest_stable_streak:
                longest_stable_streak = streak
        else:
            streak = 0

    # window mean score
    window_scores = [int(r.get("score", 0) or 0) for r in recent]
    window_mean_score = round(sum(window_scores) / len(window_scores), 2) if window_scores else 0.0

    # Build metrics object aligned with JSON schema contract
    metrics = {
        "schema_version": 1,
        "timestamp": now,
        "breaking": current_breaking,
        "score": current_score,
        "window_size": window,
        "window_total_count": recent_total,
        "window_stable_count": recent_stable,
        "window_stability_ratio": ratio(recent_stable, recent_total),
        "current_stable_streak": current_stable_streak,
        "longest_stable_streak": longest_stable_streak,
        "window_mean_score": window_mean_score,
    }

    # Non-contract / auxiliary fields go into extensions for forward compatibility
    extensions = {
        "total_runs": total_runs,
        "breaking_runs": breaking_runs,
        "stable_runs": stable_runs,
        "stability_ratio": ratio(stable_runs, total_runs),
        "window_breaking_runs": recent_breaking,
        "generated_at": now,
    }
    metrics["extensions"] = extensions

    os.makedirs(os.path.dirname(args.output_metrics) or ".", exist_ok=True)
    with open(args.output_metrics, "w", encoding="utf-8") as mf:
        json.dump(metrics, mf, indent=2)

    # badge message: score + window stability %
    stability_pct = int(metrics["window_stability_ratio"] * 100)
    badge = {
        "schemaVersion": 1,
        "label": "api stability",
        "message": f"score:{current_score} | {stability_pct}% stable | streak:{current_stable_streak}",
        "color": badge_color(current_score),
    }
    with open(args.badge_json, "w", encoding="utf-8") as bf:
        json.dump(badge, bf)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
