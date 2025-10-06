#!/usr/bin/env python3
"""Compute milestone completion summary and emit summary + badge JSON.

Reads project_milestones.json with entries:
  {id, title, weight, status}
Status accepted values: done, in-progress, not-started, blocked (optional)

Outputs (default paths):
  milestone-summary.json:
    {
      "generated_at": ...,
      "totals": {"weight_total": X, "weight_done": Y, "percent": 87.5},
      "by_status": {"done": N, "in-progress": M, ...},
      "items": [...] (echoed with computed percent contribution)
    }
  milestones-badge.json (Shields endpoint):
    {"schemaVersion":1,"label":"milestones","message":"87.5%","color":"green"}

Color scale:
  >=90 brightgreen, >=75 green, >=55 yellow, >=35 orange, else red
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_STATUSES = {"done", "in-progress", "not-started", "blocked"}


def load(path: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to load milestones: {e}", file=sys.stderr)
        return []


def color_for(p: float) -> str:
    if p >= 0.90:
        return "brightgreen"
    if p >= 0.75:
        return "green"
    if p >= 0.55:
        return "yellow"
    if p >= 0.35:
        return "orange"
    return "red"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestones", default="project_milestones.json")
    ap.add_argument("--summary-out", default="milestone-summary.json")
    ap.add_argument("--badge-out", default="milestones-badge.json")
    args = ap.parse_args()

    items = load(args.milestones)
    weight_total = sum(max(0, int(i.get("weight", 0))) for i in items)
    weight_done = 0
    by_status = dict.fromkeys(VALID_STATUSES, 0)
    norm_items = []
    for raw in items:
        status = raw.get("status", "not-started")
        if status not in VALID_STATUSES:
            status = "not-started"
        w = max(0, int(raw.get("weight", 0)))
        if status == "done":
            weight_done += w
        by_status[status] += 1
        pct_contrib = (w / weight_total * 100) if weight_total else 0
        norm = {
            "id": raw.get("id"),
            "title": raw.get("title"),
            "weight": w,
            "status": status,
            "weight_pct": round(pct_contrib, 2),
        }
        norm_items.append(norm)
    percent = (weight_done / weight_total) if weight_total else 0

    summary = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "totals": {
            "weight_total": weight_total,
            "weight_done": weight_done,
            "percent": round(percent * 100, 2),
        },
        "by_status": by_status,
        "items": norm_items,
    }
    Path(args.summary_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    badge = {
        "schemaVersion": 1,
        "label": "milestones",
        "message": f"{summary['totals']['percent']}%",
        "color": color_for(percent),
    }
    Path(args.badge_out).write_text(json.dumps(badge), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
