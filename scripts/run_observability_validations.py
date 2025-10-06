#!/usr/bin/env python
"""Unified wrapper to run layout and alert validations and emit combined artifacts.

Outputs:
- combined_metrics.prom : concatenated metrics from both validators
- validations_index.json : high-level status summary with pointers to individual reports (if provided)

This script assumes the underlying validator scripts already exist:
- scripts/compare_grafana_layout.py
- scripts/validate_alert_rules.py
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
LAYOUT_SCRIPT = ROOT / "compare_grafana_layout.py"
ALERT_SCRIPT = ROOT / "validate_alert_rules.py"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r


def main():
    ap = argparse.ArgumentParser(
        description="Run layout and alert validations and aggregate metrics"
    )
    ap.add_argument("--layout-baseline", required=True)
    ap.add_argument("--layout-current-glob", required=True)
    ap.add_argument("--layout-report", default="")
    ap.add_argument("--layout-pos-tolerance", type=int, default=0)
    ap.add_argument("--layout-size-threshold", type=int, default=-1)
    ap.add_argument("--alerts-rules", required=True)
    ap.add_argument("--alerts-taxonomy", required=True)
    ap.add_argument("--alerts-report", default="")
    ap.add_argument("--alerts-required-labels", default="")
    ap.add_argument("--out-metrics", default="combined_metrics.prom")
    ap.add_argument("--out-index", default="validations_index.json")
    args = ap.parse_args()

    tmpdir = tempfile.mkdtemp(prefix="obs-validate-")
    layout_metrics = os.path.join(tmpdir, "layout.prom")
    alert_metrics = os.path.join(tmpdir, "alerts.prom")

    layout_cmd = [
        sys.executable,
        str(LAYOUT_SCRIPT),
        "--baseline",
        args.layout_baseline,
        "--current-glob",
        args.layout_current_glob,
        "--pos-tolerance",
        str(args.layout_pos_tolerance),
        "--size-threshold",
        str(args.layout_size_threshold),
        "--prom-metrics",
        layout_metrics,
    ]
    if args.layout_report:
        layout_cmd += ["--report", args.layout_report]

    alert_cmd = [
        sys.executable,
        str(ALERT_SCRIPT),
        "--rules",
        args.alerts_rules,
        "--taxonomy",
        args.alerts_taxonomy,
        "--prom-metrics",
        alert_metrics,
    ]
    if args.alerts_report:
        alert_cmd += ["--report", args.alerts_report]
    if args.alerts_required_labels:
        alert_cmd += ["--required-labels", args.alerts_required_labels]

    layout_res = run(layout_cmd)
    alert_res = run(alert_cmd)

    # Combine metrics (best effort)
    combined_metrics = []
    for p in (layout_metrics, alert_metrics):
        if os.path.exists(p):
            combined_metrics.append(open(p, encoding="utf-8").read().strip())
    os.makedirs(os.path.dirname(args.out_metrics) or ".", exist_ok=True)
    with open(args.out_metrics, "w", encoding="utf-8") as f:
        f.write("\n".join([m for m in combined_metrics if m]) + "\n")

    # Build index
    index = {
        "schema_version": 1,
        "layout": {
            "exit_code": layout_res.returncode,
            "report": args.layout_report or None,
        },
        "alerts": {
            "exit_code": alert_res.returncode,
            "report": args.alerts_report or None,
        },
        "overall_status": (
            "pass" if layout_res.returncode == 0 and alert_res.returncode == 0 else "fail"
        ),
    }
    with open(args.out_index, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    if layout_res.returncode != 0:
        print("Layout validation failed", file=sys.stderr)
        sys.stderr.write(layout_res.stderr)
    else:
        print("Layout validation succeeded")
        sys.stdout.write(layout_res.stdout)
    if alert_res.returncode != 0:
        print("Alert validation failed", file=sys.stderr)
        sys.stderr.write(alert_res.stderr)
    else:
        print("Alert validation succeeded")
        sys.stdout.write(alert_res.stdout)

    # Exit with aggregate non-zero if any failed
    if layout_res.returncode != 0 or alert_res.returncode != 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
