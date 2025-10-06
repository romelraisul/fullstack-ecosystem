import json
from pathlib import Path

import pytest
import yaml

RULES_PATH = Path("docker/prometheus_rules.yml")
TAXONOMY_PATH = Path("alerts_taxonomy.json")

REQUIRED_TAXONOMY_FIELDS = {"alert", "severity", "deprecated"}


def load_rules_alert_names():
    data = yaml.safe_load(RULES_PATH.read_text())
    alerts = set()
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            # Only consider actual alerting rules (those with 'alert' key)
            if isinstance(rule, dict) and "alert" in rule:
                alerts.add(rule["alert"].strip())
    return alerts


def load_taxonomy_index():
    tax = json.loads(TAXONOMY_PATH.read_text())
    index = {}
    for entry in tax.get("alerts", []):
        alert_name = entry.get("alert")
        if alert_name:
            index[alert_name] = entry
    return index


def test_prometheus_alerts_present_in_taxonomy():
    active_alerts = load_rules_alert_names()
    taxonomy = load_taxonomy_index()

    missing = [a for a in sorted(active_alerts) if a not in taxonomy]
    assert not missing, f"Alerts missing from taxonomy: {missing}"


def test_taxonomy_required_fields_and_status():
    taxonomy = load_taxonomy_index()
    problems = []
    for name, entry in taxonomy.items():
        missing_fields = REQUIRED_TAXONOMY_FIELDS - set(entry.keys())
        if missing_fields:
            problems.append(f"{name}: missing fields {sorted(missing_fields)}")
        # Basic severity sanity (could be tightened later)
        sev = entry.get("severity")
        if sev and sev.lower() not in {"low", "medium", "high", "critical", "warning", "info"}:
            problems.append(f"{name}: unexpected severity '{sev}'")
    assert not problems, "; ".join(problems)


def test_taxonomy_no_stale_active_entries():
    active_alerts = load_rules_alert_names()
    taxonomy = load_taxonomy_index()

    stale = []
    for name, entry in taxonomy.items():
        # If deprecated == false but alert not in rules, treat as stale
        if not entry.get("deprecated", False) and name not in active_alerts:
            stale.append(name)
    # Allow some legacy placeholders? Keep strict for now.
    assert not stale, f"Taxonomy entries marked active but not found in rules: {stale}"


def test_all_rule_alerts_have_severity_label():
    data = yaml.safe_load(RULES_PATH.read_text())
    missing = []
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            if "alert" in rule:
                labels = rule.get("labels", {}) or {}
                if "severity" not in labels:
                    missing.append(rule["alert"])
    assert not missing, f"Alert rules missing severity label: {missing}"


@pytest.mark.parametrize("field", ["runbook"])  # extensible for future required metadata
def test_active_taxonomy_entries_have_runbook(field):
    taxonomy = load_taxonomy_index()
    missing = []
    for name, entry in taxonomy.items():
        if not entry.get("deprecated", False):
            value = entry.get(field, "").strip()
            if not value or value.lower() in {"tbd", "todo", "pending"}:
                missing.append(name)
    assert not missing, f"Active taxonomy entries missing usable {field}: {missing}"
