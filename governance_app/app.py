from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .github_client import GitHubClient
from .persistence import aggregate_stats, init_db, list_findings, recent_runs, record_run
from .processors.events import EventProcessor

try:  # optional redis import
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None

app = FastAPI(title="Governance App", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


settings = get_settings()
client = GitHubClient()
processor = EventProcessor(client)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# Alias /health for container orchestration probes (Dockerfile HEALTHCHECK expects /health)
@app.get("/health")
async def health():  # pragma: no cover - trivial alias
    return {"status": "ok"}


@app.get("/runs")
async def runs(
    limit: int = 20,
    offset: int = 0,
    repo: str | None = None,
    branch: str | None = None,
):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    items = list(recent_runs(limit=limit, offset=offset, repo=repo, branch=branch))
    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "offset": offset,
        "repo": repo,
        "branch": branch,
    }


@app.get("/findings")
async def findings(
    run_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    repo: str | None = None,
    branch: str | None = None,
    workflow: str | None = None,
    action: str | None = None,
):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    items = list(
        list_findings(
            run_id=run_id,
            limit=limit,
            offset=offset,
            repo=repo,
            branch=branch,
            workflow=workflow,
            action=action,
        )
    )
    return {
        "items": items,
        "count": len(items),
        "limit": limit,
        "offset": offset,
        "run_id": run_id,
        "repo": repo,
        "branch": branch,
        "workflow": workflow,
        "action": action,
    }


_delivery_cache: dict[str, float] = {}
_metrics = {
    "stats_cache_hits": 0,
    "stats_cache_misses": 0,
    "replay_blocks": 0,
}
_redis_client = None
_redis_ttl = int(os.getenv("WEBHOOK_REPLAY_WINDOW_SECONDS", "300"))
if os.getenv("REDIS_URL") and redis is not None:
    try:
        _redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))  # type: ignore
        _redis_client.ping()
    except Exception:  # pragma: no cover
        _redis_client = None


@app.post("/webhook")
async def webhook(request: Request):
    started = time.time()
    cid = str(uuid.uuid4())
    body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")
    event = request.headers.get("X-GitHub-Event", "unknown")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    # Replay protection
    replay_window = float(os.getenv("WEBHOOK_REPLAY_WINDOW_SECONDS", "300"))
    now = time.time()
    if delivery_id:
        if _redis_client:
            key = f"delivery:{delivery_id}"
            added = _redis_client.set(name=key, value=1, nx=True, ex=_redis_ttl)
            if not added:
                _metrics["replay_blocks"] += 1
                raise HTTPException(status_code=409, detail="Duplicate delivery (replay detected)")
        else:
            purge_keys = [k for k, ts in _delivery_cache.items() if now - ts > replay_window]
            for k in purge_keys:
                _delivery_cache.pop(k, None)
            if delivery_id in _delivery_cache:
                _metrics["replay_blocks"] += 1
                raise HTTPException(status_code=409, detail="Duplicate delivery (replay detected)")
            _delivery_cache[delivery_id] = now

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


_stats_cache: dict[str, object] = {"data": None, "expires": 0.0}


@app.get("/stats")
async def stats():
    ttl = float(os.getenv("STATS_CACHE_TTL_SECONDS", "15"))
    now = time.time()
    if _stats_cache["data"] is not None and now < _stats_cache["expires"]:
        _metrics["stats_cache_hits"] += 1
        return _stats_cache["data"]
    _metrics["stats_cache_misses"] += 1
    data = aggregate_stats()
    _stats_cache["data"] = data
    _stats_cache["expires"] = now + ttl
    return data


@app.get("/metrics")
async def metrics():
    # Expose minimal Prometheus-style metrics
    lines = [
        "# HELP governance_stats_cache_hits Number of cache hits for /stats endpoint",
        "# TYPE governance_stats_cache_hits counter",
        f"governance_stats_cache_hits {_metrics['stats_cache_hits']}",
        "# HELP governance_stats_cache_misses Number of cache misses for /stats endpoint",
        "# TYPE governance_stats_cache_misses counter",
        f"governance_stats_cache_misses {_metrics['stats_cache_misses']}",
        "# HELP governance_replay_blocks Number of blocked webhook deliveries (replay protection)",
        "# TYPE governance_replay_blocks counter",
        f"governance_replay_blocks {_metrics['replay_blocks']}",
    ]
    return JSONResponse({"raw": "\n".join(lines)})
