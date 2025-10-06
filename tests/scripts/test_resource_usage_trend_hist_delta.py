import contextlib
import json
import os
import pathlib
import subprocess
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "resource_usage_trend.py"

# Two consecutive samples to exercise delta logic
MOCK_SAMPLE_1 = """NAME                CPU %     MEM USAGE / LIMIT     NET I/O
container_a         10.0%     100MiB/1GiB           10kB/5kB
""".strip()
MOCK_SAMPLE_2 = """NAME                CPU %     MEM USAGE / LIMIT     NET I/O
container_a         15.0%     120MiB/1GiB           18kB/9kB
""".strip()


def run(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_histograms_and_deltas(tmp_path):
    driver = tmp_path / "driver_hist.py"
    jsonl = tmp_path / "trend.jsonl"
    prom = tmp_path / "trend.prom"
    driver.write_text(
        textwrap.dedent(
            f"""
    import subprocess as _sp, sys
    import scripts.resource_usage_trend as mod
    samples = [{json.dumps(MOCK_SAMPLE_1)}, {json.dumps(MOCK_SAMPLE_2)}]
    state = {{'i':0}}
    real_run = _sp.run
    def fake_run(cmd, capture_output=False, text=False):
        if isinstance(cmd, list) and cmd[:2]==['docker','stats']:
            class R: ...
            r = R(); r.returncode=0; r.stdout=samples[state['i']]; r.stderr=''
            if state['i'] < len(samples)-1:
                state['i'] += 1
            return r
        return real_run(cmd, capture_output=capture_output, text=text)
    mod.subprocess.run = fake_run
    sys.argv=['x','--jsonl','{jsonl.as_posix()}','--prom','{prom.as_posix()}','--hist-cpu','0,50,100','--hist-mem','0,50,100']
    mod.main()
    sys.argv=['x','--jsonl','{jsonl.as_posix()}','--prom','{prom.as_posix()}','--hist-cpu','0,50,100','--hist-mem','0,50,100']
    mod.main()
    """
        )
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT.as_posix()
    res = run([sys.executable, str(driver)], env=env)
    assert res.returncode == 0, res.stderr
    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) >= 2
    rec_last = json.loads(lines[-1])
    # Delta bytes: 18kB->10kB = 8kB (8192) approx; our parser uses kB*1024
    assert rec_last.get("delta_net_in") is not None
    assert rec_last.get("delta_net_out") is not None
    delta_mem = rec_last.get("delta_mem_used")
    assert delta_mem in (20, 20 * 1024 * 1024), f"unexpected delta_mem_used={delta_mem}"
    prom_text = prom.read_text()
    # Histogram bucket lines
    assert "resource_trend_cpu_perc_bucket" in prom_text
    assert "resource_trend_mem_perc_bucket" in prom_text

    # Validate histogram cumulative logic for CPU and Mem
    def extract_hist(name):
        buckets = []
        count = None
        for ln in prom_text.splitlines():
            if ln.startswith(f"{name}_bucket"):
                # format: name_bucket{le="X"} value
                try:
                    metric, val = ln.split()[-2:]
                except ValueError:
                    continue
            if ln.startswith(f"{name}_bucket"):
                parts = ln.split()
                if len(parts) != 2:
                    continue
                raw_metric, raw_val = parts
                # extract le label
                le_part = raw_metric.split('le="', 1)[-1]
                le_val = le_part.split('"', 1)[0]
                try:
                    v = float(raw_val)
                except ValueError:
                    continue
                buckets.append((le_val, v))
            elif ln.startswith(f"{name}_count"):
                with contextlib.suppress(ValueError):
                    count = float(ln.split()[-1])
        return buckets, count

    for metric in ("resource_trend_cpu_perc", "resource_trend_mem_perc"):
        buckets, total = extract_hist(metric)
        # Expect at least 2 boundaries plus +Inf
        assert buckets and buckets[-1][0] == "+Inf"
        # Cumulative monotonicity
        vals = [v for _, v in buckets]
        assert vals == sorted(vals), f"Histogram {metric} not cumulative: {vals}"
        assert (
            total == buckets[-1][1]
        ), f"Histogram count mismatch for {metric}: count={total} last={buckets[-1][1]}"
