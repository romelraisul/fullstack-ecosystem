#!/usr/bin/env python
"""Validate Grafana dashboard JSON files with a minimal schema.

Ensures common pitfalls are caught early in CI:
 - JSON parse errors
 - Required top-level keys: title, panels (list)
 - Each panel requires: title, type
 - No duplicate panel titles within a dashboard
 - Optional: version increments (warn only)

Exit codes:
 0 = all dashboards valid
 1 = one or more errors detected
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    print(
        "jsonschema dependency not installed; install jsonschema to run validation", file=sys.stderr
    )
    sys.exit(1)

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["title", "panels"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "panels": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "type"],
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "type": {"type": "string", "minLength": 1},
                },
            },
        },
    },
}


def validate_dashboard(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:  # pragma: no cover
        return [f"{path}: read error: {e}"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"{path}: JSON decode error: {e}"]
    v = Draft7Validator(SCHEMA)
    for err in sorted(v.iter_errors(data), key=lambda e: e.path):
        loc = ".".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: schema violation at {loc}: {err.message}")
    # Additional layout validations
    if isinstance(data, dict) and isinstance(data.get("panels"), list):
        titles = []
        seen = set()
        dups = set()
        rects = []  # (x,y,w,h,title)
        for p in data["panels"]:
            if not isinstance(p, dict):
                continue
            title = p.get("title")
            titles.append(title)
            if title in seen:
                dups.add(title)
            else:
                seen.add(title)
            gp = p.get("gridPos")
            if gp is None:
                errors.append(f"{path}: panel '{title}' missing gridPos")
                continue
            if not all(k in gp for k in ("x", "y", "w", "h")):
                errors.append(f"{path}: panel '{title}' gridPos incomplete (needs x,y,w,h)")
                continue
            try:
                x, y, w, h = int(gp["x"]), int(gp["y"]), int(gp["w"]), int(gp["h"])
            except Exception:
                errors.append(f"{path}: panel '{title}' gridPos values must be integers")
                continue
            if w <= 0 or h <= 0:
                errors.append(f"{path}: panel '{title}' has non-positive width/height")
                continue
            rects.append((x, y, w, h, title))
        if dups:
            errors.append(f"{path}: duplicate panel titles: {', '.join(sorted(dups))}")
        # Overlap detection: simple O(n^2) is fine for dashboard sizes
        for i in range(len(rects)):
            x1, y1, w1, h1, t1 = rects[i]
            r1 = (x1, y1, x1 + w1, y1 + h1)
            for j in range(i + 1, len(rects)):
                x2, y2, w2, h2, t2 = rects[j]
                r2 = (x2, y2, x2 + w2, y2 + h2)
                # Overlap if rectangles intersect in both axes
                if not (r1[2] <= r2[0] or r2[2] <= r1[0] or r1[3] <= r2[1] or r2[3] <= r1[1]):
                    errors.append(f"{path}: panels '{t1}' and '{t2}' overlap (gridPos)")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "docker" / "grafana" / "dashboards"
    if not root.exists():
        print(f"Dashboards path missing: {root}")
        return 0
    failures: list[str] = []
    for f in sorted(root.glob("*.json")):
        failures.extend(validate_dashboard(f))
    if failures:
        print("Dashboard validation failed:")
        for line in failures:
            print(f" - {line}")
        return 1
    print("All dashboards valid (schema + basic checks).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
