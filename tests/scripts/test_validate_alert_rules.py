import json
import os
import pathlib
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).parents[2] / "scripts" / "validate_alert_rules.py"
PYTHON = sys.executable


def RULES_TEMPLATE(name):
    return {
        "groups": [
            {
                "name": "example",
                "rules": [
                    {
                        "alert": name,
                        "expr": "up == 0",
                        "for": "1m",
                        "labels": {"severity": "critical"},
                        "annotations": {"summary": "Instance down"},
                    }
                ],
            }
        ]
    }


def TAXONOMY_TEMPLATE(name):
    return {
        "alerts": [{"alert": name, "severity": "critical", "runbook": "https://runbooks/" + name}]
    }


def write_file(tmp, name, content):
    p = os.path.join(tmp, name)
    if name.endswith(".yml") or name.endswith(".yaml"):
        import yaml as _y

        with open(p, "w", encoding="utf-8") as f:
            _y.safe_dump(content, f)
    else:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(content, f)
    return p


def run(*args):
    return subprocess.run([PYTHON, str(SCRIPT), *args], capture_output=True, text=True)


def test_validation_passes_basic():
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = write_file(tmp, "rules.yml", RULES_TEMPLATE("TestAlert"))
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("TestAlert"))
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "passed" in r.stdout.lower()


def test_missing_required_label():
    with tempfile.TemporaryDirectory() as tmp:
        # Remove severity label
        rules = RULES_TEMPLATE("TestAlert")
        rules["groups"][0]["rules"][0]["labels"] = {}
        rules_path = write_file(tmp, "rules.yml", rules)
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("TestAlert"))
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path)
        assert r.returncode != 0
        assert "missing required labels" in r.stderr.lower()


def test_additional_required_labels():
    with tempfile.TemporaryDirectory() as tmp:
        rules = RULES_TEMPLATE("TestAlert")
        # Add extra label we'll require
        rules["groups"][0]["rules"][0]["labels"]["scope"] = "global"
        rules_path = write_file(tmp, "rules.yml", rules)
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("TestAlert"))
        # require scope label
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path, "--required-labels", "scope")
        assert r.returncode == 0, r.stdout + r.stderr
        assert "passed" in r.stdout.lower()


def test_additional_required_label_missing():
    with tempfile.TemporaryDirectory() as tmp:
        rules = RULES_TEMPLATE("TestAlert")
        # no scope label present, but we will require it
        rules_path = write_file(tmp, "rules.yml", rules)
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("TestAlert"))
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path, "--required-labels", "scope")
        assert r.returncode != 0
        assert "missing required labels" in r.stderr.lower()


def test_per_alert_label_diff_report():
    import json
    import os
    import tempfile

    import yaml as _y

    with tempfile.TemporaryDirectory() as tmp:
        # taxonomy says critical, rule sets warning
        rules = RULES_TEMPLATE("DiffAlert")
        rules["groups"][0]["rules"][0]["labels"]["severity"] = "warning"
        taxonomy = {"alerts": [{"alert": "DiffAlert", "severity": "critical", "runbook": "rb"}]}
        rules_path = os.path.join(tmp, "rules.yml")
        with open(rules_path, "w", encoding="utf-8") as f:
            _y.safe_dump(rules, f)
        taxonomy_path = os.path.join(tmp, "alerts_taxonomy.json")
        with open(taxonomy_path, "w", encoding="utf-8") as f:
            json.dump(taxonomy, f)
        report_path = os.path.join(tmp, "report.json")
        run("--rules", rules_path, "--taxonomy", taxonomy_path, "--report", report_path)
        # mismatch should be a warning not error (since severity mismatch logic warns)
        data = json.load(open(report_path, encoding="utf-8"))
        assert "DiffAlert" in data["per_alert"]
        per = data["per_alert"]["DiffAlert"]
        # label mismatch recorded
        assert "severity" in per["label_mismatches"]
        assert per["label_mismatches"]["severity"]["rule"] == "warning"
        assert per["label_mismatches"]["severity"]["taxonomy"] == "critical"


def test_schema_version_in_report():
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = write_file(tmp, "rules.yml", RULES_TEMPLATE("SchemaAlert"))
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("SchemaAlert"))
        report_path = os.path.join(tmp, "report.json")
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path, "--report", report_path)
        assert r.returncode == 0
        data = json.load(open(report_path, encoding="utf-8"))
        assert "schema_version" in data and data["schema_version"] >= 2


def test_alert_validation_prom_metrics():
    with tempfile.TemporaryDirectory() as tmp:
        rules_path = write_file(tmp, "rules.yml", RULES_TEMPLATE("MetricAlert"))
        taxonomy_path = write_file(tmp, "alerts_taxonomy.json", TAXONOMY_TEMPLATE("MetricAlert"))
        metrics_path = os.path.join(tmp, "metrics.prom")
        r = run("--rules", rules_path, "--taxonomy", taxonomy_path, "--prom-metrics", metrics_path)
        assert r.returncode == 0
        text = open(metrics_path, encoding="utf-8").read()
        assert "alert_validation_alerts_checked" in text
        assert "alert_validation_failing" in text
        # New severity breakdown metrics
        assert "alert_validation_severity_count" in text
        # Expect at least one severity label, e.g., severity="critical"
        assert 'severity="critical"' in text or 'severity="warning"' in text
