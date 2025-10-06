#!/usr/bin/env python3
"""Adaptive synthetic traffic seeder (lightweight implementation).

Behavior:
1. Load agent registry (list of agent objects with `name` & optional `seed_endpoint`).
2. Query Prometheus for recent request rates (5m) per agent using a standard metric
    pattern (microservice_requests_total{service="<agent>"}). If Prometheus unreachable,
    fall back to seeding a capped subset.
3. Identify agents below a target RPS threshold (default: 0.1 req/s) and send a
    lightweight HTTP GET/POST to stimulate metrics & latency histograms.

Safety / Limits:
- Max seeded agents per run: 10 (configurable via SEED_MAX_AGENTS).
- Per-agent parallelism: 1 simple request.
- Timeouts kept small (3s) to avoid piling up.

Environment Variables:
  PROMETHEUS_BASE   (default http://localhost:9090)
  SEED_RPS_THRESHOLD (default 0.1)
  SEED_MAX_AGENTS    (default 10)
  SEED_DRY_RUN       (if '1', only log planned actions)
  AGENT_REGISTRY     (path override)

Assumptions:
- Registry entries are list objects each with at minimum `name`.
- Agents accept a generic `/health` or custom `seed_endpoint` (default /health).
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from datetime import datetime

try:
    import httpx  # fast async-capable client; we'll use simple sync interface
except Exception:  # pragma: no cover
    httpx = None

REGISTRY_PATH = os.environ.get("AGENT_REGISTRY", "autogen/agents/agent_registry.json")
PROM_BASE = os.environ.get("PROMETHEUS_BASE", "http://localhost:9090")
RPS_THRESHOLD = float(os.environ.get("SEED_RPS_THRESHOLD", "0.1"))
MAX_AGENTS = int(os.environ.get("SEED_MAX_AGENTS", "10"))
DRY_RUN = os.environ.get("SEED_DRY_RUN", "0") == "1"

REQUEST_METRIC = "microservice_requests_total"


def load_registry() -> list[dict]:
    if not os.path.exists(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict) and d.get("name")]
    return []


def prom_instant_query(query: str):
    if httpx is None:
        return None
    url = f"{PROM_BASE}/api/v1/query"
    try:
        r = httpx.get(url, params={"query": query}, timeout=3.0)
        r.raise_for_status()
        payload = r.json()
        if payload.get("status") != "success":
            return None
        return payload.get("data", {}).get("result", [])
    except Exception:
        return None


def collect_rps(agents: list[dict]):
    # Use rate() over 5m for each agent; build OR expression
    if not agents:
        return {}
    # We'll pull all and filter client-side for simplicity
    # Query: sum by (service) (rate(microservice_requests_total[5m]))
    q = f"sum by (service) (rate({REQUEST_METRIC}[5m]))"
    result = prom_instant_query(q) or []
    rps_map = {}
    for series in result:
        metric = series.get("metric", {})
        svc = metric.get("service")
        value = series.get("value")
        if svc and value and isinstance(value, list) and len(value) == 2:
            with contextlib.suppress(ValueError):
                rps_map[svc] = float(value[1])
    # Only keep for our agents
    agent_names = {a["name"] for a in agents}
    return {k: v for k, v in rps_map.items() if k in agent_names}


def pick_low_traffic_agents(agents: list[dict], rps_map):
    chosen = []
    for a in agents:
        name = a["name"]
        rps = rps_map.get(name, 0.0)  # treat missing as 0
        if rps < RPS_THRESHOLD:
            chosen.append((name, rps, a.get("seed_endpoint") or "/health"))
    # sort by ascending rps so the *lowest* get priority
    chosen.sort(key=lambda t: t[1])
    return chosen[:MAX_AGENTS]


def stimulate(agent_name: str, endpoint: str):
    if DRY_RUN or httpx is None:
        print(f"[dry-run] Would stimulate {agent_name} -> {endpoint}")
        return
    url = f"http://{agent_name}:8000{endpoint}"  # assumes agent reachable by service name & default port
    with contextlib.suppress(Exception):
        resp = httpx.get(url, timeout=3.0)
        print(f"Seeded {agent_name} {endpoint} status={resp.status_code}")


def main():
    now = datetime.utcnow().isoformat()
    print(
        f"[synthetic_seed] {now} run start (threshold={RPS_THRESHOLD} rps, max={MAX_AGENTS}, dry={DRY_RUN})"
    )
    agents = load_registry()
    if not agents:
        print(f"No registry entries found at {REGISTRY_PATH}; exiting")
        return 0
    rps_map = collect_rps(agents)
    selected = pick_low_traffic_agents(agents, rps_map)
    if not selected:
        print("All agents at/above threshold or none selected")
        return 0
    print(f"Selected {len(selected)} agents for stimulation (of {len(agents)} total)")
    for name, rps, endpoint in selected:
        print(f" - {name} current_rps={rps:.4f} endpoint={endpoint}")
        stimulate(name, endpoint)
    return 0


if __name__ == "__main__":
    sys.exit(main())
