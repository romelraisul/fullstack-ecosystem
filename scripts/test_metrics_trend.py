#!/usr/bin/env python3
"""Simple regression test for taxonomy metrics trends.

This test ensures churn/risk churn do not unexpectedly increase beyond configured deltas
(compared to previous day's snapshot). Exit 0 on success, non-zero on failure.

Usage: run from repo root where metrics-history exists (or from CI). Configure via env:
  MAX_CHURN_DELTA = absolute allowed increase in churn_30d (default 5)
  MAX_RISK_CHURN_DELTA = absolute allowed increase in risk_churn_30d (default 10)

Returns detailed diagnostics on failure.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> int:
    HIST = Path("metrics-history")
    if not HIST.exists():
        print("No metrics-history directory; skipping trend test")
        return 0

    files = sorted(HIST.glob("metrics-*.json"))
    if len(files) < 2:
        print("Not enough history snapshots (<2); skipping trend test")
        return 0

    cur = json.loads(files[-1].read_text(encoding="utf-8"))
    prev = json.loads(files[-2].read_text(encoding="utf-8"))

    cur_churn = cur.get("churn_30d", 0)
    prev_churn = prev.get("churn_30d", 0)
    cur_risk = cur.get("risk_churn_30d", 0)
    prev_risk = prev.get("risk_churn_30d", 0)

    max_churn_delta = int(os.environ.get("MAX_CHURN_DELTA", "5"))
    max_risk_delta = int(os.environ.get("MAX_RISK_CHURN_DELTA", "10"))

    errs = []
    if cur_churn - prev_churn > max_churn_delta:
        errs.append(
            f"Churn increased by {cur_churn - prev_churn} (prev {prev_churn} -> cur {cur_churn}) > {max_churn_delta}"
        )
    if cur_risk - prev_risk > max_risk_delta:
        errs.append(
            f"Risk churn increased by {cur_risk - prev_risk} (prev {prev_risk} -> cur {cur_risk}) > {max_risk_delta}"
        )

    if errs:
        print("Trend regression test FAILED:\n" + "\n".join(errs))
        return 2
    else:
        print("Trend regression test PASSED")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
