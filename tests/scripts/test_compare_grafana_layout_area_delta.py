import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2] / "scripts"
SCRIPT = ROOT / "compare_grafana_layout.py"


def parse_metrics(text):
    metrics = {}
    for ln in text.splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        m = re.match(r"([^\s{]+)(?:\{[^}]*\})?\s+([0-9.eE+-]+)$", ln.strip())
        if m:
            metrics.setdefault(m.group(1), []).append(float(m.group(2)))
    return metrics


def run_layout(baseline, current, tmp_path):
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    current_path.write_text(json.dumps(current), encoding="utf-8")
    prom_out = tmp_path / "layout.prom"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--baseline",
        str(baseline_path),
        "--current-glob",
        str(current_path),
        "--min-panels",
        "2",
        "--prom-metrics",
        str(prom_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res, prom_out.read_text()


def test_layout_area_delta_percent_changes(tmp_path):
    baseline = [
        {"title": "Panel A", "gridPos": {"x": 0, "y": 0, "w": 4, "h": 3}},  # area 12
        {"title": "Panel B", "gridPos": {"x": 4, "y": 0, "w": 4, "h": 3}},  # area 12
    ]
    # Modify Panel B size: increase width by 2 (w=6,h=3 => area 18) delta +6 out of baseline total 24 => 25.0%
    current = [
        {"title": "Panel A", "gridPos": {"x": 0, "y": 0, "w": 4, "h": 3}},
        {"title": "Panel B", "gridPos": {"x": 4, "y": 0, "w": 6, "h": 3}},
    ]
    res, prom_text = run_layout(baseline, current, tmp_path)
    metrics = parse_metrics(prom_text)
    assert (
        res.returncode == 0 or metrics.get("layout_failing", [0])[0] == 0
    ), f"Unexpected failure: {res.returncode} stderr={res.stderr}"
    percent = metrics.get("layout_panel_area_delta_percent", [0])[0]
    assert 24.9 <= percent <= 25.1, f"Expected ~25% area delta got {percent} prom=\n{prom_text}"
    # Confirm cumulative area delta metric is 6
    cum_area = metrics.get("layout_area_cumulative_delta", [0])[0]
    assert cum_area == 6, f"Expected cumulative area delta 6 got {cum_area} prom=\n{prom_text}"


def test_layout_area_delta_percent_zero_when_identical(tmp_path):
    baseline = [
        {"title": "Panel A", "gridPos": {"x": 0, "y": 0, "w": 4, "h": 3}},
        {"title": "Panel B", "gridPos": {"x": 4, "y": 0, "w": 4, "h": 3}},
    ]
    current = json.loads(json.dumps(baseline))
    res, prom_text = run_layout(baseline, current, tmp_path)
    metrics = parse_metrics(prom_text)
    assert (
        res.returncode == 0
    ), f"Expected success identical layout got exit={res.returncode} stderr={res.stderr}"
    percent = metrics.get("layout_panel_area_delta_percent", [99])[0]
    assert percent == 0, f"Expected 0 area delta percent got {percent} prom=\n{prom_text}"
    cum_area = metrics.get("layout_area_cumulative_delta", [1])[0]
    assert cum_area == 0, f"Expected 0 cumulative area delta got {cum_area} prom=\n{prom_text}"
