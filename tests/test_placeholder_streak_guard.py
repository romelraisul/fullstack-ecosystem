import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path("scripts/placeholder_streak_guard.py")


def run_guard(metrics_obj, max_runs=3, streak_file=None):
    tmpdir = tempfile.mkdtemp()
    try:
        metrics_path = os.path.join(tmpdir, "stability-metrics.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_obj, f)
        if streak_file is None:
            streak_file = os.path.join(tmpdir, ".placeholder-streak")
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--metrics",
            metrics_path,
            "--streak-file",
            streak_file,
            "--max",
            str(max_runs),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip(), streak_file
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_streak_increments_until_limit():
    streak_file = None
    # 3 allowed, 4th should fail
    for i in range(1, 5):
        code, out, err, streak_file = run_guard(
            {"placeholder": True, "window_stability_ratio": 1.0},
            max_runs=3,
            streak_file=streak_file,
        )
        if i < 4:
            assert code == 0, f"Unexpected non-zero before limit: {code}, err={err}"
        else:
            assert code == 4, f"Expected failure exit code 4 on exceeding streak, got {code}"


def test_streak_resets_on_non_placeholder():
    streak_file = None
    # first placeholder
    code, *_ = run_guard(
        {"placeholder": True, "window_stability_ratio": 1.0}, max_runs=3, streak_file=streak_file
    )
    assert code == 0
    # non placeholder resets
    code, *_ = run_guard(
        {
            "schema_version": 1,
            "breaking": False,
            "timestamp": "t",
            "window_total_count": 1,
            "window_stable_count": 1,
            "window_stability_ratio": 1.0,
            "current_stable_streak": 1,
            "longest_stable_streak": 1,
        },
        max_runs=3,
        streak_file=streak_file,
    )
    assert code == 0
    # another placeholder should start at 1 again
    code, *_ = run_guard(
        {"placeholder": True, "window_stability_ratio": 1.0}, max_runs=3, streak_file=streak_file
    )
    assert code == 0


def test_missing_metrics_file_error():
    # invoke with missing metrics path
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--metrics",
        "does-not-exist.json",
        "--streak-file",
        ".sf",
        "--max",
        "2",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "metrics file missing" in proc.stderr


def test_invalid_json_metrics():
    tmpdir = tempfile.mkdtemp()
    try:
        metrics_path = os.path.join(tmpdir, "bad.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            f.write("{bad json")
        streak_path = os.path.join(tmpdir, ".placeholder-streak")
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--metrics",
            metrics_path,
            "--streak-file",
            streak_path,
            "--max",
            "2",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 3
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
