#!/usr/bin/env python3
"""Generate an alerts taxonomy changelog (added/removed/changed metadata) vs previous commit.

Outputs markdown to stdout or --out path.

Change categories:
- Added alerts
- Removed alerts
- Modified (severity/scope/category/description/for/windows/runbook changed)
- Deprecated newly (non-deprecated -> deprecated)
- Undeprecated (deprecated -> active)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FIELDS_COMPARE = ["severity", "scope", "category", "for", "windows", "runbook", "description"]

ROOT = Path(__file__).resolve().parent.parent
CUR_PATH = ROOT.parent / "alerts_taxonomy.json"


def load_current():
    return json.loads(CUR_PATH.read_text(encoding="utf-8"))


def load_previous() -> dict | None:
    try:
        prev = subprocess.check_output(
            ["git", "show", "HEAD^:alerts_taxonomy.json"], cwd=str(ROOT.parent), text=True
        )
        return json.loads(prev)
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None


def index(alerts):
    return {a["alert"]: a for a in alerts}


def summarize_changes(prev, cur):
    prev_idx = index(prev.get("alerts", [])) if prev else {}
    cur_idx = index(cur.get("alerts", []))

    added = sorted(set(cur_idx) - set(prev_idx))
    removed = sorted(set(prev_idx) - set(cur_idx))
    modified = []
    severity_changes = []
    newly_deprecated = []
    undeprecated = []

    for name in sorted(set(cur_idx).intersection(prev_idx)):
        p = prev_idx[name]
        c = cur_idx[name]
        # state transitions
        if not p.get("deprecated") and c.get("deprecated"):
            newly_deprecated.append(name)
        if p.get("deprecated") and not c.get("deprecated"):
            undeprecated.append(name)
        diffs = {}
        for f in FIELDS_COMPARE:
            if p.get(f) != c.get(f):
                diffs[f] = (p.get(f), c.get(f))
                if f == "severity":
                    severity_changes.append((name, p.get("severity"), c.get("severity")))
        if diffs:
            modified.append((name, diffs))
    return added, removed, modified, newly_deprecated, undeprecated, severity_changes


def format_md(added, removed, modified, newly_dep, undep, severity_changes):
    lines = ["# Alert Taxonomy Changelog", ""]
    if not any([added, removed, modified, newly_dep, undep, severity_changes]):
        lines.append("No changes vs previous commit.")
        return "\n".join(lines) + "\n"
    if added:
        lines.append("## Added")
        for a in added:
            lines.append(f"- {a}")
        lines.append("")
    if removed:
        lines.append("## Removed")
        for r in removed:
            lines.append(f"- {r}")
        lines.append("")
    if newly_dep:
        lines.append("## Newly Deprecated")
        for n in newly_dep:
            lines.append(f"- {n}")
        lines.append("")
    if undep:
        lines.append("## Undeprecated")
        for u in undep:
            lines.append(f"- {u}")
        lines.append("")
    if modified:
        lines.append("## Modified")
        for name, diffs in modified:
            parts = []
            for k, (old, new) in diffs.items():
                parts.append(f"{k}: '{old}' -> '{new}'")
            lines.append(f"- {name}: " + "; ".join(parts))
        lines.append("")
    if severity_changes:
        lines.append("## Severity Transitions")
        for name, old, new in severity_changes:
            lines.append(f"- {name}: {old} -> {new}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="Write markdown changelog to file path")
    args = ap.parse_args()

    cur = load_current()
    prev = load_previous()
    added, removed, modified, newly_dep, undep, severity_changes = summarize_changes(
        prev or {}, cur
    )
    md = format_md(added, removed, modified, newly_dep, undep, severity_changes)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)


if __name__ == "__main__":
    main()
