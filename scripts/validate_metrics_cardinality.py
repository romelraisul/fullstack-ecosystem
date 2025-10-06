#!/usr/bin/env python
"""Validate Prometheus text format metrics cardinality & sample counts.

Rules (configurable by env / flags):
- Max unique metric names
- Max samples per metric (by name)
- Max total samples
- Optional allowed name prefix whitelist

Intended to run in CI after combined_metrics.prom generation.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

RE_SAMPLE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"
)


def parse_metrics(path):
    counts = defaultdict(int)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = RE_SAMPLE.match(line)
            if not m:
                continue
            name = m.group("name")
            counts[name] += 1
    list(counts.keys())
    total_samples = sum(counts.values())
    return counts, total_samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", default="combined_metrics.prom")
    ap.add_argument("--max-metric-names", type=int, default=int(os.getenv("CARD_MAX_NAMES", "200")))
    ap.add_argument(
        "--max-samples-per-metric", type=int, default=int(os.getenv("CARD_MAX_SAMPLES_PER", "100"))
    )
    ap.add_argument(
        "--max-total-samples", type=int, default=int(os.getenv("CARD_MAX_TOTAL", "2000"))
    )
    ap.add_argument("--allow-prefixes", default=os.getenv("CARD_ALLOW_PREFIXES", ""))
    ap.add_argument("--json-report", default="")
    args = ap.parse_args()

    if not os.path.exists(args.metrics):
        print(f"Metrics file not found: {args.metrics}", file=sys.stderr)
        sys.exit(1)

    counts, total = parse_metrics(args.metrics)
    prefixes = [p for p in args.allow_prefixes.split(",") if p]

    violations = []
    unique_names = len(counts)
    if unique_names > args.max_metric_names:
        violations.append(f"metric_names_exceed:{unique_names}>{args.max_metric_names}")
    for name, c in counts.items():
        if c > args.max_samples_per_metric:
            violations.append(f"samples_exceed:{name}:{c}>{args.max_samples_per_metric}")
        if prefixes and not any(name.startswith(p) for p in prefixes):
            violations.append(f"prefix_violation:{name}")
    if total > args.max_total_samples:
        violations.append(f"total_samples_exceed:{total}>{args.max_total_samples}")

    report = {
        "metric_names": unique_names,
        "total_samples": total,
        "per_metric_samples": counts,
        "violations": violations,
        "config": {
            "max_metric_names": args.max_metric_names,
            "max_samples_per_metric": args.max_samples_per_metric,
            "max_total_samples": args.max_total_samples,
            "allow_prefixes": prefixes,
        },
    }

    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if violations:
        print("Cardinality validation FAILED:")
        for v in violations:
            print(" -", v)
        sys.exit(2)
    else:
        print(f"Cardinality validation passed: {unique_names} metric names, {total} samples")


if __name__ == "__main__":
    main()
