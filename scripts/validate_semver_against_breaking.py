#!/usr/bin/env python3
"""Validate semantic version progression against breaking change detection.

Policy:
- If breaking changes detected (flag file or env) then MAJOR must bump vs previous.
- If MAJOR bumped but no breaking changes -> policy violation.
- If non-breaking and only MINOR bumped where PATCH would suffice -> warning (not failure).

Inputs:
  --current openapi file path (JSON or YAML) OR --current-version string
  --previous openapi file path (optional) OR --previous-version string
  --breaking-flag file path containing 'true'/'false' OR --breaking bool
  --out path for JSON summary (default semver-validation.json)

Exit codes:
 0 success (policy satisfied or only warnings)
 2 policy violation (fail)
 3 unexpected error

Output JSON fields:
  {
    "previous": "1.2.3" | null,
    "current": "1.3.0",
    "breaking": true/false,
    "status": "ok"|"fail"|"warn",
    "messages": ["..."],
    "expected_version_hint": "2.0.0" (optional)
  }
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def extract_version_from_openapi(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return None
    # naive search for info.version
    m = re.search(r"info\s*:\s*\n(?:.*\n)*?version\s*:\s*([\'\"]?)([0-9]+\.[0-9]+\.[0-9]+)\1", text)
    if m:
        return m.group(2)
    m2 = re.search(r'"version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"', text)
    if m2:
        return m2.group(1)
    return None


def parse_semver(v: str | None) -> tuple[int, int, int] | None:
    if not v:
        return None
    m = SEMVER_RE.match(v.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_major(v: tuple[int, int, int]) -> str:
    return f"{v[0] + 1}.0.0"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--current")
    p.add_argument("--current-version")
    p.add_argument("--previous")
    p.add_argument("--previous-version")
    p.add_argument("--breaking-flag")
    p.add_argument("--breaking", choices=["true", "false"])
    p.add_argument("--out", default="semver-validation.json")
    args = p.parse_args()

    messages = []
    status = "ok"

    current_version = (
        args.current_version
        or extract_version_from_openapi(args.current)
        or os.environ.get("CURRENT_API_VERSION")
    )
    previous_version = (
        args.previous_version
        or extract_version_from_openapi(args.previous)
        or os.environ.get("PREVIOUS_API_VERSION")
    )

    if not current_version:
        messages.append("Could not determine current version")
        status = "fail"
        result = {
            "previous": previous_version,
            "current": current_version,
            "breaking": None,
            "status": status,
            "messages": messages,
        }
        open(args.out, "w", encoding="utf-8").write(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 2

    prev_tuple = parse_semver(previous_version) if previous_version else None
    curr_tuple = parse_semver(current_version)
    if curr_tuple is None:
        messages.append(f"Current version {current_version} is not valid semver X.Y.Z")
        status = "fail"

    # Determine breaking
    breaking = None
    if args.breaking is not None:
        breaking = args.breaking == "true"
    elif args.breaking_flag and os.path.exists(args.breaking_flag):
        with contextlib.suppress(Exception):
            breaking = open(args.breaking_flag, encoding="utf-8").read().strip().lower() == "true"

    if breaking is None:
        # Default to False if undetermined
        breaking = False
        messages.append("Breaking flag not found; defaulting to false")

    expected_hint = None

    if prev_tuple and curr_tuple:
        maj_delta = curr_tuple[0] - prev_tuple[0]
        min_delta = curr_tuple[1] - prev_tuple[1]
        patch_delta = curr_tuple[2] - prev_tuple[2]
        if breaking:
            # Must bump major strictly
            if maj_delta < 1:
                status = "fail"
                expected_hint = bump_major(prev_tuple)
                messages.append(
                    f"Breaking changes detected but version did not bump major (prev {previous_version} -> current {current_version}). Expected at least {expected_hint}."
                )
        else:
            # No breaking: major bump is suspicious
            if maj_delta > 0:
                status = "fail"
                messages.append(
                    f"Major version bumped without breaking changes (prev {previous_version} -> current {current_version})."
                )
            elif maj_delta == 0 and min_delta > 0 and patch_delta == 0:
                # purely minor bump; suggest patch if stability unaffected
                if status == "ok":
                    status = "warn"
                messages.append(
                    f"No breaking changes; consider patch bump instead of minor ({previous_version} -> {current_version})."
                )
    elif not prev_tuple:
        messages.append("Previous version not found or invalid; treating as first release.")

    result = {
        "previous": previous_version,
        "current": current_version,
        "breaking": breaking,
        "status": status,
        "messages": messages,
    }
    if expected_hint:
        result["expected_version_hint"] = expected_hint

    open(args.out, "w", encoding="utf-8").write(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

    if status == "fail":
        return 2
    return 0


if __name__ == "__main__":
    try:
        code = main()
        sys.exit(code)
    except Exception as e:
        print(json.dumps({"status": "fail", "messages": [f"Unhandled error: {e}"]}))
        sys.exit(3)
