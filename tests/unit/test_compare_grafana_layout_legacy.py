import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

pytest.skip(
    "Duplicated by tests/scripts/test_compare_grafana_layout.py; skipping to avoid import mismatch.",
    allow_module_level=True,
)

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "compare_grafana_layout.py"

BASELINE = [
    {"title": "CPU", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4}},
    {"title": "Memory", "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4}},
    {"title": "Latency", "gridPos": {"x": 0, "y": 4, "w": 12, "h": 4}},
]


def run_script(args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def write_json(tmpdir, name, payload):
    p = pathlib.Path(tmpdir) / name
    p.write_text(json.dumps(payload))
    return p


def test_pass_within_tolerance():
    with tempfile.TemporaryDirectory() as td:
        baseline_path = write_json(td, "baseline.json", BASELINE)
        # Current panels drift by 1 in x,y within tolerance 2
        # Shift panels slightly but keep them non-overlapping
        current = [
            {"title": "CPU", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {
                "title": "Memory",
                "gridPos": {"x": 6, "y": 1, "w": 6, "h": 4},
            },  # y drift within tolerance
            {"title": "Latency", "gridPos": {"x": 0, "y": 4, "w": 12, "h": 4}},
        ]
        write_json(td, "current.json", {"panels": current})
        code, out, err = run_script(
            [
                "--baseline",
                str(baseline_path),
                "--current-glob",
                str(pathlib.Path(td) / "current.json"),
                "--pos-tolerance",
                "2",
                "--min-panels",
                "3",
            ]
        )
        assert code == 0, f"Expected success; stderr={err} stdout={out}"
        assert "tolerated minor drift" in out


def test_fail_major_drift():
    with tempfile.TemporaryDirectory() as td:
        baseline_path = write_json(td, "baseline.json", BASELINE)
        current = [
            {"title": "CPU", "gridPos": {"x": 10, "y": 10, "w": 6, "h": 4}},  # large move
            {"title": "Memory", "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4}},
            {"title": "Latency", "gridPos": {"x": 0, "y": 4, "w": 12, "h": 4}},
        ]
        write_json(td, "current.json", {"panels": current})
        code, out, err = run_script(
            [
                "--baseline",
                str(baseline_path),
                "--current-glob",
                str(pathlib.Path(td) / "current.json"),
                "--pos-tolerance",
                "2",
            ]
        )
        assert code != 0, "Expected failure for major drift"
        assert "major drift" in err or "major drift" in out


def test_missing_panel():
    with tempfile.TemporaryDirectory() as td:
        baseline_path = write_json(td, "baseline.json", BASELINE)
        current = [
            {"title": "CPU", "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"title": "Memory", "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4}},
        ]  # Missing Latency
        write_json(td, "current.json", {"panels": current})
        code, out, err = run_script(
            [
                "--baseline",
                str(baseline_path),
                "--current-glob",
                str(pathlib.Path(td) / "current.json"),
                "--pos-tolerance",
                "2",
            ]
        )
        assert code != 0
        assert "Missing required panels" in err
