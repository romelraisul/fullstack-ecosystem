import json
import os
import pathlib
import subprocess
import sys
import textwrap
import time
import tracemalloc

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOCK_STATS = """NAME                CPU %     MEM USAGE / LIMIT     NET I/O
container_x         7.5%      64MiB/1GiB            5kB/2kB
""".strip()


@pytest.mark.slow
def test_histogram_extreme_bucket_stress(tmp_path):
    bucket_count = 500
    boundaries = ",".join(str(i) for i in range(bucket_count))
    jsonl = tmp_path / "trend_stress.jsonl"
    prom = tmp_path / "trend_stress.prom"
    shim = tmp_path / "shim_stress.py"
    shim.write_text(
        textwrap.dedent(
            f"""
    import subprocess as _sp, sys
    import scripts.resource_usage_trend as mod
    MOCK = {json.dumps(MOCK_STATS)}
    real_run = _sp.run
    def fake_run(cmd, capture_output=False, text=False):
        if isinstance(cmd, list) and cmd[:2]==['docker','stats']:
            class R: ...
            r = R(); r.returncode=0; r.stdout=MOCK; r.stderr=''; return r
        return real_run(cmd, capture_output=capture_output, text=text)
    mod.subprocess.run = fake_run
    sys.argv=['x','--jsonl','{jsonl.as_posix()}','--prom','{prom.as_posix()}','--hist-cpu','{boundaries}','--hist-mem','{boundaries}']
    mod.main()
    """
        )
    )
    tracemalloc.start()
    start = time.time()
    res = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0,'{ROOT.as_posix()}'); exec(open('{shim.as_posix()}').read())",
        ],
        capture_output=True,
        text=True,
    )
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    assert res.returncode == 0, res.stderr
    prom_text = prom.read_text()
    cpu_bucket_lines = [
        l for l in prom_text.splitlines() if l.startswith("resource_trend_cpu_perc_bucket")
    ]
    expected = bucket_count + 1
    assert (
        len(cpu_bucket_lines) == expected
    ), f"CPU bucket line count mismatch {len(cpu_bucket_lines)} != {expected}"
    # Thresholds (overridable via env for CI fine-tuning)
    time_limit = float(os.getenv("HIST_STRESS_RUNTIME_LIMIT_SEC", "2.0"))
    mem_limit = int(os.getenv("HIST_STRESS_MEM_LIMIT_BYTES", str(4 * 1024 * 1024)))
    assert elapsed < time_limit, f"Stress histogram runtime {elapsed:.2f}s exceeds {time_limit}s"
    assert (
        peak < mem_limit
    ), f"Stress histogram peak memory {peak / 1024:.1f} KiB exceeds {mem_limit / 1024:.1f} KiB"
