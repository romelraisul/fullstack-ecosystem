# Governance App Service

FastAPI-based GitHub governance automation service (successor of `governance-app`).

## Features

- Webhook handling (push; PR ignored placeholder)
- HMAC signature verification
- Diff-based workflow file discovery
- External action reference extraction & unpinned detection
- GitHub App installation token usage (when available)
- SQLite persistence of runs & findings
- Structured JSON logging (correlation_id, timing)
- Check Run creation summarizing unpinned external actions
- REST API: /healthz, /runs, /findings (pagination & filtering WIP)
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

## API (Current)

| Endpoint | Method | Query Params | Description |
|----------|--------|--------------|-------------|
| /healthz | GET | – | Liveness check |
| /runs | GET | limit (int) | Recent runs (cap 200) |
| /findings | GET | run_id (int), limit (int) | Findings (optionally for a run) |

### Planned Enhancements

- `/runs` support: offset, repo, branch filters
- `/findings` support: offset, repo, branch, workflow filters
- `/runs/{id}/findings` convenience endpoint

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

## Docker (to be added)

Planned Dockerfile will support multi-stage build and non-root execution.

## Security Notes

- Ensure private key is mounted via secret store.
- Consider rotating WEBHOOK_SECRET regularly.
- Future: rate limiting and audit logging.

## License / Status

Prototype—NOT production hardened. Expect breaking changes.
