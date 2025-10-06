#!/usr/bin/env python3
"""
license_scan.py

Generates a JSON license inventory using pip-licenses and enforces a denylist.

Usage:
  python security/license_scan.py --deny MIT-0,GPL-3.0-only --output licenses.json

Exit codes:
  0 - Success / no blocked licenses found
  1 - Blocked license detected
  2 - Execution / tooling error
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[license-scan] Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        raise


def ensure_tool(tool: str, package: str | None = None) -> None:
    if shutil.which(tool):
        return
    pkg = package or tool
    print(f"[license-scan] Installing missing tool: {pkg}")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg], check=True)


def collect_licenses(format_version: int = 1) -> list[dict]:
    """Collect license information using pip-licenses."""
    base_cmd = [
        sys.executable,
        "-m",
        "piplicenses",
        "--format",
        "json",
        "--with-authors",
        "--with-urls",
        "--with-description",
    ]
    if format_version >= 2:
        base_cmd.append("--with-license-file")
    output = run(base_cmd)
    try:
        data = json.loads(output)
        if not isinstance(data, list):
            raise ValueError("Unexpected pip-licenses JSON root type")
        return data
    except json.JSONDecodeError as e:
        print("[license-scan] Failed to parse pip-licenses output as JSON", file=sys.stderr)
        raise SystemExit(2) from e


def enforce_policy(records: list[dict], deny: set[str]) -> list[dict]:
    violations = []
    for rec in records:
        lic = (rec.get("License") or "").strip()
        # Some packages list multiple licenses separated by ; or ,
        normalized = [l.strip() for part in lic.split(";") for l in part.split(",") if l.strip()]
        if any(l in deny for l in normalized):
            rec["__violation__"] = True
            violations.append(rec)
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deny", default="", help="Comma-separated list of disallowed licenses (exact match)"
    )
    parser.add_argument("--output", default="licenses-report.json", help="Output JSON file path")
    parser.add_argument(
        "--format-version", type=int, default=1, help="Internal: toggle extra columns (default:1)"
    )
    args = parser.parse_args()

    ensure_tool("piplicenses", "pip-licenses")

    deny = {d.strip() for d in args.deny.split(",") if d.strip()}
    records = collect_licenses(args.format_version)
    violations = enforce_policy(records, deny)

    meta = {
        "total_packages": len(records),
        "denylist": sorted(deny),
        "violation_count": len(violations),
    }
    report = {
        "meta": meta,
        "packages": records,
        "violations": violations,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[license-scan] Wrote report to {out_path} (violations={len(violations)})")

    if violations:
        print("[license-scan] Blocked licenses detected:")
        for v in violations:
            print(f"  - {v.get('Name')} : {v.get('License')}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError:
        sys.exit(2)
