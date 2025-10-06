import json
import pathlib
import subprocess
import sys

SCRIPT = pathlib.Path("scripts/generate_stability_metrics.py").resolve()


def run_script(args):
    cmd = [sys.executable, str(SCRIPT)] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def test_metrics_initial_run(tmp_path):
    history = tmp_path / "history.jsonl"
    status = tmp_path / "status.json"
    metrics = tmp_path / "metrics.json"
    badge = tmp_path / "badge.json"

    status.write_text(json.dumps({"breaking": False, "incompatible": 0, "deleted_or_removed": 0}))
    code, out, err = run_script(
        [
            "--history",
            str(history),
            "--current-status",
            str(status),
            "--output-metrics",
            str(metrics),
            "--badge-json",
            str(badge),
            "--window",
            "5",
        ]
    )
    assert code == 0, err
    data = json.loads(metrics.read_text())
    assert data["total_runs"] == 1
    assert data["breaking_runs"] == 0
    assert data["last_score"] == 100
    b = json.loads(badge.read_text())
    assert "score:100" in b["message"]
    assert "stable" in b["message"]
    assert "streak:" in b["message"]
    # streak should be 1 on first run
    assert data["current_stable_streak"] == 1
    assert data["longest_stable_streak"] == 1
    assert "window_mean_score" in data


def test_metrics_with_history_window(tmp_path):
    history = tmp_path / "history.jsonl"
    # Pre-seed 3 stable and 2 breaking entries
    pre_lines = [
        {"timestamp": "2025-10-01T00:00:00Z", "breaking": False, "score": 100},
        {"timestamp": "2025-10-01T01:00:00Z", "breaking": False, "score": 95},
        {"timestamp": "2025-10-01T02:00:00Z", "breaking": True, "score": 60},
        {"timestamp": "2025-10-01T03:00:00Z", "breaking": False, "score": 90},
        {"timestamp": "2025-10-01T04:00:00Z", "breaking": True, "score": 50},
    ]
    with open(history, "w", encoding="utf-8") as f:
        for line in pre_lines:
            f.write(json.dumps(line) + "\n")

    status = tmp_path / "status.json"
    status.write_text(json.dumps({"breaking": False, "incompatible": 0, "deleted_or_removed": 0}))
    metrics = tmp_path / "metrics.json"
    badge = tmp_path / "badge.json"

    code, out, err = run_script(
        [
            "--history",
            str(history),
            "--current-status",
            str(status),
            "--output-metrics",
            str(metrics),
            "--badge-json",
            str(badge),
            "--window",
            "5",
        ]
    )
    assert code == 0, err
    data = json.loads(metrics.read_text())
    # After appending new stable run, total runs should be 6
    assert data["total_runs"] == 6
    assert data["breaking_runs"] == 2
    assert data["stable_runs"] == 4
    assert data["last_breaking"] is False
    assert 0 <= data["last_score"] <= 100
    # Window size = 5 -> last 5 entries (including new run). Ensure window_total_runs=5
    assert data["window_total_runs"] == 5
    # Badge should include score, percentage and streak
    b = json.loads(badge.read_text())
    assert "score:" in b["message"] and "% stable" in b["message"] and "streak:" in b["message"]
    # Current streak after a stable run following breaking entries should be >0
    assert data["current_stable_streak"] >= 1
    assert data["longest_stable_streak"] >= data["current_stable_streak"]
    assert "window_mean_score" in data
