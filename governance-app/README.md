# Governance App (Prototype)

Minimal FastAPI-based GitHub App backend to support CI governance automation.

## Features (Initial)

- /healthz endpoint
- /webhook endpoint (push & pull_request basic handling)
- HMAC signature verification (X-Hub-Signature-256)
- Action reference extraction + unpinned detection placeholder

## Install / Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r governance-app/requirements.txt
uvicorn governance-app.app:app --reload --port 8000
```

## Environment Variables

| Name | Purpose |
|------|---------|
| GITHUB_APP_ID | App identifier |
| GITHUB_APP_PRIVATE_KEY | PEM private key contents (multi-line) |
| GITHUB_WEBHOOK_SECRET | Shared HMAC secret |
| GITHUB_API_URL | Override for GH Enterprise (default api.github.com) |

## Webhook Development (ngrok)

```bash
ngrok http 8000
```

Set the public URL as the webhook in the temporary App setup (or update manifest).

## Manifest Flow

1. Create new GitHub App via UI (paste `manifest.yml`).
2. Capture App ID + private key, store securely.
3. Set environment variables before starting.

## TODO / Next Steps

- Fetch installation token & retrieve actual changed workflow files.
- Parse diff from push payload for workflow paths.
- Post check-run or PR comment summarizing unpinned refs.
- Persist metrics / snapshots centrally.

## Testing

(Prototype test structure; adjust PYTHONPATH accordingly.)

```bash
pytest -q
```

## Disclaimer

Prototype scaffold for iterative hardening; not production-ready (no retries,
no logging enrichment, no persistence layer yet).
