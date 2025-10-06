#!/usr/bin/env python3
"""Generate a constraints.txt from a pip-compile style requirements.txt.

This strips hashes and environment markers to produce pure 'pkg==ver' lines for reuse.
"""

from __future__ import annotations

import argparse
import re

LOCK_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--lock", default="requirements.txt")
    p.add_argument("--output", default="constraints.txt")
    return p.parse_args()


def main():
    a = parse_args()
    seen = set()
    lines = []
    with open(a.lock, encoding="utf-8") as f:
        for line in f:
            m = LOCK_RE.match(line)
            if not m:
                continue
            name = m.group(1).lower()
            if name in seen:
                continue
            seen.add(name)
            lines.append(f"{m.group(1)}=={m.group(2)}\n")
    with open(a.output, "w", encoding="utf-8") as f:
        f.write("# Auto-generated constraints derived from requirements.txt\n")
        f.writelines(sorted(lines))
    print(f"[constraints] Wrote {len(lines)} constraints -> {a.output}")


if __name__ == "__main__":
    main()
