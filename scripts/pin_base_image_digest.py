#!/usr/bin/env python
"""Pin the base image digest in docker/platforms/Dockerfile.platform.

Process:
1. Parse current FROM line (expects format: FROM python:3.11-slim-bookworm as base or similar).
2. Resolve latest digest via `docker pull` and `docker inspect`.
3. Replace FROM with fully qualified @sha256:digest if different.
4. Write updated file & emit summary for CI.

Idempotent: if already pinned to current digest, no change.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

DOCKERFILE = pathlib.Path("docker/platforms/Dockerfile.platform")

FROM_RE = re.compile(
    r"^(FROM\s+python:3\.11-slim-bookworm)(?:@sha256:[0-9a-f]{64})?(\s+AS\s+\w+)?$", re.IGNORECASE
)


def sh(*cmd: str) -> str:
    try:
        out = subprocess.check_output(cmd, text=True)
        return out.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}\n{e.output}", file=sys.stderr)
        raise


def find_from_line(lines):
    for i, line in enumerate(lines):
        if line.upper().startswith("FROM python:3.11-slim-bookworm".upper()):
            return i
    raise SystemExit("No FROM python:3.11-slim-bookworm line found")


def get_current_digest(ref: str) -> str:
    # Pull & inspect
    sh("docker", "pull", ref)
    inspect = sh("docker", "inspect", "--format", "{{index .RepoDigests 0}}", ref)
    # format: python:3.11-slim-bookworm@sha256:....
    if "@sha256:" not in inspect:
        raise SystemExit(f"Unexpected RepoDigest: {inspect}")
    return inspect.split("@sha256:", 1)[1]


def main():
    if not DOCKERFILE.exists():
        print(f"Missing {DOCKERFILE}", file=sys.stderr)
        return 1
    lines = DOCKERFILE.read_text().splitlines()
    idx = find_from_line(lines)
    m = FROM_RE.match(lines[idx].strip())
    if not m:
        print("FROM line does not match expected pattern; skipping.")
        return 0
    base, stage = m.group(1), m.group(2) or ""
    current_line = lines[idx].strip()
    print(f"Current base line: {current_line}")
    digest = get_current_digest("python:3.11-slim-bookworm")
    desired = f"{base}@sha256:{digest}{stage}".rstrip()
    if current_line.lower() == desired.lower():
        print("Already pinned to latest digest; no change.")
        return 0
    lines[idx] = desired
    DOCKERFILE.write_text("\n".join(lines) + "\n")
    print(f"Updated base image to {desired}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
