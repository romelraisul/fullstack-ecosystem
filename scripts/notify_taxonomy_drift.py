#!/usr/bin/env python
"""Notify via webhook (Slack-compatible) if taxonomy drift or validation failures are detected.

Usage:
  python scripts/notify_taxonomy_drift.py --rules docker/prometheus_rules.yml --taxonomy alerts_taxonomy.json --webhook $WEBHOOK_URL

Exit codes:
 0 - No drift / no errors
 2 - Drift or validation errors found (still posts message)
 3 - Script error (e.g., IO)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

import yaml


def load_rules(path: str):
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    names = []
    for g in doc.get("groups", []) or []:
        for r in g.get("rules", []) or []:
            if "alert" in r:
                names.append(r["alert"])
    return set(names)


def load_taxonomy(path: str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {e.get("alert"): e for e in data.get("alerts", []) if e.get("alert")}


def build_message(diff: dict[str, Any]):
    if not diff["errors"] and not diff["drift"]:
        return "✅ Alert taxonomy sync OK: all active alerts aligned."
    lines = []
    if diff["errors"]:
        lines.append("*Errors:*")
        for e in diff["errors"]:
            lines.append(f" • {e}")
    if diff["drift"]:
        lines.append("*Drift:*")
        for d in diff["drift"]:
            lines.append(f" • {d}")
    return "\n".join(lines)


def build_blocks(text: str, diff: dict):
    """Return Slack blocks representing the message if richer formatting desired."""
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": text.split("\n")[0][:2900]}}]

    def section(title, items, style):
        if not items:
            return
        joined = "\n".join(f"• {i}" for i in items[:15])
        if len(items) > 15:
            joined += f"\n… (+{len(items) - 15} more)"
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*\n{joined}"}}
        )

    section("Errors", diff.get("errors"), "danger")
    section("Drift", diff.get("drift"), "warning")
    return blocks


def post_webhook(url: str, text: str, diff: dict):
    if os.getenv("TAXONOMY_SLACK_BLOCKS", "0") == "1":
        payload_obj = {"text": text, "blocks": build_blocks(text, diff)}
    else:
        payload_obj = {"text": text}
    payload = json.dumps(payload_obj).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"Webhook post failed HTTP {e.code}: {e.read()}", file=sys.stderr)
    except Exception as ex:
        print(f"Webhook post exception: {ex}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--taxonomy", required=True)
    ap.add_argument("--webhook", default=os.getenv("TAXONOMY_WEBHOOK_URL", ""))
    ap.add_argument(
        "--fail-on-drift", action="store_true", help="Exit non-zero if drift/errors found"
    )
    args = ap.parse_args()

    try:
        rule_names = load_rules(args.rules)
        taxonomy = load_taxonomy(args.taxonomy)
    except Exception as ex:
        print(f"Load error: {ex}", file=sys.stderr)
        sys.exit(3)

    taxonomy_names = set(taxonomy.keys())
    errors = []
    drift = []

    missing_in_taxonomy = sorted(rule_names - taxonomy_names)
    if missing_in_taxonomy:
        errors.append(
            f"{len(missing_in_taxonomy)} active alert(s) missing from taxonomy: {', '.join(missing_in_taxonomy)}"
        )
    unused_taxonomy = sorted(taxonomy_names - rule_names)
    if unused_taxonomy:
        drift.append(
            f"{len(unused_taxonomy)} taxonomy alert(s) not active: {', '.join(unused_taxonomy[:10])}{' ...' if len(unused_taxonomy) > 10 else ''}"
        )

    deprecated_active = [n for n in rule_names if taxonomy.get(n, {}).get("deprecated")]
    if deprecated_active:
        errors.append(f"Deprecated alert(s) still active: {', '.join(deprecated_active)}")

    runbook_missing = [
        n for n in rule_names if taxonomy.get(n, {}).get("runbook") in (None, "", "TBD")
    ]
    if runbook_missing:
        drift.append(
            f"Alerts missing runbook: {', '.join(runbook_missing[:10])}{' ...' if len(runbook_missing) > 10 else ''}"
        )

    diff = {"errors": errors, "drift": drift}
    msg = build_message(diff)
    print(msg)

    if args.webhook:
        post_webhook(args.webhook, msg, diff)
    else:
        print("No webhook URL provided; skipping post.")

    if (errors or drift) and args.fail_on_drift:
        sys.exit(2)


if __name__ == "__main__":
    main()
