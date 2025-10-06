#!/usr/bin/env python3
"""Check that packages pinned in requirements-ai.in align with versions in main lock.

Rules:
  - For each non-comment, non-empty line in requirements-ai.in of form 'pkg[extras]==X' or 'pkg==X'
    ensure requirements.txt contains same package name (case-insensitive) at identical version.
  - If a package appears in AI file but not main lock => warning (fail by default).
  - If version mismatch => failure.

Exit codes: 0 aligned, 1 mismatch.
"""

from __future__ import annotations

import argparse
import re
import sys

PIN_RE = re.compile(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?==([^\s#;]+)")
LOCK_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s#;]+)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ai", default="requirements-ai.in")
    p.add_argument("--lock", default="requirements.txt")
    p.add_argument(
        "--allow-missing", action="store_true", help="Do not fail if package missing in main lock"
    )
    return p.parse_args()


def load_lock(path: str):
    versions = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = LOCK_RE.match(line)
            if not m:
                continue
            versions[m.group(1).lower()] = m.group(2)
    return versions


def main():
    a = parse_args()
    lock_versions = load_lock(a.lock)
    errors = []
    with open(a.ai, encoding="utf-8") as f:
        for _idx, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = PIN_RE.match(line)
            if not m:
                continue
            name, ver = m.group(1).lower(), m.group(2)
            lock_ver = lock_versions.get(name)
            if not lock_ver:
                msg = f"missing in main lock: {name} (ai:{ver})"
                (errors if not a.allow_missing else print("[warn]", msg))
                if not a.allow_missing:
                    errors.append(msg)
            elif lock_ver != ver:
                errors.append(f"version mismatch {name}: ai:{ver} lock:{lock_ver}")
    if errors:
        print("[ai-align] FAIL:")
        for e in errors:
            print(" -", e, file=sys.stderr)
        return 1
    print("[ai-align] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
