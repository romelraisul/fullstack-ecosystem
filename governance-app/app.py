from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .github_client import GitHubClient
from .persistence import init_db, list_findings, recent_runs, record_run
from .processors.events import EventProcessor

app = FastAPI(title="Governance App", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    # Initialize database schema
    init_db()


settings = get_settings()
client = GitHubClient()
processor = EventProcessor(client)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/runs")
async def runs(limit: int = 20):  # noqa: D401 - simple endpoint
    limit = max(1, min(limit, 200))
    return {"items": list(recent_runs(limit=limit)), "count": limit}


@app.get("/findings")
async def findings(run_id: int | None = None, limit: int = 100):
    limit = max(1, min(limit, 500))
    return {
        "items": list(list_findings(run_id=run_id, limit=limit)),
        "count": limit,
        "run_id": run_id,
    }


@app.post("/webhook")
async def webhook(request: Request):
    started = time.time()
    cid = str(uuid.uuid4())
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
        # Persist run summary if successful
        if result.get("status") == "ok":
            repo = payload.get("repository", {}).get("full_name", "unknown")
            record_run(
                repo,
                result.get("branch", "unknown"),
                result.get("workflows_scanned", 0),
                result.get("findings", []),
            )
    elif event == "pull_request":
        result = await processor.handle_pull_request(payload)
    else:
        result = {"status": "unhandled", "event": event}
    elapsed = time.time() - started
    log = {
        "correlation_id": cid,
        "event": event,
        "status": result.get("status"),
        "elapsed_ms": int(elapsed * 1000),
        "findings_count": (
            sum(len(f.get("issues", [])) for f in result.get("findings", []))
            if result.get("status") == "ok"
            else 0
        ),
    }
    print(json.dumps(log), flush=True)
    result["correlation_id"] = cid
    return JSONResponse(result)
