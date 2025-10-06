#!/usr/bin/env python3
"""Classify per-operation additions and removals between two OpenAPI documents.

Outputs JSON with fields:
  operations_added: [{"method": "GET", "path": "/v1/foo"}, ...]
  operations_removed: [...]
  counts: {"added": <int>, "removed": <int>, "total_new": <int>, "total_old": <int>}
  generated_at: ISO8601 UTC timestamp

Usage:
  python classify_operation_changes.py --old previous.json --new openapi.json --out operations-classification.json

If --old is missing or empty, treats all new operations as added.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def load(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def collect_ops(spec: dict):
    paths = spec.get("paths") or {}
    out = set()
    for p, obj in paths.items():
        if not isinstance(obj, dict):
            continue
        for m, _op in obj.items():
            if m.lower() in HTTP_METHODS:
                out.add((m.upper(), p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=False, help="Previous schema file (JSON)")
    ap.add_argument("--new", required=True, help="New schema file (JSON)")
    ap.add_argument("--out", required=True, help="Output JSON file")
    args = ap.parse_args()

    old_spec = load(args.old) if args.old else {}
    new_spec = load(args.new) if args.new else {}

    new_ops = collect_ops(new_spec)
    old_ops = collect_ops(old_spec)

    added = sorted(new_ops - old_ops)
    removed = sorted(old_ops - new_ops)

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "total_new": len(new_ops),
            "total_old": len(old_ops),
        },
        "operations_added": [{"method": m, "path": p} for m, p in added],
        "operations_removed": [{"method": m, "path": p} for m, p in removed],
    }
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to write output: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
