#!/usr/bin/env python
import argparse
import json
import os
import sys
from typing import Any

import yaml

BASE_REQUIRED_LABELS = {"severity"}
OPTIONAL_LABELS = {"scope", "slo", "category"}


def load_taxonomy(path: str) -> dict[str, dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    mapping = {}
    for entry in data.get("alerts", []):
        alert_name = entry.get("alert")
        if alert_name:
            mapping[alert_name] = entry
    return mapping


def load_rules(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    rules: list[dict[str, Any]] = []
    for group in doc.get("groups", []):
        for rule in group.get("rules", []) or []:
            # Only consider alerting rules (skip pure recording rules with 'record')
            if "alert" in rule:
                enriched = dict(rule)
                enriched["group_name"] = group.get("name")
                rules.append(enriched)
    return rules


def validate_rules(
    rules: list[dict[str, Any]], taxonomy: dict[str, dict[str, Any]], extra_required: set[str]
) -> dict[str, Any]:
    required_labels = BASE_REQUIRED_LABELS | extra_required
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    per_alert_diffs: dict[str, dict[str, Any]] = {}

    taxonomy_names: set[str] = set(taxonomy.keys())
    rule_names: set[str] = {r["alert"] for r in rules}

    # 1. Every alerting rule must exist in taxonomy
    missing_in_taxonomy = sorted(rule_names - taxonomy_names)
    if missing_in_taxonomy:
        errors.append(
            f"{len(missing_in_taxonomy)} alert(s) not in taxonomy: {', '.join(missing_in_taxonomy)}"
        )

    # 2. Deprecated still active
    deprecated_active = [name for name in rule_names if taxonomy.get(name, {}).get("deprecated")]
    if deprecated_active:
        errors.append(f"Deprecated alert(s) still active: {', '.join(deprecated_active)}")

    # 3. Required labels present
    for r in rules:
        labels = r.get("labels", {}) or {}
        missing_labels = required_labels - set(labels.keys())
        if missing_labels:
            errors.append(
                f"Alert {r['alert']} missing required labels: {', '.join(sorted(missing_labels))}"
            )
        # capture label diff vs taxonomy for present alerts
        t = taxonomy.get(r["alert"], {})
        t_labels = {}
        # project taxonomy attributes that map to labels (currently severity only)
        if "severity" in t:
            t_labels["severity"] = t["severity"]
        label_diffs = {}
        for k, v in t_labels.items():
            rv = labels.get(k)
            if rv != v:
                label_diffs[k] = {"rule": rv, "taxonomy": v}
        per_alert_diffs[r["alert"]] = {
            "missing_required_labels": sorted(missing_labels) if missing_labels else [],
            "label_mismatches": label_diffs,
        }

    # 4. Severity mismatch vs taxonomy (warning)
    for r in rules:
        t = taxonomy.get(r["alert"]) or {}
        labels = r.get("labels", {}) or {}
        expected_severity = t.get("severity")
        if (
            expected_severity
            and labels.get("severity")
            and labels["severity"].lower() != expected_severity.lower()
        ):
            warnings.append(
                f"Severity mismatch for {r['alert']}: rule={labels['severity']} taxonomy={expected_severity}"
            )

    # 5. Runbook missing / TBD (warning)
    for name, entry in taxonomy.items():
        if (
            not entry.get("deprecated")
            and (not entry.get("runbook") or entry.get("runbook") in ("TBD", ""))
            and name in rule_names
        ):
            warnings.append(f"Alert {name} active but runbook missing or TBD")

    # 6. Unused taxonomy entries (info)
    unused_taxonomy = sorted(taxonomy_names - rule_names)
    if unused_taxonomy:
        info.append(
            f"{len(unused_taxonomy)} taxonomy alert(s) not currently active: {', '.join(unused_taxonomy)}"
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "alerts_checked": sorted(rule_names),
        "required_labels": sorted(required_labels),
        "taxonomy_size": len(taxonomy_names),
        "per_alert": per_alert_diffs,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate Prometheus alert rules against taxonomy")
    parser.add_argument("--rules", required=True, help="Path to prometheus_rules.yml")
    parser.add_argument("--taxonomy", required=True, help="Path to alerts_taxonomy.json")
    parser.add_argument(
        "--required-labels",
        default="",
        help="Comma separated additional required labels (in addition to base set)",
    )
    parser.add_argument(
        "--report", default="", help="Optional path to write JSON validation report"
    )
    parser.add_argument(
        "--prom-metrics",
        default="",
        help="Optional path to write Prometheus metrics exposition format",
    )
    args = parser.parse_args()

    taxonomy = load_taxonomy(args.taxonomy)
    rules = load_rules(args.rules)
    extra_required = {l.strip() for l in args.required_labels.split(",") if l.strip()}

    report = validate_rules(rules, taxonomy, extra_required)

    # Emit human readable output
    if report["info"]:
        for line in report["info"]:
            print(f"INFO: {line}")
    if report["warnings"]:
        for line in report["warnings"]:
            print(f"WARNING: {line}")
    if report["errors"]:
        for line in report["errors"]:
            print(f"ERROR: {line}", file=sys.stderr)

    success = not report["errors"]
    if success:
        print("Alert rule taxonomy validation passed.")

    if args.report:
        report_dir = os.path.dirname(args.report)
        if report_dir and not os.path.exists(report_dir):
            os.makedirs(report_dir, exist_ok=True)
        json_payload = dict(report)
        json_payload["schema_version"] = 2
        json_payload["error_count"] = len(report["errors"])
        json_payload["warning_count"] = len(report["warnings"])
        try:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(json_payload, f, indent=2)
            print(f"Wrote validation report to {args.report}")
        except Exception as ex:
            print(f"ERROR: Failed writing report {args.report}: {ex}", file=sys.stderr)

    if args.prom_metrics:
        try:
            lines = []

            def m(name, value, help_text):
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            m("alert_validation_errors", len(report["errors"]), "Count of alert validation errors")
            m(
                "alert_validation_warnings",
                len(report["warnings"]),
                "Count of alert validation warnings",
            )
            m("alert_validation_info", len(report["info"]), "Count of informational messages")
            m(
                "alert_validation_alerts_checked",
                len(report["alerts_checked"]),
                "Number of alerting rules checked",
            )
            m(
                "alert_validation_required_labels",
                len(report["required_labels"]),
                "Number of required labels enforced",
            )
            m("alert_validation_taxonomy_size", report["taxonomy_size"], "Size of taxonomy entries")
            m("alert_validation_failing", 0 if success else 1, "Validation failing flag")
            # severity breakdown from rule labels
            severity_counts = {}
            for r in rules:
                sev = (r.get("labels", {}) or {}).get("severity")
                if sev:
                    sev_norm = str(sev).lower()
                    severity_counts[sev_norm] = severity_counts.get(sev_norm, 0) + 1
            for sev, count in sorted(severity_counts.items()):
                # Exposition format with label
                lines.append("# HELP alert_validation_severity_count Count of alerts per severity")
                lines.append("# TYPE alert_validation_severity_count gauge")
                lines.append(f'alert_validation_severity_count{{severity="{sev}"}} {count}')
            with open(args.prom_metrics, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print(f"Wrote alert validation Prometheus metrics to {args.prom_metrics}")
        except Exception as ex:
            print(f"ERROR: Failed writing metrics {args.prom_metrics}: {ex}", file=sys.stderr)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
