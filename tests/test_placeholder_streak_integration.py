import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path("scripts/placeholder_streak_guard.py")


def invoke(metrics_obj, streak_path, max_runs=5):
    metrics_path = os.path.join(os.path.dirname(streak_path), "stability-metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_obj, f)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--metrics",
        metrics_path,
        "--streak-file",
        streak_path,
        "--max",
        str(max_runs),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_sequential_placeholder_then_real_resets():
    tmpdir = tempfile.mkdtemp()
    try:
        streak_file = os.path.join(tmpdir, ".placeholder-streak")
        # First placeholder
        c1, out1, err1 = invoke({"placeholder": True, "window_stability_ratio": 1.0}, streak_file)
        assert c1 == 0 and "placeholder streak" in out1.lower()
        # Second placeholder
        c2, out2, err2 = invoke({"placeholder": True, "window_stability_ratio": 1.0}, streak_file)
        assert c2 == 0
        with open(streak_file, encoding="utf-8") as f:
            assert f.read().strip() == "2"
        # Real metrics resets
        real = {
            "schema_version": 1,
            "timestamp": "t",
            "breaking": False,
            "window_total_count": 1,
            "window_stable_count": 1,
            "window_stability_ratio": 1.0,
            "current_stable_streak": 1,
            "longest_stable_streak": 1,
        }
        c3, out3, err3 = invoke(real, streak_file)
        assert c3 == 0 and "reset" in out3.lower()
        with open(streak_file, encoding="utf-8") as f:
            assert f.read().strip() == "0"
        # Another placeholder should start at 1 again
        c4, out4, err4 = invoke({"placeholder": True, "window_stability_ratio": 1.0}, streak_file)
        assert c4 == 0
        with open(streak_file, encoding="utf-8") as f:
            assert f.read().strip() == "1"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
