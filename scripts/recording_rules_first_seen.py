#!/usr/bin/env python
"""Utility to capture first-seen times for key Prometheus recording rule series.

Usage:
  python scripts/recording_rules_first_seen.py --output artifacts/recording_rules_first_seen.json --timeout 60 \
      --base http://localhost:9090
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request

DEFAULT_METRICS = [
    "internal_service:failure_rate_5m",
    "internal_service:failure_rate_10m",
    "internal_service:p99_latency_seconds_5m",
    "internal_service:p99_latency_seconds_30m",
]


def query(base: str, expr: str):
    url = f"{base}/api/v1/query?query={expr}"
    with urllib.request.urlopen(url, timeout=5) as r:  # nosec B310
        data = json.loads(r.read().decode())
    return data


def capture(base: str, metrics: list[str], timeout: int) -> dict:
    start = time.time()
    deadline = start + timeout
    first_seen: dict[str, float | None] = dict.fromkeys(metrics)
    while time.time() < deadline and any(v is None for v in first_seen.values()):
        for m in metrics:
            if first_seen[m] is not None:
                continue
            try:
                data = query(base, m)
                if data.get("status") == "success" and data.get("data", {}).get("result"):
                    first_seen[m] = time.time()
            except Exception:
                pass
        time.sleep(2)
    snapshot = time.time()
    return {
        "base": base,
        "start_time": start,
        "snapshot_time": snapshot,
        "timeout": timeout,
        "first_seen_epoch": first_seen,
        "first_seen_offsets_sec": {k: (v - start) if v else None for k, v in first_seen.items()},
        "unresolved": [k for k, v in first_seen.items() if v is None],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:9090", help="Prometheus base URL")
    ap.add_argument("--output", required=True, help="Output JSON path")
    ap.add_argument("--timeout", type=int, default=60, help="Seconds to wait for series")
    ap.add_argument("--metric", action="append", dest="metrics", help="Extra metric(s) to include")
    args = ap.parse_args()
    metrics = list(DEFAULT_METRICS)
    if args.metrics:
        metrics.extend(args.metrics)
    artifact = capture(args.base, metrics, args.timeout)
    with open(args.output, "w") as f:
        json.dump(artifact, f, indent=2)
    if artifact["unresolved"]:
        print("WARNING: Unresolved metrics:", artifact["unresolved"])
    else:
        print("All metrics resolved. Offsets (s):")
        for k, v in artifact["first_seen_offsets_sec"].items():
            print(f"  {k}: {v:.2f}")


if __name__ == "__main__":
    main()
