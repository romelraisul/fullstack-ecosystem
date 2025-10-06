import json
import os
import pathlib
import subprocess
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "resource_usage_trend.py"

MOCK_STATS_OUTPUT = """NAME                CPU %     MEM USAGE / LIMIT     NET I/O
container_a         5.23%     100MiB/1GiB           10kB/5kB
container_b         55.1%     256MiB/2GiB           30kB/15kB
""".strip()


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def test_resource_usage_trend_parses_and_appends(tmp_path, monkeypatch):
    # Monkeypatch subprocess.run inside the module by creating a shim that returns our MOCK output
    shim = tmp_path / "shim.py"
    shim.write_text(
        textwrap.dedent(
            f"""
    import subprocess as _sp
    real_run = _sp.run
    from pathlib import Path
    import types
    MOCK = {json.dumps(MOCK_STATS_OUTPUT)}
    def fake_run(cmd, capture_output=False, text=False):
        if isinstance(cmd, list) and cmd[:2] == ['docker','stats']:
            class R: pass
            r = R(); r.returncode=0; r.stdout=MOCK; r.stderr=''; return r
        return real_run(cmd, capture_output=capture_output, text=text)
    import scripts.resource_usage_trend as mod
    mod.subprocess.run = fake_run
    mod.main()
    """
        )
    )
    jsonl = tmp_path / "trend.jsonl"
    prom = tmp_path / "trend.prom"
    os.environ.copy()
    # Execute shim with modified sys.path
    # Use POSIX style paths to avoid unicode escape issues on Windows in -c string
    code = (
        f"import sys, pathlib; sys.path.insert(0, '{ROOT.as_posix()}'); "
        f"sys.argv=['x','--jsonl','{jsonl.as_posix()}','--prom','{prom.as_posix()}']; "
        f"exec(open('{shim.as_posix()}').read())"
    )
    res = run([sys.executable, "-c", code])
    assert res.returncode == 0, res.stderr
    data_lines = jsonl.read_text().strip().splitlines()
    assert len(data_lines) == 2
    record0 = json.loads(data_lines[0])
    assert "name" in record0 and "cpu_perc" in record0
    prom_text = prom.read_text()
    assert "resource_trend_containers" in prom_text
    assert "resource_trend_latest_cpu_avg" in prom_text
