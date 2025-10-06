#!/usr/bin/env python3
"""SBOM Diff Utility

Compares two CycloneDX JSON SBOM files (previous vs current) and emits a JSON
diff describing added, removed, and version-changed components. Designed to be
fast, dependency-light (stdlib only), and CI friendly.

Exit Codes:
  0 = Success (no disallowed changes OR initial baseline creation)
  1 = Usage / argument error
  2 = Changes detected (only when --fail-on-change provided and not initial)

JSON Output Schema (written to --output):
{
    "meta": {
        "generated": ISO8601 UTC timestamp,
        "current": path to current SBOM,
        "previous": path or null,
        "initial_baseline": bool,
        "counts": {"added": n, "removed": m, "version_changed": k, "hash_changed": h}
    },
    "added": [ {"key": str, "name": str, "version": str, "purl": str|null} ],
    "removed": [ {"key": str, "name": str, "version": str, "purl": str|null} ],
    "version_changed": [ {"key": str, "name": str, "previous_version": str, "current_version": str, "purl": str|null} ],
    "hash_changed": [ {"key": str, "name": str, "version": str, "previous_hashes": [..], "current_hashes": [..], "purl": str|null} ]
}

Component Identity Strategy:
  Prefer component.purl as stable key; fallback to component.name.
  (CycloneDX strongly encourages purl; name fallback covers gaps.)

Baseline Update Behavior:
  If --update-baseline is provided and differences are acceptable (or this is
  the first baseline), the current SBOM is copied to the previous path to
  establish/update the baseline.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from typing import Any


def load_components(path: str) -> dict[str, dict[str, Any]]:
    """Load components from a CycloneDX JSON SBOM.

    Returns a mapping key -> component simplified dict {name, version, purl}.
    Key preference order: purl else name.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    comps = {}
    for comp in data.get("components", []) or []:
        name = comp.get("name") or "<unknown>"
        version = comp.get("version") or "<none>"
        purl = comp.get("purl")
        # Extract hashes (CycloneDX spec: component.hashes = [ {"alg": "SHA-256", "content": "..."}, ... ])
        hashes = []
        for h in comp.get("hashes", []) or []:
            alg = h.get("alg") or h.get("algorithm")
            content = h.get("content") or h.get("value")
            if alg and content:
                hashes.append(f"{alg}:{content}")
        key = purl or name
        if key not in comps:  # first occurrence wins
            comps[key] = {"name": name, "version": version, "purl": purl, "hashes": sorted(hashes)}
    return comps


def compute_diff(
    prev: dict[str, dict[str, Any]], cur: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    version_changed: list[dict[str, Any]] = []
    hash_changed: list[dict[str, Any]] = []

    for key, comp in cur.items():
        if key not in prev:
            added.append({"key": key, **comp})
        else:
            prev_comp = prev[key]
            prev_ver = prev_comp["version"]
            if prev_ver != comp["version"]:
                version_changed.append(
                    {
                        "key": key,
                        "name": comp["name"],
                        "previous_version": prev_ver,
                        "current_version": comp["version"],
                        "purl": comp["purl"],
                    }
                )
            else:
                # Same version: compare hash lists
                prev_hashes = prev_comp.get("hashes", [])
                cur_hashes = comp.get("hashes", [])
                if prev_hashes and cur_hashes and prev_hashes != cur_hashes:
                    hash_changed.append(
                        {
                            "key": key,
                            "name": comp["name"],
                            "version": comp["version"],
                            "previous_hashes": prev_hashes,
                            "current_hashes": cur_hashes,
                            "purl": comp["purl"],
                        }
                    )

    for key, comp in prev.items():
        if key not in cur:
            removed.append({"key": key, **comp})
    return added, removed, version_changed, hash_changed


def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Diff two CycloneDX JSON SBOM files")
    p.add_argument("--current", required=True, help="Path to current CycloneDX SBOM JSON")
    p.add_argument(
        "--previous", required=False, help="Path to previous (baseline) CycloneDX SBOM JSON"
    )
    p.add_argument("--output", required=True, help="Path to write diff JSON")
    p.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit with code 2 if any changes detected (ignored if initial baseline)",
    )
    p.add_argument(
        "--update-baseline",
        action="store_true",
        help="If provided, update/copy current to previous path after successful diff",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if not os.path.isfile(args.current):
        print(f"[sbom-diff] Current SBOM does not exist: {args.current}", file=sys.stderr)
        return 1

    previous_exists = bool(args.previous and os.path.isfile(args.previous))
    prev_components = {}
    if previous_exists:
        try:
            prev_components = load_components(args.previous)  # type: ignore
        except Exception as e:  # pragma: no cover
            print(f"[sbom-diff] Failed to read previous SBOM: {e}", file=sys.stderr)
            return 1

    try:
        cur_components = load_components(args.current)
    except Exception as e:  # pragma: no cover
        print(f"[sbom-diff] Failed to read current SBOM: {e}", file=sys.stderr)
        return 1

    if not previous_exists:
        added = [{"key": k, **v} for k, v in sorted(cur_components.items(), key=lambda kv: kv[0])]
        removed: list[dict[str, Any]] = []
        version_changed: list[dict[str, Any]] = []
        hash_changed: list[dict[str, Any]] = []
        initial = True
    else:
        added, removed, version_changed, hash_changed = compute_diff(
            prev_components, cur_components
        )
        initial = False

    diff_obj = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "current": args.current,
            "previous": args.previous if previous_exists else None,
            "initial_baseline": initial,
            "counts": {
                "added": len(added),
                "removed": len(removed),
                "version_changed": len(version_changed),
                "hash_changed": len(hash_changed),
            },
        },
        "added": added,
        "removed": removed,
        "version_changed": version_changed,
        "hash_changed": hash_changed,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    write_json(args.output, diff_obj)

    print(
        f"[sbom-diff] added={len(added)} removed={len(removed)} version_changed={len(version_changed)} hash_changed={len(hash_changed)} initial={initial} -> {args.output}"
    )

    if args.update_baseline and args.previous:
        os.makedirs(os.path.dirname(args.previous) or ".", exist_ok=True)
        try:
            shutil.copy2(args.current, args.previous)
            print(f"[sbom-diff] Baseline updated: {args.previous}")
        except Exception as e:  # pragma: no cover
            print(f"[sbom-diff] Failed to update baseline: {e}", file=sys.stderr)
            return 1

    if (
        (not initial)
        and args.fail - on - change
        and (added or removed or version_changed or hash_changed)
    ):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
