#!/usr/bin/env python3
"""Parse an openapi-diff textual report to structured JSON + optional badge & status.

Features:
  * Heuristic classification (regex) of each non-empty line.
  * External JSON config for custom patterns.
  * Outputs:
      - Main structured JSON (issues, counters, summary)
      - Optional badge JSON (shields.io style)
      - Optional status JSON (compact summary for dashboards)

Config JSON format (array of {"label": str, "pattern": str} objects):
[
  {"label": "deleted", "pattern": "deleted"},
  {"label": "removed", "pattern": "removed"}
]

Usage:
  python scripts/parse_openapi_breaking_report.py \
      --input breaking-diff.txt \
      --output breaking-diff.json \
      --config scripts/breaking_patterns.json \
      --badge-json breaking-badge.json \
      --status-json breaking-status.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PatternDef:
    label: str
    regex: re.Pattern


DEFAULT_PATTERNS: list[tuple[str, str]] = [
    ("deleted", r"deleted"),
    ("removed", r"removed"),
    ("incompatible", r"incompatible"),
    ("required_change", r"required field"),
    ("response_changed", r"response changed"),
]


def load_patterns(config_path: Path | None) -> list[PatternDef]:
    pairs: list[tuple[str, str]]
    if config_path and config_path.exists():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            pairs = []
            for obj in raw:
                if not isinstance(obj, dict):
                    continue
                label = obj.get("label")
                pattern = obj.get("pattern")
                if isinstance(label, str) and isinstance(pattern, str):
                    pairs.append((label, pattern))
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: failed to load config {config_path}: {exc}", file=sys.stderr)
            pairs = []
    else:
        pairs = []
    if not pairs:
        pairs = DEFAULT_PATTERNS
    compiled: list[PatternDef] = []
    for label, pat in pairs:
        try:
            compiled.append(PatternDef(label=label, regex=re.compile(pat, re.I)))
        except re.error as exc:  # pragma: no cover - invalid regex
            print(f"Ignoring invalid regex for label {label}: {exc}", file=sys.stderr)
    return compiled


def classify_line(line: str, patterns: list[PatternDef]) -> list[str]:
    tags = [p.label for p in patterns if p.regex.search(line)]
    return tags or ["other"]


def iter_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if line:
                yield line


def build_summary(issues: list[dict]) -> dict:
    counters: dict[str, int] = {}
    for issue in issues:
        for tag in issue["tags"]:
            counters[tag] = counters.get(tag, 0) + 1
    total = sum(counters.values())
    summary = {
        "total_lines": total,
        "deleted_or_removed": counters.get("deleted", 0) + counters.get("removed", 0),
        "incompatible": counters.get("incompatible", 0),
    }
    return counters, summary


def make_badge(summary: dict) -> dict:
    breaking = summary.get("incompatible", 0) or summary.get("deleted_or_removed", 0)
    label = "api stability"
    if breaking:
        color = "red"
        message = f"breaking:{breaking}"
    else:
        color = "brightgreen"
        message = "stable"
    return {"schemaVersion": 1, "label": label, "message": message, "color": color}


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Parse openapi-diff text to structured JSON")
    ap.add_argument("--input", required=True, help="Input text file (breaking-diff.txt)")
    ap.add_argument("--output", required=True, help="Output structured JSON path")
    ap.add_argument("--config", help="Optional pattern config JSON")
    ap.add_argument("--badge-json", help="Optional shields.io badge JSON path")
    ap.add_argument("--status-json", help="Optional compact status JSON path")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])
    in_path = Path(ns.input)
    out_path = Path(ns.output)
    config_path = Path(ns.config) if ns.config else None

    if not in_path.exists():
        data = {"issues": [], "counters": {}, "summary": {"total_lines": 0}}
        out_path.write_text(json.dumps(data, indent=2))
        print(f"Input missing; wrote empty structure -> {out_path}")
        return 0

    patterns = load_patterns(config_path)
    issues = []
    for line in iter_lines(in_path):
        tags = classify_line(line, patterns)
        issues.append({"text": line, "tags": tags})

    counters, summary = build_summary(issues)
    data = {"issues": issues, "counters": counters, "summary": summary}
    out_path.write_text(json.dumps(data, indent=2))

    # Optional badge output
    if ns.badge_json:
        badge_path = Path(ns.badge_json)
        badge_path.write_text(json.dumps(make_badge(summary), indent=2))

    # Optional status output (narrow JSON for dashboards)
    if ns.status_json:
        status = {
            "breaking": summary.get("incompatible", 0) + summary.get("deleted_or_removed", 0) > 0,
            "incompatible": summary.get("incompatible", 0),
            "deleted_or_removed": summary.get("deleted_or_removed", 0),
            "total": summary.get("total_lines", 0),
        }
        Path(ns.status_json).write_text(json.dumps(status, indent=2))

    print(f"Parsed {len(issues)} lines -> {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
