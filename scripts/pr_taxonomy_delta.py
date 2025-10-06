#!/usr/bin/env python3
"""Generate a markdown summary of taxonomy changes between two refs.

Usage (env driven for CI):
  BASE_REF=<base> HEAD_REF=<head> python scripts/pr_taxonomy_delta.py

If BASE_REF/HEAD_REF not provided, falls back to 'origin/main' and 'HEAD'.
Outputs markdown to stdout.

Change categories:
- Added alerts
- Removed alerts
- Modified core fields (group, severity, scope, category, description, runbook, deprecated flag)
- Severity transitions summary
- Runbook completeness delta (active only)
- Risk metrics delta (if metrics script fields exist)
"""

from __future__ import annotations

import difflib
import json
import os
import subprocess

TAXONOMY_FILE = "alerts_taxonomy.json"
CORE_FIELDS = ["group", "severity", "scope", "category", "description", "runbook", "deprecated"]


def load_taxonomy_at(ref: str) -> dict:
    try:
        raw = subprocess.check_output(["git", "show", f"{ref}:{TAXONOMY_FILE}"], text=True)
        return json.loads(raw)
    except subprocess.CalledProcessError:
        return {"alerts": []}


def index_alerts(obj: dict) -> dict[str, dict]:
    return {a.get("alert"): a for a in obj.get("alerts", []) if a.get("alert")}


def placeholder(text: str | None) -> bool:
    if not text:
        return True
    t = text.strip().lower()
    return (not t) or t.startswith("todo") or t in {"tbd", "placeholder"}


def runbook_completeness(alerts: list[dict]) -> float:
    active = [a for a in alerts if not a.get("deprecated")]
    if not active:
        return 100.0
    good = sum(1 for a in active if not placeholder(a.get("runbook")))
    return round(good / len(active) * 100, 2)


def main():
    base_ref = os.environ.get("BASE_REF") or os.environ.get("GITHUB_BASE_REF") or "origin/main"
    head_ref = os.environ.get("HEAD_REF") or os.environ.get("GITHUB_HEAD_REF") or "HEAD"

    base_tax = load_taxonomy_at(base_ref)
    head_tax = load_taxonomy_at(head_ref)

    base_idx = index_alerts(base_tax)
    head_idx = index_alerts(head_tax)

    base_names = set(base_idx.keys())
    head_names = set(head_idx.keys())

    added = sorted(head_names - base_names)
    removed = sorted(base_names - head_names)
    common = sorted(base_names & head_names)

    modified = []
    severity_transitions = []

    for name in common:
        b = base_idx[name]
        h = head_idx[name]
        changes = {}
        for f in CORE_FIELDS:
            if b.get(f) != h.get(f):
                # For multi-line description comparison, optionally provide short diff context
                if f == "description":
                    diff_lines = list(
                        difflib.unified_diff(
                            (b.get(f) or "").splitlines(),
                            (h.get(f) or "").splitlines(),
                            lineterm="",
                            fromfile="before",
                            tofile="after",
                            n=1,
                        )
                    )
                    changes[f] = diff_lines[:10]  # truncate
                else:
                    changes[f] = {"before": b.get(f), "after": h.get(f)}
        if changes:
            modified.append({"alert": name, "changes": changes})
        if b.get("severity") != h.get("severity"):
            severity_transitions.append(f"{name}: {b.get('severity')} -> {h.get('severity')}")

    base_runbook = runbook_completeness(list(base_idx.values()))
    head_runbook = runbook_completeness(list(head_idx.values()))

    # Risk deltas (if severities present)
    def weight(sev: str | None):
        sev = (sev or "").lower()
        return {"critical": 5, "high": 3, "medium": 2, "low": 1}.get(sev, 1)

    def weight_total(alerts_dict: dict[str, dict]):
        return sum(weight(a.get("severity")) for a in alerts_dict.values())

    base_wt = weight_total(base_idx)
    head_wt = weight_total(head_idx)

    # Simple risk churn for PR: sum weights of added + removed
    risk_added = sum(weight(head_idx[a].get("severity")) for a in added)
    risk_removed = sum(weight(base_idx[a].get("severity")) for a in removed)
    risk_churn = risk_added + risk_removed

    md = []
    md.append("### Alert Taxonomy Delta\n")
    md.append(f"Base: `{base_ref}`  →  Head: `{head_ref}`\n")
    md.append(
        f"Total alerts: {len(base_names)} → {len(head_names)} (Δ {len(head_names) - len(base_names)})\n"
    )

    if added:
        md.append(f"**Added ({len(added)}):** " + ", ".join(added) + "\n")
    if removed:
        md.append(f"**Removed ({len(removed)}):** " + ", ".join(removed) + "\n")
    if not added and not removed:
        md.append("No additions or removals.\n")

    if modified:
        md.append(f"\n**Modified ({len(modified)}):**\n")
        for m in modified[:25]:  # cap list
            md.append(f"- `{m['alert']}`:")
            for f, val in m["changes"].items():
                if isinstance(val, list):
                    md.append(f"  - {f}: (diff)\n")
                else:
                    md.append(f"  - {f}: {val['before']} → {val['after']}")
        if len(modified) > 25:
            md.append(f"- ... {len(modified) - 25} more modified alerts truncated ...")
    else:
        md.append("\nNo modified core fields.\n")

    if severity_transitions:
        md.append(f"\n**Severity Transitions ({len(severity_transitions)}):**\n")
        for s in severity_transitions[:30]:
            md.append(f"- {s}")
        if len(severity_transitions) > 30:
            md.append(f"- ... {len(severity_transitions) - 30} more transitions ...")

    md.append(
        f"\n**Runbook Completeness:** {base_runbook:.2f}% → {head_runbook:.2f}% (Δ {head_runbook - base_runbook:+.2f}%)\n"
    )

    md.append(
        f"**Risk Weights:** total weight {base_wt:.0f} → {head_wt:.0f} (Δ {head_wt - base_wt:+.0f}); risk churn (added+removed weight) = {risk_churn}\n"
    )

    print("\n".join(md))


if __name__ == "__main__":
    main()
