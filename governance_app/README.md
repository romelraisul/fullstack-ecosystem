# Governance App Service

FastAPI-based GitHub governance automation service (successor of `governance-app`).

## Features

- Webhook handling (push + PR placeholder)
- HMAC signature verification
- Diff-based workflow file discovery
- External action reference extraction & unpinned detection
- GitHub App installation token usage (when available)
- SQLite persistence of runs & findings
- Structured JSON logging (correlation_id, timing)
- Check Run creation summarizing unpinned external actions
- REST API: `/healthz`, `/runs`, `/findings`, `/runs/{id}/findings`, `/stats`
- Pagination & filtering for runs/findings
- Local simulation script

## Install / Run (Local)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r governance-app/requirements.txt
$env:WEBHOOK_SECRET='devsecret'
# run from repo root containing governance_app/
python -m uvicorn governance_app.app:app --port 8081 --reload
```

In another shell:

```powershell
# Ensure an example workflow exists
if (!(Test-Path '.github/workflows')) { New-Item -ItemType Directory -Path '.github/workflows' | Out-Null }
@'
name: Example
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: someorg/someaction@v1
'@ | Set-Content '.github/workflows/example.yml'

$env:GOV_APP_PORT='8081'
python governance_app/sample_push_event.py
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Liveness check |
| `/runs` | GET | Paginated recent runs (filters: repo, branch) |
| `/findings` | GET | Paginated findings (filters: run_id, repo, branch, workflow, action) |
| `/runs/{id}/findings` | GET | Findings for a specific run (supports pagination & workflow/action filters) |
| `/stats` | GET | Aggregate stats (totals, per-repo, per-action) |

### OpenAPI Examples

#### GET /runs

Request:

```http
GET /runs?limit=5&offset=0&repo=org/repo1 HTTP/1.1
Host: localhost:8081
```

Response (200):

```json
{
  "items": [
    {"id": 42, "ts": "2025-10-02T09:00:00Z", "repo": "org/repo1", "branch": "main", "workflows_scanned": 3, "findings_count": 1}
  ],
  "count": 1,
  "limit": 5,
  "offset": 0,
  "repo": "org/repo1",
  "branch": null
}
```

#### GET /findings

```http
GET /findings?repo=org/repo1&workflow=ci.yml&limit=50 HTTP/1.1
```

```json
{
  "items": [
    {"id": 7, "run_id": 42, "workflow": "ci.yml", "action": "someorg/action", "ref": "v1", "pinned": false, "internal": false, "raw": {"action": "someorg/action", "ref": "v1"}}
  ],
  "count": 1,
  "limit": 50,
  "offset": 0,
  "run_id": null,
  "repo": "org/repo1",
  "branch": null,
  "workflow": "ci.yml",
  "action": null
}
```

#### GET /runs/{id}/findings

```http
GET /runs/42/findings?limit=10 HTTP/1.1
```

```json
{
  "run_id": 42,
  "limit": 10,
  "offset": 0,
  "filters": {},
  "total": 2,
  "items": [
    {"id": 8, "run_id": 42, "workflow": "ci.yml", "action": "actions/checkout", "ref": "v4", "pinned": true, "internal": false, "raw": {"action": "actions/checkout", "ref": "v4"}},
    {"id": 7, "run_id": 42, "workflow": "ci.yml", "action": "someorg/action", "ref": "v1", "pinned": false, "internal": false, "raw": {"action": "someorg/action", "ref": "v1"}}
  ]
}
```

#### GET /stats

```http
GET /stats HTTP/1.1
```

```json
{
  "total_runs": 12,
  "total_findings": 34,
  "repos": [
    {"repo": "org/repo1", "runs": 6, "findings": 20}
  ],
  "actions": [
    {"action": "actions/checkout", "occurrences": 12, "unpinned": 0, "pinned": 12},
    {"action": "someorg/action", "occurrences": 8, "unpinned": 8, "pinned": 0}
  ]
}
```

### Notes

Limits are clamped: `/runs` max 200 items, `/findings` max 500. Always prefer paginating rather than requesting large limits.

## Environment Variables

| Name | Purpose | Default |
|------|---------|---------|
| WEBHOOK_SECRET | HMAC secret for signature verification | (none) |
| GITHUB_APP_ID | GitHub App ID | – |
| GITHUB_APP_PRIVATE_KEY | PEM private key contents | – |
| GITHUB_WEBHOOK_SECRET | Alias for WEBHOOK_SECRET (legacy) | – |
| GITHUB_API_URL | GitHub API base URL | <https://api.github.com> |
| GOV_APP_USER_AGENT | Custom UA | governance-app/0.1 |
| GOV_APP_PORT | Simulation script target port | 8081 |
| STATS_CACHE_TTL_SECONDS | Cache TTL for /stats endpoint | 15 |
| WEBHOOK_REPLAY_WINDOW_SECONDS | Time window to treat duplicate delivery IDs as replays | 300 |
| REDIS_URL | Optional Redis for distributed replay protection (e.g. redis://host:6379/0) | (none) |

## Docker

Dockerfile included at `governance_app/Dockerfile`:

```bash
docker build -t governance-app -f governance_app/Dockerfile .
docker run -e WEBHOOK_SECRET=devsecret -p 8081:8081 governance-app
```

## Badges

Daily governance stats badge workflow (`governance-stats-badge.yml`) writes
`badge-governance-stats.json` (Shields.io compatible). Example usage:

```markdown
![governance](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<owner>/<repo>/main/badge-governance-stats.json)
```

The generation script also creates timestamped historical snapshots under
`metrics-history/` (e.g. `governance-stats-20250101093045.json`). Snapshots
older than 90 days are automatically pruned each run to keep repository size
manageable.

## OpenAPI Schema Export

An automated workflow (`governance-openapi-export.yml`) produces an
`openapi-governance.json` artifact on pushes touching the app or the export
script (and via manual dispatch). Download it from the workflow run page to
integrate with tooling (client generation, spectral linting, etc.).

The same workflow also publishes the latest schema to the `schemas` branch at:

```text
schemas/openapi-governance.json
```

You can reference a raw URL directly (replace <owner>/<repo>):

```text
https://raw.githubusercontent.com/<owner>/<repo>/schemas/schemas/openapi-governance.json
```

Generate locally:

```powershell
python scripts/export_openapi_schema.py --out openapi-governance.json
```

The schema includes `x-generated-at` and `x-governance-version` custom extensions for traceability.

## Security Notes

- Ensure private key is mounted via secret store.
- Consider rotating WEBHOOK_SECRET regularly.
- Future: rate limiting and audit logging.

## License / Status

Prototype—NOT production hardened. Expect breaking changes.
