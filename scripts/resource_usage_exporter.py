#!/usr/bin/env python
"""Capture a single snapshot of `docker stats --no-stream` and emit Prometheus metrics.

Writes resource_usage_metrics.prom
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUTPUT = Path("resource_usage_metrics.prom")
TABLE_CMD = ["docker", "stats", "--no-stream", "--format", "{{json .}}"]

CPU_RE = re.compile(r"([0-9]+\.?[0-9]*)%")
MEM_RE = re.compile(r"([0-9]+\.?[0-9]*)([KMG]iB) / ([0-9]+\.?[0-9]*)([KMG]iB)")

FACTOR = {
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
}


def parse_line(line: str):
    data = json.loads(line)
    name = data.get("Name") or data.get("Container")
    cpu_raw = data.get("CPUPerc", "")
    mem_raw = data.get("MemUsage", "")
    net_io = data.get("NetIO", "")
    blk_io = data.get("BlockIO", "")

    cpu = None
    m_cur = m_limit = None
    m = CPU_RE.match(cpu_raw.strip())
    if m:
        cpu = float(m.group(1))
    m2 = MEM_RE.match(mem_raw.replace(" ", ""))
    if m2:
        cur_val, cur_unit, lim_val, lim_unit = m2.groups()
        m_cur = float(cur_val) * FACTOR.get(cur_unit, 1)
        m_limit = float(lim_val) * FACTOR.get(lim_unit, 1)
    return {
        "name": name,
        "cpu_percent": cpu,
        "memory_bytes": m_cur,
        "memory_limit_bytes": m_limit,
        "net_io_raw": net_io,
        "block_io_raw": blk_io,
    }


def main():
    proc = subprocess.run(TABLE_CMD, capture_output=True, text=True, check=False)
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    entries = []
    for line in lines:
        try:
            entries.append(parse_line(line))
        except Exception:
            continue

    out = [
        "# HELP docker_container_cpu_percent Point-in-time CPU percent (Docker reported) for container",
        "# TYPE docker_container_cpu_percent gauge",
        "# HELP docker_container_memory_bytes Current memory usage in bytes",
        "# TYPE docker_container_memory_bytes gauge",
        "# HELP docker_container_memory_limit_bytes Memory limit in bytes",
        "# TYPE docker_container_memory_limit_bytes gauge",
    ]
    for e in entries:
        lbl = f'name="{e["name"]}"'
        if e["cpu_percent"] is not None:
            out.append(f"docker_container_cpu_percent{{{lbl}}} {e['cpu_percent']}")
        if e["memory_bytes"] is not None:
            out.append(f"docker_container_memory_bytes{{{lbl}}} {int(e['memory_bytes'])}")
        if e["memory_limit_bytes"] is not None:
            out.append(
                f"docker_container_memory_limit_bytes{{{lbl}}} {int(e['memory_limit_bytes'])}"
            )
    OUTPUT.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
