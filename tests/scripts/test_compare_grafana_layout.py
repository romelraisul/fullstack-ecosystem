import json
import os
import pathlib
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).parents[2] / "scripts" / "compare_grafana_layout.py"
PYTHON = sys.executable


def write_json(tmp, name, obj):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def run(*args):
    return subprocess.run([PYTHON, str(SCRIPT), *args], capture_output=True, text=True)


def BASELINE_PANEL_TEMPLATE(title, x, y):
    return {
        "title": title,
        "gridPos": {"x": x, "y": y, "w": 4, "h": 3},
    }


def test_pass_within_tolerance():
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE(f"P{i}", i * 4, 0) for i in range(3)]
        current = [BASELINE_PANEL_TEMPLATE(f"P{i}", i * 4 + 1, 0) for i in range(3)]  # drift x by 1
        baseline_path = write_json(tmp, "baseline.json", baseline)
        write_json(tmp, "current.json", {"panels": current})
        r = run(
            "--baseline",
            baseline_path,
            "--current-glob",
            os.path.join(tmp, "current.json"),
            "--pos-tolerance",
            "1",
            "--min-panels",
            "1",
        )
        assert r.returncode == 0, r.stderr + r.stdout
        assert "tolerated minor drift" in r.stdout


def test_fail_major_drift():
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0)]
        current = [BASELINE_PANEL_TEMPLATE("P1", 5, 0)]  # drift by 5 beyond tolerance 1
        baseline_path = write_json(tmp, "baseline.json", baseline)
        write_json(tmp, "current.json", {"panels": current})
        r = run(
            "--baseline",
            baseline_path,
            "--current-glob",
            os.path.join(tmp, "current.json"),
            "--pos-tolerance",
            "1",
            "--min-panels",
            "1",
        )
        assert r.returncode != 0
        assert "major drift" in r.stderr


def test_missing_panel():
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0), BASELINE_PANEL_TEMPLATE("P2", 4, 0)]
        current = [BASELINE_PANEL_TEMPLATE("P1", 0, 0)]  # P2 missing
        baseline_path = write_json(tmp, "baseline.json", baseline)
        write_json(tmp, "current.json", {"panels": current})
        r = run("--baseline", baseline_path, "--current-glob", os.path.join(tmp, "current.json"))
        assert r.returncode != 0
        assert "Missing required panels" in r.stderr


def test_size_change_reporting():
    """Ensure size change captured in JSON report."""
    import json
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0)]
        # Same position but different size
        current = [{"title": "P1", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 5}}]
        baseline_path = write_json(tmp, "baseline.json", baseline)
        write_json(tmp, "current.json", {"panels": current})
        report_path = os.path.join(tmp, "report.json")
        r = run(
            "--baseline",
            baseline_path,
            "--current-glob",
            os.path.join(tmp, "current.json"),
            "--min-panels",
            "1",
            "--report",
            report_path,
        )
        # size change alone should not fail (pass status)
        assert r.returncode == 0, r.stderr + r.stdout
        data = json.load(open(report_path, encoding="utf-8"))
        assert data["size_changes_minor"], data
        assert data["size_change_percent_baseline"] > 0, data


def test_size_threshold_gating_fail():
    """If size change percent exceeds threshold, script should fail."""
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0), BASELINE_PANEL_TEMPLATE("P2", 4, 0)]
        # Change size of both panels -> 100% size change
        current = [
            {"title": "P1", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"title": "P2", "gridPos": {"x": 4, "y": 0, "w": 5, "h": 4}},
        ]
        baseline_path = write_json(tmp, "baseline.json", baseline)
        current_path = write_json(tmp, "current.json", {"panels": current})
        report_path = os.path.join(tmp, "report.json")
        r = run(
            "--baseline",
            baseline_path,
            "--current-glob",
            current_path,
            "--size-threshold",
            "10",
            "--report",
            report_path,
        )
        assert r.returncode != 0, r.stdout + r.stderr
        data = json.load(open(report_path, encoding="utf-8"))
        assert data["size_threshold_breach"] is True
        assert data["schema_version"] >= 2


def test_prom_metrics_output():
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0)]
        current = [BASELINE_PANEL_TEMPLATE("P1", 1, 0)]  # minor drift
        baseline_path = write_json(tmp, "baseline.json", baseline)
        current_path = write_json(tmp, "current.json", {"panels": current})
        metrics_path = os.path.join(tmp, "metrics.prom")
        # Provide tolerance so drift of 1 is minor and not failing
        r = run(
            "--baseline",
            baseline_path,
            "--current-glob",
            current_path,
            "--pos-tolerance",
            "1",
            "--prom-metrics",
            metrics_path,
            "--min-panels",
            "1",
        )
        assert r.returncode == 0, r.stderr + r.stdout
        text = open(metrics_path, encoding="utf-8").read()
        assert "layout_minor_drift_panels" in text
        assert "layout_failing" in text
        # New area aggregation metrics should be present
        assert "layout_total_area_current" in text
        assert "layout_total_area_baseline" in text
        assert "layout_area_changed_panels" in text
        assert "layout_area_cumulative_delta" in text


def test_prom_metrics_missing_panels_metric():
    with tempfile.TemporaryDirectory() as tmp:
        baseline = [BASELINE_PANEL_TEMPLATE("P1", 0, 0), BASELINE_PANEL_TEMPLATE("P2", 4, 0)]
        current = [BASELINE_PANEL_TEMPLATE("P1", 0, 0)]  # P2 missing
        baseline_path = write_json(tmp, "baseline.json", baseline)
        current_path = write_json(tmp, "current.json", {"panels": current})
        metrics_path = os.path.join(tmp, "metrics.prom")
        run(
            "--baseline",
            baseline_path,
            "--current-glob",
            current_path,
            "--pos-tolerance",
            "1",
            "--prom-metrics",
            metrics_path,
            "--min-panels",
            "1",
        )
        # Should fail due to missing panel, but still produce metrics file
        assert os.path.exists(metrics_path)
        text = open(metrics_path, encoding="utf-8").read()
        assert "layout_missing_panels" in text
        assert "layout_total_panels" in text
