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


def test_layout_any_overlap_flag(tmp_path):
    # Two panels intentionally overlapping (same x,y region)
    baseline = [
        {"title": "Panel A", "gridPos": {"x": 0, "y": 0, "w": 4, "h": 3}},
        {"title": "Panel B", "gridPos": {"x": 1, "y": 1, "w": 4, "h": 3}},
    ]
    # Current identical to baseline; overlap should be detected
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    current_path.write_text(json.dumps(baseline), encoding="utf-8")
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
    # Expect non-zero exit due to overlap (validation failing)
    assert (
        res.returncode != 0
    ), f"Expected non-zero exit for overlap, got 0 stdout={res.stdout} stderr={res.stderr}"
    prom_text = prom_out.read_text()
    metrics = parse_metrics(prom_text)
    assert (
        metrics.get("layout_any_overlap", [0])[0] == 1
    ), f"Expected layout_any_overlap=1 got {metrics.get('layout_any_overlap')}\n{prom_text}"
    assert (
        metrics.get("layout_overlapping_pairs", [0])[0] >= 1
    ), f"Expected at least one overlapping pair.\n{prom_text}"
    assert metrics.get("layout_failing", [0])[0] == 1, f"Expected layout_failing=1\n{prom_text}"
