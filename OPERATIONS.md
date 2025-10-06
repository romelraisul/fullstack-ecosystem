# Operations Guide

<!-- TLDR-START: AUTO-GENERATED (edit source sections, then run scripts/generate_runbook_tldr.py) -->
## Runbook TL;DR

### Core Commands

- Start stack: `docker compose up -d`
- Stop stack: `docker compose down`
- Rebuild (deps changed): `docker compose build --no-cache && docker compose up -d`
- Tail one service: `docker compose logs -f <service>`
- Reload Prometheus rules: `curl -X POST http://localhost:9090/prometheus/-/reload`

### Key Files

- Compose: `docker-compose.yml`
- Agent registry: `autogen/agents/agent_registry.json`
- Prometheus rules: `docker/prometheus_rules.yml`
- Gateway config: `docker/gateway/nginx.conf`
- Seeder: `autogen/agent_traffic_seeder.py`
- Dashboard JSON: `autogen/grafana-dashboard-config.json`

### Add an Agent

1. Create module in `autogen/agents/`.
2. Add service & nginx route.
3. Append thresholds entry to `agent_registry.json`.
4. Rebuild/start impacted services.

### Dynamic SLO Thresholds

- Edit latency/error budget in `agent_registry.json` (hot-reload ≤60s)
- Gauges auto-update alerts (no rule edits)

### Synthetic Traffic

- Adaptive seeder skips agents above organic RPS threshold
- Disable: `docker compose stop autogen-agent-traffic-seeder`

### Security & Tracing

- Basic Auth protects observability & agent paths
- X-Request-ID propagated/injected at gateway & logged by agents

### Troubleshooting Fast Path

1. Gateway 502 → check container & nginx route
2. Missing metrics → curl /metrics & confirm scrape job
3. High latency alert → inspect panels 11 & 14 (p95 vs thresholds)
4. Burn alert → panels 12 & 13 (fast/slow error burn) + recent deploy diff

### Escalation Criteria

- Critical latency > threshold 10m
- Error rate > critical threshold 5m or burn fast >14
- Fleet error alert firing (systemic)

(Full details in subsequent sections. Regenerate with: `python scripts/generate_runbook_tldr.py`)
<!-- TLDR-END -->

Environment: Docker Compose multi-service (gateway, agents, monitoring stack, data stores)

Primary Gateway: <http://localhost:5125>

Internal Agent Port (all agents): 8000

## 1. Rebuild & Restart Procedure

Use this after changing Dockerfiles, dependencies, environment variables, or agent/gateway code.

Windows PowerShell (from repository root):

```powershell
# Stop existing stack (ignore errors if not running)
docker compose down

# Remove dangling images (optional cleanup)
docker image prune -f

# Rebuild all images (no cache if you changed base dependencies)
docker compose build --no-cache

# Start detached
docker compose up -d

# Follow logs for first 30s (Ctrl+C to exit)
docker compose logs -f --tail=200
```

Quick incremental (when only a single agent file changed and not base Dockerfile):

```powershell
docker compose up -d --build <agent_service_name>
```

Services names (examples – adjust if compose file differs):

```text
agents_academic  agents_developer  agents_web_security  agents_topics  agents_ultimate  gateway  prometheus  grafana  alertmanager
```

## 2. Verifying Health

1. Open gateway: <http://localhost:5125>
2. Check "Agents" panel (each should show OK within ~10-15s).
3. Aggregated Fleet Summary should show Healthy count matching total agents.
4. Click Prometheus link -> verify targets are all UP (Status page: `/prometheus/targets`).
5. Grafana -> Add a panel -> query
   `{__name__=~"REQUEST_COUNT.*"}` or use Prometheus datasource and
   search for `REQUEST_COUNT_total`.

## 3. Metrics Visibility (Cold Start)

Agents now self-prime metrics with zero-value samples, so metrics appear
immediately after startup without traffic. If some metrics do not appear:

- Confirm container logs for the agent (`docker compose logs agents_academic | Select-String ERROR`)
- Ensure Prometheus job points to `agent_service_name:8000`.
- Curl locally from inside a temporary container:
   `docker run --rm --network <your_network> curlimages/curl:8.9.1 curl -s \
    agents_academic:8000/metrics | head`.

## 4. Common Troubleshooting

| Symptom | Action |
|---------|--------|
| Gateway 5125 not loading | `docker compose ps`; ensure `gateway` is healthy; check `docker compose logs gateway` for nginx errors. |
| Agents show DOWN | Open one agent health URL directly: <http://localhost:5125/agents/academic/health>; if 502, nginx can't reach container (container name mismatch or failed start). |
| Prometheus missing agent targets | Re-run with `docker compose up -d prometheus`; inspect `docker/prometheus.yml`; restart Prometheus after edits. |
| Grafana shows no datasource | Ensure provisioning files (if any) exist; otherwise manually add Prometheus at `http://prometheus:9090`. |
| Aggregated summary errors column populated | Inspect ultimate aggregator logs: `docker compose logs agents_ultimate`; possible network or DNS issue between containers. |
| Metrics absent despite health OK | Confirm `prometheus-client` library installed in agent image (base Dockerfile) and that `/metrics` endpoint responds (curl). |
| High restart count | Check Docker Desktop for memory limits; reduce parallel services or raise resources. |

## 5. Adding a New Agent

1. Create `autogen/agents/<new_agent>.py` using existing pattern (import FastAPI, metrics, health & stats routes).
2. Add service to `docker-compose.yml` referencing
   `build: { context: ., dockerfile: autogen/Dockerfile.agent-base }` and set
   `environment: AGENT_MODULE=<path.module>`; include `env_file: .env`.
3. Add Prometheus scrape job:

   ```yaml
   - job_name: '<new_agent>'
     static_configs:
       - targets: ['<compose_service_name>:8000']
   ```

4. Add nginx route in `docker/gateway/nginx.conf`:

   ```nginx
   location /agents/<alias>/ { proxy_pass http://<compose_service_name>:8000/; }
   ```

5. Add to `AGENTS` array and aggregation list (ultimate service if using static list there).
6. Rebuild & restart (see above) then verify.

## 6. Environment Variables & Secrets

Central `.env` loaded by all agents. Update then rebuild containers that depend
on changed values (or `docker compose up -d --env-file .env --build`).

For sensitive production secrets, replace `.env` with Docker secrets / Vault integration (see `SECURITY_NOTES.md`).

## 7. Log Inspection Shortcuts

```powershell
# Tail one service
docker compose logs -f agents_topics

# Search errors last 300 lines
docker compose logs --tail=300 agents_web_security | Select-String -Pattern "ERROR|Traceback"

# All services brief status
docker compose ps
```

## 8. Updating Base Dependencies

When modifying `autogen/Dockerfile.agent-base`:

```powershell
docker compose build --no-cache agents_academic agents_developer agents_web_security agents_topics agents_ultimate
# Or rebuild entire stack
```
Then restart: `docker compose up -d`.

## 11. Health & Observability Roadmap (Future Enhancements)

- (Done) Alertmanager rules: agent target down (2m) & no requests (10m) added (`agents-health` group in `docker/prometheus_rules.yml`).
- (Done) Initial Grafana dashboard JSON `docker/grafana/dashboards/agent_fleet.json`
   (request rate, p95 latency, up count, inactivity, per-agent rates).
- Next: Auto-provision dashboard (needs manual import unless provisioning path
   mounted in Grafana). Add auth (reverse proxy basic auth or OAuth) for gateway
   & dashboards.
- Future: Automatic agent discovery (service label scraping) to reduce static lists.

### 11.1 Agent Alert Rules Summary

File: `docker/prometheus_rules.yml` group `agents-health`.

Alerts:

| Alert | Condition | For | Severity | Meaning |
|-------|-----------|-----|----------|---------|
| AgentTargetDown | `up{job=~"agent-.*"} == 0` | 2m | critical | An agent target is unreachable. |
| *Agent*NoRequests10m | `sum(rate(<agent>_requests_total[10m])) == 0 and up==1` | instant | warning | Agent healthy but idle for 10m (possible traffic issue). |

Disable/adjust by editing/removing rules and reloading Prometheus: `curl -X POST http://localhost:9090/prometheus/-/reload`.

### 11.2 Grafana Dashboard Import

Dashboard file: `docker/grafana/dashboards/agent_fleet.json`.

Manual import steps:

1. Open Grafana (gateway link or <http://localhost:3030> if direct port exposed).
2. Menu -> Dashboards -> New -> Import.
3. Upload JSON file or paste its contents.
4. Select Prometheus datasource (should auto-populate if already provisioned).

To auto-provision, place JSON and a dashboard provisioning YAML in Grafana
provisioning directory (e.g.,
`docker/grafana/provisioning/dashboards/agent_fleet.yml`). Example YAML:

```yaml
apiVersion: 1
providers:
   - name: agent-fleet
      orgId: 1
      folder: Agents
      type: file
      disableDeletion: false
      updateIntervalSeconds: 30
      options:
         path: /etc/grafana/custom-dashboards
```

Ensure the volume mapping already includes `/etc/grafana/custom-dashboards` and the JSON resides there.

### 11.3 Recording Rules

Recording rules added (group: `agent-recording` in `docker/prometheus_rules.yml`):

| Record Name | Expression (summary) | Purpose |
|-------------|----------------------|---------|
| `agent:requests_rate_5m` | Sum rate of each agent's `*_requests_total` over 5m | Simplify dashboard / alert queries for throughput |
| `agent:academic_research:p95_latency_seconds` | p95 from histogram buckets | Latency SLO tracking |
| `agent:developer_ecosystem:p95_latency_seconds` | p95 from histogram buckets | Latency SLO tracking |
| `agent:web_security:p95_latency_seconds` | p95 from histogram buckets | Latency SLO tracking |
| `agent:awesome_topics:p95_latency_seconds` | p95 from histogram buckets | Latency SLO tracking |

Prometheus reload (no restart required):

```powershell
curl -X POST http://localhost:9090/prometheus/-/reload
```


Use in Grafana: query `agent:requests_rate_5m` or individual p95 metrics instead of repeating full histogram_quantile expressions.

## 12. Quick Verification Checklist After Any Change

- [ ] Gateway loads without 502/500.
- [ ] All agents show OK in Agents panel.
- [ ] Fleet summary healthy count correct.
- [ ] Prometheus targets all UP.
- [ ] Metrics name `REQUEST_COUNT_total` present.
- [ ] No crash loops in `docker compose ps`.

---
Maintainer Tip: Keep this guide versioned with changes—update sections when adding new services or observability features.

## 13. Latency SLO Alerts (New)

Added alert group `agents-slo-latency` in `docker/prometheus_rules.yml` leveraging recording rules `agent:*:p95_latency_seconds`.

| Alert | Threshold | For | Severity |
|-------|-----------|-----|----------|
| *Agent*P95LatencyHigh | p95 > 0.5s | 5m | warning |
| *Agent*P95LatencyCritical | p95 > 1.0s | 10m | critical |

Reload after editing:
 
```powershell
curl -X POST http://localhost:9090/prometheus/-/reload
```

Tune thresholds per agent by copying a rule and scoping with label `agent:` or
creating a second recording rule (e.g., adjust future high-traffic agents
 differently).

## 14. Dynamic Agent Registry

Static hard‑coded agent lists replaced by a JSON registry at
`autogen/agents/agent_registry.json` mounted read‑only into each agent container
at `/app/agents/agent_registry.json`.

Example entry:
 
```json
{
   "name": "academic",
   "job": "agent-academic-research",
   "host": "autogen-academic-research-platform:8000",
   "health_path": "/health",
   "display_name": "Academic Research",
   "category": "research"
}
```

Add a new agent:

1. Define its service in `docker-compose.yml`.
2. Append an entry to `agent_registry.json`.
3. Recreate only affected services (gateway picks up dynamically via ultimate service):
 
```powershell
docker compose up -d autogen-ultimate-enterprise-summary gateway <new_agent_service>
```

Ultimate summary service exposes:

- `/api/agents/list` – raw registry (name/display/category/job/health_path)
- `/api/agents/status` – aggregated health checks (dynamic)

## 15. Gateway UI Dynamic Loading

The control panel (`docker/gateway/index.html`) now calls
`/agents/ultimate/api/agents/list` and constructs the agent polling list at
runtime. No code change required to surface a newly added agent—only update
registry + service + nginx route.

If an agent fails to appear:
 
1. Check registry JSON syntax.
2. Ensure nginx route exists mapping `/agents/<name>/` to the container.
3. Verify ultimate service logs for registry load message.

## 16. Synthetic Traffic Seeder

docker compose up -d autogen-agent-traffic-seeder --build
docker compose stop autogen-agent-traffic-seeder
docker compose logs -f autogen-agent-traffic-seeder | Select-String seeding
Service: `autogen-agent-traffic-seeder` (module `agent_traffic_seeder`).

Purpose: Prevent “no requests” false positives and keep latency histograms active
by issuing lightweight GETs to each agent's health endpoint. This legacy simple
mode used a fixed interval and is retained for backward compatibility; the
adaptive mode (see section 23) supersedes it.

Legacy Environment Variable (simple interval mode only):

| Variable | Default | Description |
|----------|---------|-------------|
| `SEED_INTERVAL_SECONDS` | 60 | Interval between seed cycles (legacy). Not used by current adaptive script but still honored if present in legacy deployments. |

Adjust interval (example 120s):

```powershell
$env:SEED_INTERVAL_SECONDS=120; docker compose up -d autogen-agent-traffic-seeder --build
```

Disable seeding (keep service definition):

```powershell
docker compose stop autogen-agent-traffic-seeder
```

Remove permanently: delete/comment service block then rebuild.

Logs (sampling):

```powershell
docker compose logs -f autogen-agent-traffic-seeder | Select-String seeding
```

Notes:

- Prefer adaptive seeder (section 23) for production-like scenarios.
- CI dry-run job (planned) will execute adaptive script with `SEED_DRY_RUN=1` to surface regressions early.
- AuthN/Z for gateway & APIs (JWT / OIDC / Basic Auth + IP allowlists).
- Adaptive synthetic traffic backs off under real user load to minimize noise (adaptive mode only).

## 18. Registry Hot Reload & Disabled Flag

The ultimate service now hot‑reloads `agent_registry.json` every 60s (mtime + size fingerprint). Changes appear automatically in:

- Gateway dynamic agent list
- Aggregated `/api/agents/status` response
- Seeder active target list

To temporarily hide an agent without removing its entry, add:

```json
"disabled": true
```

in the agent's JSON object. The agent will be excluded from status aggregation, UI list, and synthetic seeding. Remove or set `false` to re‑enable (no container restart needed).

Verification checklist after edit:

1. Modify JSON and save
2. Wait ≤60s
3. Refresh gateway; agent disappears / reappears
4. Seeder logs show updated active vs disabled counts

## 19. Burn-Rate Latency Alerts

Group `agents-slo-burn` introduces early-warning latency alerts that trigger before absolute SLO breaches by comparing a short window p95 latency to a longer baseline window (e.g. 5m vs 30m). An alert fires when the short window shows a significant surge (e.g. >30%) AND exceeds an absolute floor (e.g. 0.6s) to avoid noise on very low latencies.

Tuning tips:

- Increase multiplier (e.g. 1.3 → 1.5) to reduce noise.
- Raise floor (0.6s) if normal variation clusters near threshold.
- Add severity label mapping to routing in Alertmanager if needed.

Disable a single burn alert and reload Prometheus:

```powershell
curl -X POST http://localhost:9090/prometheus/-/reload
```


Per-agent SLO thresholds are now declared in `autogen/agents/agent_registry.json` with keys:

| Field | Meaning | Example |
|-------|---------|---------|
| `latency_p95_warning_seconds` | Warning p95 latency threshold | 0.5 |
| `latency_p95_critical_seconds` | Critical p95 latency threshold | 1.0 |
| `error_budget_fraction` | Allowed 5xx error fraction (e.g. 0.01 = 1%) | 0.01 |

The ultimate summary service exports these as Prometheus gauges:

| Gauge | Labels | Description |
|-------|--------|-------------|
| `agent_latency_p95_warning_seconds` | agent | Warning latency threshold |
| `agent_latency_p95_critical_seconds` | agent | Critical latency threshold |
| `agent_error_budget_fraction` | agent | Error budget fraction |

Alert expressions in groups `agents-slo-latency`, `agents-slo-error`, and `agents-slo-error-burn-multiwindow` now join on these gauges, removing hard-coded values. Adjusting any threshold requires only editing the registry JSON; the hot-reload loop (≤60s) plus Prometheus scrape automatically applies changes (no rule file edit needed unless structure changes).

Verification:

```powershell
curl http://localhost:5125/agents/ultimate/metrics | Select-String agent_latency_p95_warning_seconds
```



## 23. Adaptive Synthetic Traffic Seeder

File: `autogen/agent_traffic_seeder.py`

Enhancements:

1. Queries Prometheus for 5m request rate per agent.
2. Skips agents whose organic (real) traffic exceeds threshold.
3. Logs skipped agents with current rps.

Environment Variables (current adaptive implementation):

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_BASE` | `http://localhost:9090` (container override: `http://prometheus:9090`) | Prometheus API base for 5m rate queries |
| `SEED_RPS_THRESHOLD` | `0.1` | Skip agent if its 5m rate >= threshold (organic traffic sufficient) |
| `SEED_MAX_AGENTS` | `10` | Max agents stimulated per run (safety cap) |
| `SEED_DRY_RUN` | `0` | When `1`, only log planned actions (no requests sent) |
| `AGENT_REGISTRY` | `autogen/agents/agent_registry.json` | Path to registry JSON |

Deprecated / Replaced Variables:

| Old Variable | Replacement | Rationale |
|--------------|-------------|-----------|
| `PROMETHEUS_BASE_URL` | `PROMETHEUS_BASE` | Unified naming convention |
| `SEED_ORGANIC_RPS_THRESHOLD` | `SEED_RPS_THRESHOLD` | Concise & consistent term |
| `SEED_ADAPTIVE_ENABLED` | (removed) | Adaptive always on; disable via stopping container |
| `SEED_PROM_QUERY_TIMEOUT` | (internal) | Fixed 3s timeout simplifies config |

Operational Guidance:

- Increase `SEED_RPS_THRESHOLD` to further reduce synthetic traffic once real users arrive.
- Lower `SEED_MAX_AGENTS` on constrained local laptops to reduce noise.
- Use `SEED_DRY_RUN=1 python scripts/synthetic_seed.py` locally (or via CI) to validate selection logic without network calls.
- During Prometheus outages the script treats missing data as zero RPS; consider disabling temporarily if this would cause unwanted stimulation.

Operational Impact: Reduces noise and prevents synthetic traffic inflating latency or error metrics once real users hit the system.

To disable adaptivity but retain baseline seeding:

```powershell
$env:SEED_ADAPTIVE_ENABLED="false"; docker compose up -d autogen-agent-traffic-seeder
```

## 24. Gateway Basic Auth Enforcement

Location: `docker/gateway/nginx.conf`

Protected paths: `/grafana/`, `/prometheus/`, `/alertmanager/`, `/agents/*/`.

Added directives per location:

```nginx
auth_basic "Restricted <Service>";
auth_basic_user_file /etc/nginx/.htpasswd;
```

Rate limiting (`limit_req`) applied with burst tuning to mitigate brute force.

Setup Steps:

```powershell
docker run --rm httpd:2.4-alpine htpasswd -nbB admin "Str0ngP@ss" > docker/gateway/htpasswd
# Add volume to gateway service if not present
docker compose up -d gateway
```

Security Notes:

- For production prefer OIDC / SSO; Basic Auth is a minimal interim guard.
- Ensure `.htpasswd` not committed publicly if storing real creds.

## 25. Correlation IDs & Structured Request Logging

Implemented in each agent (academic, developer, web-security, topics) via middleware inserting `X-Request-ID` (preserving incoming or generating UUID v4). Logs now emit lines:

```text
request_completed service=<svc> method=GET path=/health status=200 latency_s=0.0123 correlation_id=1c8e...
```

Usage:

- Propagate header from clients to tie together multi-service calls.
- Search logs by `correlation_id` for distributed debugging.
- Extend future tracing by mapping header → trace/span when adding OpenTelemetry.

Next Step Idea: Add middleware to gateway to inject header for external requests missing it, ensuring hop-to-hop continuity.

## 26. Dashboard Additions (Dynamic SLO Visualization)

File: `autogen/grafana-dashboard-config.json`

New Panels:

| Panel ID | Title | Purpose |
|----------|-------|---------|
| 11 | Agent p95 Latency (5m) | Unified latency across agents (dynamic) |
| 12 | Error Budget Burn Fast | 5m & 1h burn multipliers vs budget |
| 13 | Error Budget Burn Slow | 30m & 6h burn multipliers |
| 14 | Latency vs Warning Threshold | Overlay p95 with warning & critical thresholds |
| 15 | Error Rate vs Budget (5m) | Compare actual error % vs budget line |

Interpretation Guidelines:

- Burn > 14 (fast) or > 6 (slow) indicates budget depletion acceleration (alerts align with these thresholds).
- Latency crossing warning but below critical suggests watch / tune; sustained critical signals paging.
- Error rate close to budget (<1x) normal; 2–5x triggers warning/critical alerts (mirrors rule multipliers).

Provisioning Reminder: If dashboards not auto-loaded, ensure Grafana provisioning points to the JSON path or manually import.

---
Dynamic SLO refactor complete: thresholds are data-driven, alerts scale automatically, dashboard surfaces real-time conformance & burn, and request correlation supports incident forensics.

Disable a single burn alert: comment rule and reload Prometheus:

```powershell
curl -X POST http://localhost:9090/prometheus/-/reload
```

## 22. Dynamic Threshold Framework (Latency & Error Budgets)

## 20. Optional Gateway Basic Auth Scaffold

To enable simple Basic Auth (not enabled by default):

1. Create an `.htpasswd` file (example tooling via Docker):

   ```powershell
   docker run --rm httpd:2.4-alpine htpasswd -nbB admin "StrongPassword123" > docker/gateway/htpasswd
   ```

2. In `docker/gateway/nginx.conf`, inside `server {}` add commented reference then uncomment when ready:

   ```nginx
   # auth_basic "Restricted";
   # auth_basic_user_file /etc/nginx/htpasswd;
   ```

3. Mount the file by adding to gateway service volumes in `docker-compose.yml`:

   ```yaml
         - ./docker/gateway/htpasswd:/etc/nginx/htpasswd:ro
   ```

4. Reload gateway:

   ```powershell
   docker compose up -d gateway
   ```

For production: prefer OIDC or an identity-aware proxy and restrict Prometheus / Grafana further.

## 21. Error-Rate SLO (5xx) Monitoring

New recording rules and alerts extend SLO coverage from latency to reliability (5xx error ratio). Implemented in `docker/prometheus_rules.yml` via groups `agent-recording` (recordings) and `agents-slo-error` (alerts).

### 21.1 Recording Rules Added

| Record | Expression (summary) | Purpose |
|--------|----------------------|---------|
| `agent:<agent>:error_rate_5m` | 5xx over total over 5m | Short window error ratio |
| `agent:<agent>:error_rate_30m` | 5xx over total over 30m | Baseline for burn comparison |
| `agent:fleet:error_rate_5m` | Sum 5xx / sum total (5m) | Fleet-wide health snapshot |
| `agent:fleet:error_rate_30m` | Sum 5xx / sum total (30m) | Fleet baseline |

All expressions clamp denominators with `clamp_min(..., 1e-9)` to avoid division by zero on very low traffic.

### 21.2 Alert Rules

| Alert | Threshold | For | Severity | Description |
|-------|-----------|-----|----------|-------------|
| *Agent*ErrorRateHigh | >2% (0.02) | 10m | warning | Sustained elevated errors |
| *Agent*ErrorRateCritical | >5% (0.05) | 5m | critical | Rapid error spike requiring action |
| *Agent*ErrorBurnFast | >1% & >2x 30m baseline | 5m | warning | Early acceleration (burn) |
| AgentFleetErrorRateHigh | Fleet >3% (0.03) | 10m | critical | Broad / systemic failure |

Burn alerts rely on both an absolute floor (to ignore noise at near-zero) and a ratio multiplier (2x). Adjust these to control sensitivity.

### 21.3 Grafana Panels

Two new panels added in `autogen/grafana-dashboard-config.json`:

1. Agent Error Rate (5m) – individual agents (%).  
2. Error Rate Burn (5m vs 30m) – ratio (values >2 highlight fast deterioration).

Suggested annotation thresholds:

| Context | Warning | Critical |
|---------|---------|----------|
| Per-agent error % | 2% | 5% |
| Fleet error % | 2% | 3% |
| Burn ratio | 2x | 3x |

### 21.4 Tuning Guidance

- High baseline traffic: shorten evaluation `for` durations (e.g., 5m → 3m) for faster detection.  
- Low traffic agents: consider adding a minimum request rate guard (e.g., wrap alert expr with `sum(rate(<agent>_requests_total[5m])) > 0.1 and ...`).  
- Frequently flapping: raise thresholds incrementally (e.g., 2% → 2.5%) or lengthen `for` window.  
- Fleet threshold: keep slightly above typical aggregate noise to prevent single outlier from triggering fleet alert (current 3%).

### 21.5 Verification Steps

1. Reload Prometheus after rule changes:

   ```powershell
   curl -X POST http://localhost:9090/prometheus/-/reload
   ```
   
2. Induce a test 5xx: temporarily raise an exception in one agent endpoint and issue requests.
3. Confirm `agent:<agent>:error_rate_5m` rises in Prometheus expression browser.
4. Observe alert transition in Alertmanager (pending → firing) within configured `for` window.
5. Revert code, ensure metric returns near zero and alert resolves.

### 21.6 Remediation Playbook

| Scenario | Probable Causes | Actions |
|----------|-----------------|---------|
| Single agent spike | Recent deploy, dependency outage, bad input payload | Rollback or hotfix; inspect container logs; compare recent commits |
| Multi-agent simultaneous spike | Shared upstream (DB/cache/API) issue | Check upstream health & saturation; apply circuit breaker or rate limit |
| Fleet error with normal latency | Logic / functional regression | Identify common code path; enable debug logging; isolate failing route |
| High burn ratio but low absolute error % | Emerging issue / early warning | Increase sampling, capture traces, prep rollback pipeline |

Document root cause and resolution in CHANGELOG or incident log for future pattern recognition.

### 21.7 Future Enhancements

- Error budget burn (multi-window multi-factor e.g., 5m/1h & 30m/6h pairs).  
- Integrate tracing IDs into error responses for correlation.  
- Auto-mute alerts for known maintenance windows via Alertmanager silence automation.  
- Adaptive thresholds based on moving percentile of historical weeks.

---
Error SLO layer complete: latency + error coverage now form dual pillars for reliability governance.

