import json
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync_alert_taxonomy.py"
RULES = REPO_ROOT / "docker" / "prometheus_rules.yml"

BASIC_ALERT = {
    "alert": "TestAlertPlaceholder",
    "group": "dummy",
    "severity": "warning",
    "description": "TODO: add description",
    "runbook": "TODO: fill runbook guidance",
}


def run_lint(tax_obj):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "alerts_taxonomy.json"
        json.dump(tax_obj, tmp.open("w"), indent=2)
        cmd = [sys.executable, str(SCRIPT), "--rules", str(RULES), "--taxonomy", str(tmp), "--lint"]
        return subprocess.run(cmd, capture_output=True, text=True)


def test_placeholder_detection_fails():
    tax = {"schema_version": "1.0.0", "last_updated": None, "alerts": [BASIC_ALERT]}
    res = run_lint(tax)
    assert (
        res.returncode != 0
    ), f"Expected lint failure, got success: stdout={res.stdout} stderr={res.stderr}"
    assert "placeholder description" in (res.stdout + res.stderr).lower()
    assert "placeholder runbook" in (res.stdout + res.stderr).lower()


def test_fixed_content_passes():
    fixed = {
        **BASIC_ALERT,
        "description": "Fires when test condition holds",
        "runbook": "Check logs and restart",
    }
    tax = {"schema_version": "1.0.0", "last_updated": None, "alerts": [fixed]}
    res = run_lint(tax)
    assert (
        res.returncode == 0
    ), f"Expected lint success, got failure: stdout={res.stdout} stderr={res.stderr}"
