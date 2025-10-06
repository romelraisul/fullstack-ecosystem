import json
import pathlib
import re
import subprocess
import sys
import textwrap
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2] / "scripts"
WRAPPER = ROOT / "run_observability_validations.py"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _parse_prometheus_metrics(raw: str) -> dict[str, list[dict[str, Any]]]:
    """Very small Prometheus text format parser for simple 'name{labels} value' lines.
    Returns mapping name -> list of samples with {'labels': {..}, 'value': float}.
    Skips HELP/TYPE/comment and blank lines.
    """
    metrics: dict[str, list[dict[str, Any]]] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # pattern: name{label="v"} value  OR name value
        m = re.match(
            r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(\{(?P<labels>[^}]*)\})?\s+(?P<value>[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)",
            line,
        )
        if not m:
            continue
        name = m.group("name")
        labels_raw = m.group("labels") or ""
        labels: dict[str, str] = {}
        if labels_raw:
            for part in re.split(r",(?![^\"]*\")", labels_raw):
                if not part:
                    continue
                k, v = part.split("=", 1)
                v = v.strip('"')
                labels[k.strip()] = v
        try:
            value = float(m.group("value"))
        except ValueError:
            continue
        metrics.setdefault(name, []).append({"labels": labels, "value": value})
    return metrics


def test_wrapper_produces_combined_artifacts(tmp_path):
    # Minimal baseline/current with 5 panels (meets default min-panels=5)
    baseline = [
        {"title": f"Panel {i}", "gridPos": {"x": i * 2, "y": 0, "w": 2, "h": 2}} for i in range(5)
    ]
    current = [
        {"title": f"Panel {i}", "gridPos": {"x": i * 2, "y": 0, "w": 2, "h": 2}} for i in range(5)
    ]
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    write_json(baseline_path, baseline)
    write_json(current_path, current)

    # Minimal alert rules + taxonomy with matching severity
    rules_yaml = textwrap.dedent(
        """
        groups:
          - name: test
            rules:
              - alert: SampleAlert
                expr: up == 1
                labels:
                  severity: critical
        """
    ).strip()
    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(rules_yaml, encoding="utf-8")

    taxonomy = {"alerts": [{"alert": "SampleAlert", "severity": "critical", "runbook": "r"}]}
    taxonomy_path = tmp_path / "taxonomy.json"
    write_json(taxonomy_path, taxonomy)

    combined_metrics = tmp_path / "combined.prom"
    index_json = tmp_path / "index.json"
    layout_report = tmp_path / "layout_report.json"
    alerts_report = tmp_path / "alerts_report.json"

    cmd = [
        sys.executable,
        str(WRAPPER),
        "--layout-baseline",
        str(baseline_path),
        "--layout-current-glob",
        str(current_path),
        "--alerts-rules",
        str(rules_path),
        "--alerts-taxonomy",
        str(taxonomy_path),
        "--layout-report",
        str(layout_report),
        "--alerts-report",
        str(alerts_report),
        "--out-metrics",
        str(combined_metrics),
        "--out-index",
        str(index_json),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Wrapper failed stdout={res.stdout} stderr={res.stderr}"

    # Validate index structure (explicit required key set + value checks)
    assert index_json.exists()
    idx = json.loads(index_json.read_text())
    required_top_keys = {"schema_version", "layout", "alerts", "overall_status"}
    assert required_top_keys.issubset(
        idx.keys()
    ), f"Index missing keys: {required_top_keys - set(idx.keys())}"
    assert idx["schema_version"] == 1
    assert idx["overall_status"] == "pass"
    for section in ("layout", "alerts"):
        assert "exit_code" in idx[section]
        assert isinstance(idx[section]["exit_code"], int)
        assert idx[section]["exit_code"] == 0, f"{section} exit_code non-zero"
        assert "report" in idx[section]
    # Ensure no unexpected extra top-level keys (forward-compat tolerant but we record)
    set(idx.keys()) - required_top_keys
    # (Do not fail for unexpected yet; could log in future)

    # Validate reports exist and have expected schema versions
    lr = json.loads(layout_report.read_text())
    ar = json.loads(alerts_report.read_text())
    assert lr["schema_version"] == 2
    assert ar["schema_version"] == 2

    # Combined metrics should contain a known metric from each validator and have sane values
    metrics_text = combined_metrics.read_text()
    assert "layout_total_panels" in metrics_text, "layout metrics missing"
    assert "alert_validation_errors" in metrics_text, "alert metrics missing"
    parsed = _parse_prometheus_metrics(metrics_text)

    # Required metric presence
    for required_metric in (
        "layout_total_panels",
        "layout_changes_detected",
        "alert_validation_errors",
        "alert_validation_severity_count",
    ):
        assert (
            required_metric in parsed
        ), f"Missing expected metric {required_metric} in combined output"

    # layout_total_panels should equal 5 with no labels
    ltp_samples = parsed["layout_total_panels"]
    assert (
        len(ltp_samples) == 1 and ltp_samples[0]["value"] == 5
    ), f"Unexpected layout_total_panels samples: {ltp_samples}"
    assert ltp_samples[0]["labels"] == {}

    # alert_validation_errors should be 0
    ave_samples = parsed["alert_validation_errors"]
    assert all(
        s["value"] == 0 for s in ave_samples
    ), f"Non-zero alert_validation_errors: {ave_samples}"

    # severity count must have exactly one sample with severity="critical" value 1
    sev_samples = [
        s
        for s in parsed["alert_validation_severity_count"]
        if s["labels"].get("severity") == "critical"
    ]
    assert (
        len(sev_samples) == 1 and sev_samples[0]["value"] == 1.0
    ), f"Expected critical severity count=1 got {sev_samples}"
    # ensure no negative metric values across all parsed metrics
    negatives = [(name, s) for name, samples in parsed.items() for s in samples if s["value"] < 0]
    assert not negatives, f"Found negative metric values: {negatives}"

    # If future schema versions appear, flag (informational)
    assert lr["schema_version"] <= 2
    assert ar["schema_version"] <= 2
