import json
import math
import os
import pathlib
import subprocess
import sys
import textwrap
import time
import tracemalloc

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "resource_usage_trend.py"

MOCK_STATS = """NAME                CPU %     MEM USAGE / LIMIT     NET I/O
container_x         42.0%     512MiB/2GiB           100kB/50kB
""".strip()


def _run_with_buckets(tmp_path, bucket_count):
    boundaries = ",".join(str(i) for i in range(bucket_count))
    jsonl = tmp_path / f"trend_{bucket_count}.jsonl"
    prom = tmp_path / f"trend_{bucket_count}.prom"
    shim = tmp_path / f"shim_{bucket_count}.py"
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
    start = time.time()
    tracemalloc.start()
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
    mem_bucket_lines = [
        l for l in prom_text.splitlines() if l.startswith("resource_trend_mem_perc_bucket")
    ]
    # bucket_count explicit + 1 +Inf
    expected = bucket_count + 1
    assert (
        len(cpu_bucket_lines) == expected
    ), f"Unexpected CPU bucket count={len(cpu_bucket_lines)} expected={expected}"
    assert (
        len(mem_bucket_lines) == expected
    ), f"Unexpected Mem bucket count={len(mem_bucket_lines)} expected={expected}"
    # Performance scaling: allow a small logarithmic factor; baseline <0.5s for 100, scale loosely.
    base_limit = 0.5 * max(1, math.log(bucket_count + 2, 10))
    limit = float(os.getenv("HIST_RUNTIME_LIMIT_SEC", base_limit))
    assert elapsed < limit, f"Histogram generation too slow: {elapsed:.3f}s (limit {limit:.3f}s)"
    # Memory peak should stay modest (<2MB) for these sizes.
    mem_limit = int(os.getenv("HIST_MEM_LIMIT_BYTES", str(2 * 1024 * 1024)))
    assert (
        peak < mem_limit
    ), f"Peak memory too high {peak / 1024:.1f} KiB (limit {mem_limit / 1024:.1f} KiB)"


def test_large_histogram_bucket_parametrized(tmp_path):
    for count in (10, 50, 100):
        _run_with_buckets(tmp_path, count)
