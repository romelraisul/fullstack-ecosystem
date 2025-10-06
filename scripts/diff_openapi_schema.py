"""Diff two OpenAPI schema JSON files and print a concise summary.

Usage:
  python scripts/diff_openapi_schema.py --old path/to/old.json --new path/to/new.json

Output:
  Prints counts of added/removed/changed top-level paths and components schemas.
  Exits 0 always (informational) unless files cannot be read/parsed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _diff_sets(old: set[str], new: set[str]):
    return sorted(new - old), sorted(old - new), sorted(s for s in new & old if s not in old - new)


def main() -> int:
    ap = argparse.ArgumentParser(description="Diff two OpenAPI schemas")
    ap.add_argument("--old", required=True, help="Old schema JSON path")
    ap.add_argument("--new", required=True, help="New schema JSON path")
    ap.add_argument("--json-out", help="Optional JSON diff output path")
    args = ap.parse_args()

    old_p = Path(args.old)
    new_p = Path(args.new)
    if not old_p.exists() or not new_p.exists():
        print("One or both schema files do not exist", file=sys.stderr)
        return 1

    try:
        old = _load(old_p)
        new = _load(new_p)
    except Exception as e:
        print(f"Failed to parse schema(s): {e}", file=sys.stderr)
        return 1

    old_paths = set((old.get("paths") or {}).keys())
    new_paths = set((new.get("paths") or {}).keys())

    added_paths = sorted(new_paths - old_paths)
    removed_paths = sorted(old_paths - new_paths)
    common_paths = sorted(new_paths & old_paths)

    old_schemas = set(((old.get("components") or {}).get("schemas") or {}).keys())
    new_schemas = set(((new.get("components") or {}).get("schemas") or {}).keys())

    added_schemas = sorted(new_schemas - old_schemas)
    removed_schemas = sorted(old_schemas - new_schemas)

    print("OpenAPI Diff Summary")
    print("====================")
    print(
        f"Paths: +{len(added_paths)} -{len(removed_paths)} ~{len(common_paths)} (total new: {len(new_paths)})"
    )
    if added_paths:
        print("  Added paths:")
        for p in added_paths:
            print(f"    + {p}")
    if removed_paths:
        print("  Removed paths:")
        for p in removed_paths:
            print(f"    - {p}")

    print(f"Schemas: +{len(added_schemas)} -{len(removed_schemas)} (total new: {len(new_schemas)})")
    if added_schemas:
        print("  Added schemas:")
        for s in added_schemas:
            print(f"    + {s}")
    if removed_schemas:
        print("  Removed schemas:")
        for s in removed_schemas:
            print(f"    - {s}")

    if args.json_out:
        diff_obj = {
            "paths": {
                "added": added_paths,
                "removed": removed_paths,
                "total_new": len(new_paths),
            },
            "schemas": {
                "added": added_schemas,
                "removed": removed_schemas,
                "total_new": len(new_schemas),
            },
        }
        try:
            Path(args.json_out).write_text(json.dumps(diff_obj, indent=2), encoding="utf-8")
            print(f"Wrote JSON diff -> {args.json_out}")
        except Exception as e:  # pragma: no cover
            print(f"Failed to write JSON diff: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
