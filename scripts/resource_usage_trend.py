#!/usr/bin/env python
"""Append & aggregate docker resource usage trends.

Capabilities:
 1. Capture a single docker stats snapshot; append each container row to JSONL.
 2. Maintain an in-memory rolling window (loaded from tail of JSONL) to compute:
            - rolling mean/max cpu & memory percent
            - per-interval deltas for net I/O & memory usage
            - simple histogram buckets for cpu & memory percent distributions
 3. Emit enriched Prometheus exposition including rolling + latest + histogram buckets.

JSONL Fields per container row:
    name, cpu_perc, mem_used_bytes, mem_limit_bytes, mem_perc, net_in_bytes, net_out_bytes,
    timestamp (ISO8601), seq (monotonic sequence), delta_net_in, delta_net_out, delta_mem_used

CLI Examples:
    python scripts/resource_usage_trend.py --jsonl trends/resource_usage.jsonl \
            --prom trends/resource_usage_summary.prom --window 50 --hist-cpu "0,10,25,50,75,90,100" --hist-mem "0,25,50,75,90,100"

Design Notes:
 - We avoid heavy dependencies (e.g., pandas) for portability.
 - Rolling window is reconstructed by reading only the last N *containers lines (seek from EOF).
 - Histogram buckets follow Prometheus cumulative bucket convention: metric_bucket{le="x"} value.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

LINE_RE = re.compile(
    r"^(?P<container>[^\s]+)\s+(?P<cpu>[0-9.]+)%\s+(?P<mem_usage>[^\s]+)\s+(?P<netio>[^\s]+)"
)
SIZE_RE = re.compile(
    r"^(?P<used>[0-9.]+)(?P<usuffix>[A-Za-z]+?)/(?P<limit>[0-9.]+)(?P<lsuffix>[A-Za-z]+?)$"
)
BYTES_MAP = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}


def to_bytes(val, suffix):
    suf = suffix.upper()
    return float(val) * BYTES_MAP.get(suf, 1.0)


def parse_mem_usage(s: str):
    m = SIZE_RE.match(s)
    if not m:
        return None, None
    try:
        used = to_bytes(m.group("used"), m.group("usuffix"))
        limit = to_bytes(m.group("limit"), m.group("lsuffix"))
        return int(used), int(limit)
    except Exception:
        return None, None


def parse_netio(s: str):
    # Format e.g. 12.3kB/45.1kB
    parts = s.split("/")

    def one(p):
        m = re.match(r"([0-9.]+)([A-Za-z]+)", p)
        if not m:
            return None
        return int(to_bytes(m.group(1), m.group(2)))

    if len(parts) == 2:
        return one(parts[0]), one(parts[1])
    return None, None


def capture():
    cmd = [
        "docker",
        "stats",
        "--no-stream",
        "--format",
        "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("docker stats failed", res.stderr, file=sys.stderr)
        return []
    lines = res.stdout.strip().splitlines()
    if lines and lines[0].lower().startswith("name"):
        lines = lines[1:]
    out = []
    for ln in lines:
        ln.split()
        # Reconstruct segments with tabs replaced by spaces in capture, fallback regex
        m = LINE_RE.match(ln.replace("\t", "  "))
        if not m:
            continue
        cont = m.group("container")
        cpu = float(m.group("cpu"))
        mem_usage = m.group("mem_usage")
        netio = m.group("netio")
        mem_used, mem_limit = parse_mem_usage(mem_usage)
        net_in, net_out = parse_netio(netio)
        mem_perc = (mem_used / mem_limit * 100.0) if mem_used and mem_limit else None
        out.append(
            {
                "name": cont,
                "cpu_perc": cpu,
                "mem_used_bytes": mem_used,
                "mem_limit_bytes": mem_limit,
                "mem_perc": mem_perc,
                "net_in_bytes": net_in,
                "net_out_bytes": net_out,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    return out


def tail_jsonl(path: str, window: int) -> list:
    """Read up to last `window` *containers records from JSONL (cheap tail)."""
    if window <= 0 or not os.path.exists(path):
        return []
    # Read entire file if reasonably small (<5MB) else manual tail
    try:
        size = os.path.getsize(path)
        read_size = min(size, 5 * 1024 * 1024)
        with open(path, "rb") as f:
            if size > read_size:
                f.seek(size - read_size)
            data = f.read().decode("utf-8", errors="ignore")
        lines = data.strip().splitlines()
        # If we truncated mid-line, discard first
        if size > read_size:
            lines = lines[1:]
        docs = []
        for ln in lines[-window:]:
            try:
                docs.append(json.loads(ln))
            except Exception:
                continue
        return docs
    except Exception:
        return []


def compute_deltas(latest_rows: list, history: list) -> None:
    """Augment latest_rows with previous counters to compute deltas.
    Uses most recent matching container entry in history (by name)."""
    index = {}
    for rec in reversed(history):  # take most recent first
        nm = rec.get("name")
        if nm not in index:
            index[nm] = rec
    for row in latest_rows:
        prev = index.get(row["name"])
        if prev:
            for key, delta_key in (
                ("net_in_bytes", "delta_net_in"),
                ("net_out_bytes", "delta_net_out"),
                ("mem_used_bytes", "delta_mem_used"),
            ):
                cur = row.get(key)
                prior = prev.get(key)
                if (
                    isinstance(cur, (int, float))
                    and isinstance(prior, (int, float))
                    and prior is not None
                ):
                    row[delta_key] = cur - prior
                else:
                    row[delta_key] = None
        else:
            row["delta_net_in"] = row["delta_net_out"] = row["delta_mem_used"] = None


def hist_buckets(values: list, boundaries: list) -> list:
    """Return cumulative counts for histogram buckets given raw values."""
    counts = []
    for b in boundaries:
        c = sum(1 for v in values if v is not None and v <= b)
        counts.append((b, c))
    # +Inf bucket
    counts.append((math.inf, sum(1 for v in values if v is not None)))
    return counts


def write_prom(latest: list, window_docs: list, path: str, cpu_bounds: list, mem_bounds: list):
    if not latest:
        return
    # Combine for rolling stats: include window_docs + latest
    combined = window_docs + latest
    lines = []

    def gauge(name, value, help_text, labels=None):
        if value is None:
            return
        if labels:
            lbl = ",".join(f'{k}="{v}"' for k, v in labels.items())
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{{{lbl}}} {value}")
        else:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

    gauge("resource_trend_containers", len(latest), "Number of containers in latest snapshot")
    cpus = [r["cpu_perc"] for r in latest if r.get("cpu_perc") is not None]
    if cpus:
        gauge(
            "resource_trend_latest_cpu_avg",
            round(sum(cpus) / len(cpus), 2),
            "Average CPU percent latest snapshot",
        )
    mems = [r["mem_perc"] for r in latest if r.get("mem_perc") is not None]
    if mems:
        gauge(
            "resource_trend_latest_mem_avg",
            round(sum(mems) / len(mems), 2),
            "Average memory percent latest snapshot",
        )

    # Rolling stats
    roll_cpus = [r["cpu_perc"] for r in combined if r.get("cpu_perc") is not None]
    if roll_cpus:
        gauge(
            "resource_trend_roll_cpu_avg",
            round(sum(roll_cpus) / len(roll_cpus), 2),
            "Rolling average CPU percent",
        )
        gauge("resource_trend_roll_cpu_max", round(max(roll_cpus), 2), "Rolling max CPU percent")
    roll_mems = [r["mem_perc"] for r in combined if r.get("mem_perc") is not None]
    if roll_mems:
        gauge(
            "resource_trend_roll_mem_avg",
            round(sum(roll_mems) / len(roll_mems), 2),
            "Rolling average memory percent",
        )
        gauge("resource_trend_roll_mem_max", round(max(roll_mems), 2), "Rolling max memory percent")

    # Per-container latest gauges (cpu, mem, deltas)
    for r in latest:
        lbl = {"name": r["name"]}
        gauge("resource_trend_container_cpu_perc", r.get("cpu_perc"), "Container CPU percent", lbl)
        gauge(
            "resource_trend_container_mem_perc", r.get("mem_perc"), "Container Memory percent", lbl
        )
        gauge(
            "resource_trend_container_delta_net_in_bytes",
            r.get("delta_net_in"),
            "Delta net in bytes since previous",
            lbl,
        )
        gauge(
            "resource_trend_container_delta_net_out_bytes",
            r.get("delta_net_out"),
            "Delta net out bytes since previous",
            lbl,
        )
        gauge(
            "resource_trend_container_delta_mem_used_bytes",
            r.get("delta_mem_used"),
            "Delta memory used bytes since previous",
            lbl,
        )

    # Histograms (cpu & mem percent) built over rolling window + latest combined
    def histogram(name, values, bounds, help_text):
        vals = [v for v in values if v is not None]
        if not vals:
            return
        counts = hist_buckets(vals, bounds)
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} histogram")
        for b, c in counts:
            le = "+Inf" if b is math.inf else str(b)
            lines.append(f'{name}_bucket{{le="{le}"}} {c}')
        lines.append(f"{name}_count {len(vals)}")
        lines.append(f"{name}_sum {round(sum(vals), 4)}")

    histogram(
        "resource_trend_cpu_perc",
        roll_cpus,
        cpu_bounds,
        "CPU percent histogram over rolling window",
    )
    histogram(
        "resource_trend_mem_perc",
        roll_mems,
        mem_bounds,
        "Memory percent histogram over rolling window",
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="resource_usage_trend.jsonl")
    ap.add_argument("--prom", default="")
    ap.add_argument(
        "--window",
        type=int,
        default=50,
        help="Rolling window size (number of recent rows across all containers)",
    )
    ap.add_argument(
        "--hist-cpu",
        default="0,10,25,50,75,90,100",
        help="CPU percent histogram bucket boundaries (comma list)",
    )
    ap.add_argument(
        "--hist-mem",
        default="0,25,50,75,90,100",
        help="Memory percent histogram bucket boundaries (comma list)",
    )
    args = ap.parse_args()

    data = capture()
    if not data:
        print("No data captured; exiting")
        return
    # Load prior window
    history = tail_jsonl(args.jsonl, args.window)
    seq_base = history[-1]["seq"] + 1 if history and "seq" in history[-1] else 0
    compute_deltas(data, history)
    for i, row in enumerate(data):
        row["seq"] = seq_base + i
    os.makedirs(os.path.dirname(args.jsonl) or ".", exist_ok=True)
    with open(args.jsonl, "a", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
    print(f"Appended {len(data)} usage rows to {args.jsonl}")

    if args.prom:
        cpu_bounds = [float(x) for x in args.hist_cpu.split(",") if x.strip()]
        mem_bounds = [float(x) for x in args.hist_mem.split(",") if x.strip()]
        write_prom(data, history, args.prom, cpu_bounds, mem_bounds)
        print(f"Wrote Prometheus summary metrics to {args.prom}")


if __name__ == "__main__":
    main()
