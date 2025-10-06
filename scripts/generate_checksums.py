#!/usr/bin/env python3
"""Generate checksum bundle (SHA256) for key governance artifacts.

Outputs JSON (checksums.json) with shape:
{
  "generated_at": ISO8601,
  "artifacts": [
     {"path": "schemas/openapi-governance.json", "sha256": "...", "size": 12345},
     {"path": "status/governance-summary.json", "sha256": "...", "size": 456}
  ],
  "aggregate_sha256": "sha256 of concatenated individual sha256 lines"
}

Badge JSON (optional) if --badge-out provided:
{"schemaVersion":1,"label":"checksums","message":"N artifacts","color":"blue"}

Concatenation order is lexical by path to produce deterministic aggregate.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_TARGETS = [
    "schemas/openapi-governance.json",
    "status/governance-summary.json",
    "status/stability-metrics.json",
    "status/operations-classification.json",
    "status/semver-validation.json",
]


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="checksums.json")
    ap.add_argument("--badge-out", help="Optional badge JSON output")
    ap.add_argument("--base", default=".", help="Base directory (schemas branch working tree)")
    ap.add_argument(
        "--include", action="append", help="Additional artifact path(s) relative to base"
    )
    args = ap.parse_args()

    base = Path(args.base)
    targets = list(dict.fromkeys([*(DEFAULT_TARGETS), *(args.include or [])]))

    artifacts = []
    for rel in targets:
        p = base / rel
        if not p.exists():
            continue
        try:
            digest, size = sha256_file(p)
            artifacts.append({"path": rel, "sha256": digest, "size": size})
        except Exception as e:
            print(f"WARN: failed to hash {rel}: {e}", file=sys.stderr)

    artifacts.sort(key=lambda x: x["path"])
    concat = "".join(a["sha256"] for a in artifacts).encode("utf-8")
    aggregate = hashlib.sha256(concat).hexdigest() if artifacts else ""

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "artifacts": artifacts,
        "aggregate_sha256": aggregate,
        "count": len(artifacts),
    }
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.badge_out:
        color = "lightgrey"
        if payload["count"] >= 5:
            color = "blue"
        if payload["count"] >= 7:
            color = "indigo"
        badge = {
            "schemaVersion": 1,
            "label": "checksums",
            "message": f"{payload['count']} artifacts",
            "color": color,
        }
        Path(args.badge_out).write_text(json.dumps(badge), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
