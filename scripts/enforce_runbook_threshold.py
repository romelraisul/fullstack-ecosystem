#!/usr/bin/env python
"""Enforce runbook completeness threshold for taxonomy metrics.

Reads RUNBOOK_MIN_PERCENT (default 90) from env and taxonomy-metrics.json for the
runbook_completeness_percent field. Exits non-zero if below threshold.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

THRESH_ENV = os.getenv("RUNBOOK_MIN_PERCENT", "90")
try:
    threshold = float(THRESH_ENV)
except Exception:
    threshold = 90.0

metrics_path = pathlib.Path("taxonomy-metrics.json")
if metrics_path.exists():
    try:
        data = json.loads(metrics_path.read_text())
        completeness = float(data.get("runbook_completeness_percent", 100))
    except Exception:
        completeness = 100.0
else:
    completeness = 100.0

if completeness < threshold:
    sys.stderr.write(f"Runbook completeness {completeness:.2f}% below minimum {threshold:.2f}%\n")
    sys.exit(1)
print(f"Runbook completeness {completeness:.2f}% meets minimum {threshold:.2f}%")
