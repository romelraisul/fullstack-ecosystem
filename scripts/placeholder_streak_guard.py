#!/usr/bin/env python3
"""Guard against excessive consecutive placeholder stability metrics runs.

This script encapsulates the logic previously embedded in the workflow YAML so it
can be unit tested. It reads a metrics JSON file to determine if it is a placeholder
object (has `placeholder: true`). It maintains a streak counter file to count
consecutive placeholder occurrences and enforces a maximum allowed streak.

Usage:
  python scripts/placeholder_streak_guard.py \
      --metrics stability-metrics.json \
      --streak-file .placeholder-streak \
      --max 3

Exit codes:
  0  -> success (streak within allowed bounds or reset)
  2  -> metrics file missing (treated as error)
  3  -> invalid JSON
  4  -> exceeded max placeholder streak

On success a summary line is printed to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"metrics file missing: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"invalid json in metrics file: {e}", file=sys.stderr)
        sys.exit(3)


def read_int(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read().strip()
            return int(raw) if raw else 0
    except FileNotFoundError:
        return 0
    except Exception:
        return 0


def write_int(path: str, value: int) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(value))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True, help="Path to stability-metrics.json")
    ap.add_argument("--streak-file", required=True, help="File to persist streak counter")
    ap.add_argument(
        "--max", type=int, required=True, help="Maximum allowed consecutive placeholder runs"
    )
    args = ap.parse_args()

    metrics = load_json(args.metrics)
    is_placeholder = bool(metrics.get("placeholder"))
    streak = read_int(args.streak_file)

    if is_placeholder:
        streak += 1
        write_int(args.streak_file, streak)
        if streak > args.max:
            print(f"Placeholder streak {streak} exceeded max {args.max}", file=sys.stderr)
            return 4
        print(f"placeholder streak: {streak} (<= {args.max})")
        return 0
    else:
        # reset streak
        if streak != 0:
            write_int(args.streak_file, 0)
        print("placeholder streak reset (non-placeholder metrics)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
