#!/usr/bin/env python3
"""Inject placeholder streak into stability metrics extensions and emit a streak badge.

Inputs:
  --metrics stability-metrics.json (modified in-place)
  --streak-file .placeholder-streak (counter file)
  --badge-out placeholder-streak-badge.json (Shields endpoint style)

Badge semantics:
  label: placeholder streak
  message: <streak>
  color scale:
    0 -> brightgreen (healthy)
    1-2 -> green
    3-4 -> yellow
    >=5 -> red
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def color_for(streak: int) -> str:
    if streak == 0:
        return "brightgreen"
    if streak <= 2:
        return "green"
    if streak <= 4:
        return "yellow"
    return "red"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--streak-file", required=True)
    ap.add_argument("--badge-out", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.metrics):
        print("metrics file missing", file=sys.stderr)
        return 1
    try:
        data = json.loads(open(args.metrics, encoding="utf-8").read())
    except Exception as e:
        print(f"failed to parse metrics: {e}", file=sys.stderr)
        return 1
    try:
        streak_raw = open(args.streak_file, encoding="utf-8").read().strip()
        streak = int(streak_raw) if streak_raw else 0
    except FileNotFoundError:
        streak = 0
    except Exception:
        streak = 0

    # ensure extensions
    ext = data.get("extensions")
    if not isinstance(ext, dict):
        ext = {}
        data["extensions"] = ext
    ext["placeholder_streak"] = streak

    with open(args.metrics, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    badge = {
        "schemaVersion": 1,
        "label": "placeholder streak",
        "message": str(streak),
        "color": color_for(streak),
    }
    with open(args.badge_out, "w", encoding="utf-8") as bf:
        json.dump(badge, bf)
    print(f"injected streak {streak} and wrote badge {args.badge_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
