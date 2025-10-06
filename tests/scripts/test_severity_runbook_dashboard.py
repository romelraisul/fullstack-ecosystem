import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "severity_runbook_dashboard.py"
TAXONOMY = {
    "alerts": [
        {"alert": "A1", "severity": "critical", "runbook": "Investigate X", "deprecated": False},
        {"alert": "A2", "severity": "low", "runbook": "TODO: fill", "deprecated": False},
        {"alert": "A3", "severity": "medium", "runbook": "See docs", "deprecated": True},
    ]
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def test_severity_dashboard_outputs(tmp_path):
    tax = tmp_path / "alerts_taxonomy.json"
    html = tmp_path / "dashboard.html"
    prom = tmp_path / "metrics.prom"
    tax.write_text(json.dumps(TAXONOMY))
    res = run(
        [
            sys.executable,
            str(SCRIPT),
            "--taxonomy",
            str(tax),
            "--html",
            str(html),
            "--prom",
            str(prom),
        ]
    )
    assert res.returncode == 0, res.stderr
    assert html.exists() and html.read_text().startswith("<!DOCTYPE html>")
    text = prom.read_text()
    assert "taxonomy_alerts_total" in text
    assert 'severity="critical"' in text
    assert "taxonomy_alerts_runbook_coverage_percent" in text
