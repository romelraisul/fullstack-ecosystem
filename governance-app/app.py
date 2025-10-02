from __future__ import annotations
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from .config import get_settings
from .github_client import GitHubClient
from .processors.events import EventProcessor

app = FastAPI(title="Governance App", version="0.1.0")
settings = get_settings()
client = GitHubClient()
processor = EventProcessor(client)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")
    event = request.headers.get("X-GitHub-Event", "unknown")

    if settings.webhook_secret:
        if not sig_header or not sig_header.startswith("sha256="):
            raise HTTPException(status_code=400, detail="Missing signature")
        digest = hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        if not hmac.compare_digest(sig_header, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    if event == "push":
        result = await processor.handle_push(payload)
    elif event == "pull_request":
        result = await processor.handle_pull_request(payload)
    else:
        result = {"status": "unhandled", "event": event}

    return JSONResponse(result)
