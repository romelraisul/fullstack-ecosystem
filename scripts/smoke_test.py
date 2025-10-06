#!/usr/bin/env python
"""Simple end-to-end smoke test hitting core service endpoints and emitting results.

Exit code non-zero if any mandatory check fails.
Generates:
  smoke_results.json - structured results
  smoke_metrics.prom  - Prometheus-style metrics
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TARGETS = [
    {
        "name": "api-health",
        "url": os.environ.get("API_HEALTH_URL", "http://localhost:8010/health"),
        "required": True,
    },
    {
        "name": "prometheus-ready",
        "url": os.environ.get("PROM_READY_URL", "http://localhost:9090/-/ready"),
        "required": True,
    },
    {
        "name": "grafana-health",
        "url": os.environ.get("GRAFANA_HEALTH_URL", "http://localhost:3030/api/health"),
        "required": False,
    },
]

TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "3"))
RETRIES = int(os.environ.get("SMOKE_RETRIES", "5"))
DELAY = float(os.environ.get("SMOKE_DELAY", "2"))


def fetch(url: str):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:  # nosec B310
            body = r.read(256)
            status = r.getcode()
            return status, body[:128], time.time() - start, None
    except Exception as e:  # noqa: BLE001
        return None, None, time.time() - start, str(e)


def main():
    results = []
    overall_fail = False
    for target in TARGETS:
        name = target["name"]
        url = target["url"]
        required = target["required"]
        attempt = 0
        status = None
        err = None
        latency = None
        while attempt < RETRIES:
            attempt += 1
            status, _body, latency, err = fetch(url)
            if status and 200 <= status < 400:
                break
            time.sleep(DELAY)
        success = status is not None and 200 <= status < 400
        if required and not success:
            overall_fail = True
        results.append(
            {
                "name": name,
                "url": url,
                "required": required,
                "status": status,
                "latency_ms": round((latency or 0) * 1000, 1),
                "success": success,
                "error": err,
                "attempts": attempt,
            }
        )

    Path("smoke_results.json").write_text(json.dumps({"results": results}, indent=2) + "\n")

    # Emit metrics
    lines = [
        "# HELP smoke_target_up Whether target succeeded (1/0)",
        "# TYPE smoke_target_up gauge",
        "# HELP smoke_target_latency_ms Latency of last attempt (ms)",
        "# TYPE smoke_target_latency_ms gauge",
    ]
    for r in results:
        label = f'name="{r["name"]}"'
        up = 1 if r["success"] else 0
        lines.append(f"smoke_target_up{{{label}}} {up}")
        lines.append(f"smoke_target_latency_ms{{{label}}} {r['latency_ms']}")
    Path("smoke_metrics.prom").write_text("\n".join(lines) + "\n")

    if overall_fail:
        print("One or more required targets failed", file=sys.stderr)
        for r in results:
            if r["required"] and not r["success"]:
                print(
                    f"FAILED {r['name']} status={r['status']} error={r['error']}", file=sys.stderr
                )
        sys.exit(1)
    print("Smoke test passed for all required targets")


if __name__ == "__main__":
    main()
