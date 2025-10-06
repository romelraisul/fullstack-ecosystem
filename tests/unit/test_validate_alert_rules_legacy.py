import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

pytest.skip(
    "Duplicated by tests/scripts/test_validate_alert_rules.py; skipping to avoid import mismatch.",
    allow_module_level=True,
)

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "validate_alert_rules.py"

TAXONOMY = {
    "alerts": [
        {
            "alert": "HighErrorRate",
            "severity": "critical",
            "runbook": "runbooks/high_error_rate.md",
        },
        {"alert": "SlowLatency", "severity": "warning", "runbook": "runbooks/slow_latency.md"},
    ]
}

RULES_YAML = """
groups:
- name: example
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~\"5..\"}[5m]) > 0.05
    labels:
      severity: critical
      team: core
  - alert: SlowLatency
    expr: histogram_quantile(0.95, sum by (le) (rate(request_latency_seconds_bucket[5m]))) > 1
    labels:
      severity: warning
      team: core
"""

MISSING_LABEL_RULES_YAML = """
groups:
- name: example
  rules:
  - alert: HighErrorRate
    expr: vector(1)
    labels:
      team: core
"""


def run_script(args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_success_with_required_extra_labels():
    with tempfile.TemporaryDirectory() as td:
        taxonomy_path = pathlib.Path(td) / "taxonomy.json"
        rules_path = pathlib.Path(td) / "rules.yml"
        report_path = pathlib.Path(td) / "report.json"
        taxonomy_path.write_text(json.dumps(TAXONOMY))
        rules_path.write_text(RULES_YAML)
        code, out, err = run_script(
            [
                "--rules",
                str(rules_path),
                "--taxonomy",
                str(taxonomy_path),
                "--required-labels",
                "team",
                "--report",
                str(report_path),
            ]
        )
        assert code == 0, f"Expected pass got {code} err={err}"
        report = json.loads(report_path.read_text())
        assert report["error_count"] == 0
        assert "HighErrorRate" in report["alerts_checked"]
        assert "team" in report["required_labels"]


def test_failure_missing_required_label():
    with tempfile.TemporaryDirectory() as td:
        taxonomy_path = pathlib.Path(td) / "taxonomy.json"
        rules_path = pathlib.Path(td) / "rules.yml"
        taxonomy_path.write_text(json.dumps(TAXONOMY))
        rules_path.write_text(MISSING_LABEL_RULES_YAML)
        code, out, err = run_script(
            [
                "--rules",
                str(rules_path),
                "--taxonomy",
                str(taxonomy_path),
                "--required-labels",
                "team",
            ]
        )
        assert code != 0
        assert "missing required labels" in err.lower()
