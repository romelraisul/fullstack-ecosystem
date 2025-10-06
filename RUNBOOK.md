# Operations Runbook

This runbook helps you verify performance and reliability and troubleshoot common issues.

## Health and KPIs

- Gateway UI: <http://localhost:5125>
- API health: <http://localhost:8010/health>
- Throughput: <http://localhost:8010/orchestrator/throughput?window_seconds=60>
- Grafana: <http://localhost:5125/grafana/>
- Prometheus: <http://localhost:5125/prometheus/>
- Alertmanager: <http://localhost:5125/alertmanager/>

## Test flows

1) Burst validation (10 cycles)
   - Expect: 10/10 ok; avg duration ~50–120ms; tasks/min ~100+
   - Run via Tools guide

2) Stress (60s tight loop)
   - Expect: >500 iterations; errors near zero

3) Soak (60 minutes paced)
   - Expect: 0 errors; p95 stable; alerts remain quiet

## Alerts to watch

- HighLatencyP95: Investigate client/server latency spikes.
- LowSuccessRatio: Check recent `system.execute.error` events.
- Quantum guardrails: For QCAE/QDC/QCMS/QCC latency and errors.
- Low throughput banner (Gateway): Appears after sustained idle or low activity.

## Troubleshooting quick checks

- API container logs: ensure uvicorn workers are running and no ImportError for http2 (should use httpx[http2]).
- Internal limiter bypass: ensure tests set header `X-Orchestrator-Bypass: 1`.
- If throughput is 0 while active: verify events are being recorded (`/api/events/recent`).
- If achievements don't load: check `/api/enterprise/achievements` and Gateway console for network errors.

## Reference

- System inventory: `backend/app/data/systems_inventory.json`
- Recent events persisted: `backend/app/data/events_recent.json`
- Nginx subpaths and tuning: `docker/gateway/nginx.conf`
- Gateway UI: `docker/gateway/index.html`
- Orchestrator: `backend/app/main.py`
