#!/usr/bin/env python3
"""Sync / validate alert taxonomy against Prometheus rules.

Usage:
    python scripts/sync_alert_taxonomy.py --rules docker/prometheus_rules.yml --taxonomy ../../alerts_taxonomy.json --check
    python scripts/sync_alert_taxonomy.py --rules docker/prometheus_rules.yml --taxonomy ../../alerts_taxonomy.json --scaffold
    python scripts/sync_alert_taxonomy.py --taxonomy ../../alerts_taxonomy.json --emit-markdown docs/alerts_taxonomy.md
    python scripts/sync_alert_taxonomy.py --taxonomy ../../alerts_taxonomy.json --emit-jsonl docs/alerts_annotations.jsonl
        python scripts/sync_alert_taxonomy.py --taxonomy ../../alerts_taxonomy.json --lint
        python scripts/sync_alert_taxonomy.py --taxonomy ../../alerts_taxonomy.json --emit-html docs/alerts_taxonomy.html

Modes:
  --check    : Exit 0 if all alerts in rules.yml are present in taxonomy alerts[] array, else non‑zero
  --scaffold : Append missing alerts with minimal placeholder objects (does not overwrite existing)

This script purposefully does not remove extra taxonomy entries (allows future / retired docs to persist until manually cleaned).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import shorten

import yaml

REQUIRED_FIELDS = ["alert", "group", "severity", "description"]
ALLOWED_SCOPES = {"service", "system", "multi-service", "dimension", "route", "agent", "fleet"}
ALLOWED_CATEGORIES = {
    "latency",
    "error-rate",
    "throughput",
    "quality",
    "guardrail",
    "availability",
    "latency-acceleration",
    "error-acceleration",
    "error-budget-burn",
    "error-burn-fast",
    "error-burn-slow",
}
ALLOWED_SEVERITIES = {"info", "warning", "critical"}

PLACEHOLDER = {
    "severity": "unknown",
    "slo": None,
    "scope": "unknown",
    "category": "unspecified",
    "description": "TODO: add description",
    "expr_summary": "TODO",
    "for": "",
    "windows": [],
    "runbook": "TODO: fill runbook guidance",
    "labels": {},
}


def load_rules(rules_path: Path) -> list[dict]:
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    groups = data.get("groups", [])
    alerts = []
    for g in groups:
        gname = g.get("name")
        # Some groups may have an empty 'rules:' block with only commented entries which yaml parses as None.
        # Treat a None rules value as an empty list so deprecating (commenting out) all alerts in a group does not break validation.
        for r in g.get("rules") or []:
            if "alert" in r:
                alerts.append(
                    {
                        "alert": r["alert"],
                        "group": gname,
                        "for": r.get("for", ""),
                        "labels": r.get("labels", {}),
                    }
                )
    return alerts


def load_taxonomy(taxonomy_path: Path) -> dict:
    raw = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    if isinstance(raw, list):  # legacy format
        return {"schema_version": "0.9.0", "last_updated": None, "alerts": raw}
    return raw


def write_taxonomy(taxonomy_path: Path, obj: dict):
    obj["last_updated"] = datetime.now(timezone.utc).isoformat()
    taxonomy_path.write_text(json.dumps(obj, indent=4, sort_keys=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--taxonomy", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--scaffold", action="store_true")
    ap.add_argument("--emit-markdown", metavar="PATH")
    ap.add_argument("--emit-jsonl", metavar="PATH")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--emit-html", metavar="PATH")
    args = ap.parse_args()

    rules_path = Path(args.rules) if args.rules else None
    taxonomy_path = Path(args.taxonomy)

    rules_alerts = load_rules(rules_path) if rules_path else []
    tax_obj = load_taxonomy(taxonomy_path)
    taxonomy_alerts = tax_obj.get("alerts", [])

    tax_index = {a["alert"]: a for a in taxonomy_alerts}

    missing = []
    for ra in rules_alerts:
        if ra["alert"] not in tax_index:
            missing.append(ra)

    if args.lint:
        problems = []  # hard failures
        warnings = []  # soft notices (non-zero exit only if strict requested)
        max_age_days = int(os.environ.get("TAXONOMY_DEPRECATION_MAX_DAYS", "0") or 0)
        strict_deprecation = os.environ.get("TAXONOMY_DEPRECATION_STRICT", "0") == "1"
        now = datetime.now(timezone.utc)
        for a in taxonomy_alerts:
            scope = a.get("scope")
            cat = a.get("category")
            sev = a.get("severity")
            if scope and scope not in ALLOWED_SCOPES:
                problems.append(f"Invalid scope '{scope}' in {a.get('alert')}")
            if cat and cat not in ALLOWED_CATEGORIES:
                problems.append(f"Invalid category '{cat}' in {a.get('alert')}")
            if sev and sev not in ALLOWED_SEVERITIES:
                problems.append(f"Invalid severity '{sev}' in {a.get('alert')}")
            # coherence: if windows provided ensure 'for' duration appears or is subset
            fw = a.get("for", "").strip()
            wins = a.get("windows", []) or []
            if fw and wins:
                # If any window string contains fw or vice versa assume ok; else warn
                if not any(fw in w or w in fw for w in wins):
                    problems.append(
                        f"For/window mismatch in {a.get('alert')}: for={fw} windows={wins}"
                    )
            # deprecated note suggestion
            if a.get("deprecated") and "deprecated" not in (a.get("description") or "").lower():
                problems.append(
                    f"Deprecated alert {a.get('alert')} should mention deprecation in description"
                )
            if a.get("deprecated") and max_age_days > 0:
                ds = a.get("deprecated_since")
                if ds:
                    try:
                        dt = datetime.fromisoformat(ds.replace("Z", "+00:00"))
                        if now - dt > timedelta(days=max_age_days):
                            msg = f"Deprecated alert {a.get('alert')} exceeds max deprecation age {max_age_days}d (since {ds})"
                            if strict_deprecation:
                                problems.append(msg)
                            else:
                                warnings.append(msg)
                    except Exception:
                        problems.append(
                            f"Deprecated alert {a.get('alert')} has invalid deprecated_since format (expected ISO8601)"
                        )
            # Placeholder content checks (only for non-deprecated alerts)
            if not a.get("deprecated"):
                desc = (a.get("description") or "").strip().lower()
                if desc.startswith("todo") or desc in {"", "tbd", "placeholder"}:
                    problems.append(f"Active alert {a.get('alert')} has placeholder description")
                runbook = (a.get("runbook") or "").strip().lower()
                if runbook.startswith("todo") or runbook in {"", "tbd", "placeholder"}:
                    problems.append(f"Active alert {a.get('alert')} has placeholder runbook")
        if problems or warnings:
            if problems:
                print("Lint failures:")
                for p in problems:
                    print(" -", p)
            if warnings:
                print("Lint warnings:")
                for w in warnings:
                    print(" -", w)
            if problems:
                sys.exit(3)
        else:
            print("Lint OK: scopes & categories valid.")
        # fall through to possible emit modes

    if args.check and rules_path:
        if missing:
            print("Missing alerts in taxonomy (add or run scaffold):")
            for m in missing:
                print(f"  - {m['alert']} (group={m['group']})")
            sys.exit(1)
        # validate required fields
        bad = []
        for a in taxonomy_alerts:
            for f in REQUIRED_FIELDS:
                if f not in a or a[f] in (None, ""):
                    bad.append((a.get("alert"), f))
        if bad:
            print("Alerts with missing required fields:")
            for alert, field in bad:
                print(f"  - {alert}: missing {field}")
            sys.exit(2)
        print("Taxonomy validation OK: all rule alerts covered.")
        return

    if args.scaffold and rules_path:
        changed = False
        for m in missing:
            scaffold = {**PLACEHOLDER}
            scaffold.update(
                {
                    "alert": m["alert"],
                    "group": m["group"],
                    "for": m.get("for", ""),
                    "labels": m.get("labels", {}),
                }
            )
            taxonomy_alerts.append(scaffold)
            changed = True
            print(f"Added scaffold for {m['alert']}")
        if changed:
            tax_obj["alerts"] = sorted(taxonomy_alerts, key=lambda x: x.get("alert", ""))
            write_taxonomy(taxonomy_path, tax_obj)
            print("Taxonomy updated with scaffolds.")
        else:
            print("No missing alerts; taxonomy unchanged.")
    # Emit markdown if requested
    if args.emit_markdown:
        header = [
            "Alert",
            "Group",
            "Severity",
            "SLO",
            "Scope",
            "Category",
            "For",
            "Windows",
            "Description",
        ]
        lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
        for a in taxonomy_alerts:
            windows = " / ".join(a.get("windows", []) or [])
            desc = shorten(a.get("description", ""), width=120, placeholder="…")
            row = [
                a.get("alert", ""),
                a.get("group", ""),
                a.get("severity", ""),
                (a.get("slo") or ""),
                a.get("scope", ""),
                a.get("category", ""),
                a.get("for", ""),
                windows,
                desc,
            ]
            lines.append("| " + " | ".join(row) + " |")
        Path(args.emit_markdown).write_text(
            "# Alert Taxonomy\n\n" + "\n".join(lines) + "\n", encoding="utf-8"
        )
        print(f"Wrote markdown table to {args.emit_markdown}")

    if args.emit_jsonl:
        out_lines = []
        for a in taxonomy_alerts:
            minimal = {
                k: a.get(k)
                for k in [
                    "alert",
                    "group",
                    "severity",
                    "scope",
                    "category",
                    "for",
                    "windows",
                    "slo",
                ]
            }
            out_lines.append(json.dumps(minimal, sort_keys=True))
        Path(args.emit_jsonl).write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        print(f"Wrote JSONL annotations to {args.emit_jsonl}")

    if args.emit_html:
        # Simple standalone HTML (no external CSS) for portability
        rows = []
        for a in taxonomy_alerts:
            dep = a.get("deprecated")
            cls = "deprecated" if dep else ""
            windows = " / ".join(a.get("windows", []) or [])
            rows.append(
                f"<tr class='{cls}'><td>{a.get('alert', '')}</td><td>{a.get('group', '')}</td><td>{a.get('severity', '')}</td>"
                f"<td>{a.get('slo') or ''}</td><td>{a.get('scope', '')}</td><td>{a.get('category', '')}</td>"
                f"<td>{a.get('for', '')}</td><td>{windows}</td><td>{(a.get('description') or '').replace('<', '&lt;')}</td></tr>"
            )
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Alert Taxonomy</title>
<style>
body {{ font-family: system-ui, Arial, sans-serif; margin: 1.5rem; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 8px; vertical-align: top; }}
th {{ background:#f5f5f5; position: sticky; top:0; z-index:2; }}
tr.deprecated td {{ background: #faf0f0; color:#777; text-decoration: line-through; }}
caption {{ text-align:left; font-weight:600; margin-bottom:8px; }}
.meta {{ font-size:12px; color:#666; margin-bottom:12px; }}
</style></head><body>
<h1>Alert Taxonomy</h1>
<div class='meta'>Generated {datetime.utcnow().isoformat()}Z · schema {tax_obj.get("schema_version")}</div>
<table>
<thead><tr><th>Alert</th><th>Group</th><th>Severity</th><th>SLO</th><th>Scope</th><th>Category</th><th>For</th><th>Windows</th><th>Description</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
<p style='margin-top:2rem;font-size:12px;'>Deprecated alerts are shown struck-through. Source: alerts_taxonomy.json</p>
</body></html>"""
        Path(args.emit_html).write_text(html, encoding="utf-8")
        print(f"Wrote HTML taxonomy to {args.emit_html}")

    # If user specified only emit/lint modes that's fine; if nothing chosen show help
    if not any(
        [args.check, args.scaffold, args.emit_markdown, args.emit_jsonl, args.emit_html, args.lint]
    ):
        ap.error(
            "Specify at least one action flag: --check / --scaffold / --emit-markdown / --emit-jsonl / --emit-html / --lint"
        )


if __name__ == "__main__":
    main()
