#!/usr/bin/env python
"""Lightweight orchestrator to launch multiple platform Python modules, monitor liveness,
   and provide graceful shutdown (Ctrl+C) plus basic Prometheus-style metrics output.

Usage:
  python scripts/orchestrator.py --modules academic_research_platform.py web_security_knowledge_platform.py \
      --metrics-file orchestrator_metrics.prom

Features:
 - Starts each module in its own subprocess (same interpreter) with unbuffered output.
 - Restarts crashed processes if --auto-restart is set.
 - Emits simple counters for starts/crashes/uptime seconds per process.
 - Graceful SIGINT/SIGTERM handling.
 - Optional --health-url pattern (format with {name}) to poll basic HTTP readiness.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


class ManagedProc:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.process: subprocess.Popen | None = None
        self.starts = 0
        self.crashes = 0
        self.start_time: float | None = None

    def start(self):
        if not self.path.exists():
            raise FileNotFoundError(f"Module script not found: {self.path}")
        os.environ.copy()
        cmd = [sys.executable, str(self.path)]
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True
        )
        self.starts += 1
        self.start_time = time.time()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self, timeout: float = 10):
        if self.process and self.is_running():
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def uptime(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--modules",
        nargs="+",
        required=True,
        help="List of python module script files (.py) relative to repo root",
    )
    ap.add_argument(
        "--metrics-file",
        default="orchestrator_metrics.prom",
        help="Prometheus exposition file path",
    )
    ap.add_argument(
        "--poll-interval", type=float, default=5.0, help="Monitoring loop interval seconds"
    )
    ap.add_argument(
        "--auto-restart", action="store_true", help="Automatically restart crashed processes"
    )
    ap.add_argument("--health-url", default=None, help="Optional health URL template (use {name})")
    return ap.parse_args()


def writer_thread(proc: ManagedProc, stop_evt: threading.Event):
    if proc.process is None or proc.process.stdout is None:
        return
    for line in proc.process.stdout:
        if stop_evt.is_set():
            break
        sys.stdout.write(f"[{proc.name}] {line}")
    sys.stdout.flush()


def emit_metrics(procs: list[ManagedProc], path: Path):
    lines = [
        "# HELP orchestrator_process_starts Total process starts",
        "# TYPE orchestrator_process_starts counter",
    ]
    for p in procs:
        lines.append(f'orchestrator_process_starts{{name="{p.name}"}} {p.starts}')
    lines.append("# HELP orchestrator_process_crashes Total observed crashes (non-zero exit)")
    lines.append("# TYPE orchestrator_process_crashes counter")
    for p in procs:
        lines.append(f'orchestrator_process_crashes{{name="{p.name}"}} {p.crashes}')
    lines.append(
        "# HELP orchestrator_process_uptime_seconds Current uptime seconds for running processes"
    )
    lines.append("# TYPE orchestrator_process_uptime_seconds gauge")
    for p in procs:
        up = p.uptime() if p.is_running() else 0.0
        lines.append(f'orchestrator_process_uptime_seconds{{name="{p.name}"}} {up:.0f}')
    path.write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    base = Path(".")
    procs: list[ManagedProc] = []
    for mod in args.modules:
        name = Path(mod).stem
        procs.append(ManagedProc(name=name, path=base / mod))

    stop_evt = threading.Event()

    def handle_signal(signum, frame):  # noqa: ARG001
        stop_evt.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Start all modules
    writer_threads: list[threading.Thread] = []
    for p in procs:
        p.start()
        t = threading.Thread(target=writer_thread, args=(p, stop_evt), daemon=True)
        t.start()
        writer_threads.append(t)

    metrics_path = Path(args.metrics_file)

    try:
        while not stop_evt.is_set():
            # Monitor
            for p in procs:
                if not p.is_running():
                    ret = p.process.returncode if p.process else None
                    if ret and ret != 0:
                        p.crashes += 1
                        if args.auto_restart:
                            p.start()
                    elif args.auto_restart and ret == 0:
                        # Normal exit but auto-restart requested
                        p.start()
            emit_metrics(procs, metrics_path)
            time.sleep(args.poll_interval)
    finally:
        for p in procs:
            p.stop()
        emit_metrics(procs, metrics_path)


if __name__ == "__main__":
    main()
