# --- Multi-Environment Deployment Orchestration ---
@app.post("/deploy/start")
async def deploy_start(env: str, version: str):
    """Trigger deployment to a given environment (staging/production)."""
    # TODO: Integrate with CI/CD or deployment system
    return {"status": "started", "env": env, "version": version}


@app.post("/deploy/blue-green")
async def deploy_blue_green(env: str, version: str):
    """Trigger blue-green deployment for zero-downtime releases (stub)."""
    # TODO: Implement blue-green deployment orchestration
    return {"status": "blue-green started", "env": env, "version": version}


# --- Advanced Analytics & Dashboard Endpoints ---
@app.get("/analytics/insights")
async def analytics_insights(repo: str = "", window_days: int = 30):
    """Return governance trends, risk heatmaps, and summary insights."""
    stats = aggregate_stats()
    # Example: risk = findings / runs
    for r in stats["repos"]:
        r["risk"] = (r["findings"] / r["runs"]) if r["runs"] else 0
    return {"repos": stats["repos"], "actions": stats["actions"]}


@app.get("/analytics/predictive")
async def analytics_predictive(repo: str = "", window_days: int = 90):
    """Predict likelihood of breaking changes based on historical data (stub)."""
    # TODO: Implement real predictive analytics
    stats = aggregate_stats()
    predictions = []
    for r in stats["repos"]:
        pred = {
            "repo": r["repo"],
            "predicted_breaking_changes": int(r["findings"] * 0.1),
            "confidence": 0.7,
        }
        predictions.append(pred)
    return {"predictions": predictions}


@app.get("/dashboard")
async def governance_dashboard():
    """Return a summary dashboard for governance health (stub)."""
    stats = aggregate_stats()
    return {"summary": stats}


from .openapi_diff import diff_openapi


# --- OpenAPI Contract Stability Endpoints ---
@app.post("/openapi/diff")
async def openapi_diff_endpoint(old: dict, new: dict):
    """Detect breaking changes and stability score between two OpenAPI specs."""
    result = diff_openapi(old, new)
    return result.to_dict()


@app.post("/openapi/alert")
async def openapi_alert_endpoint(old: dict, new: dict):
    """Trigger alert if stability score drops or breaking changes detected."""
    result = diff_openapi(old, new)
    if result.stability_score < 0.8 or result.breaking_changes:
        # TODO: Integrate with email/webhook alerting system
        return {
            "alert": True,
            "reason": "Stability degraded or breaking changes detected",
            **result.to_dict(),
        }
    return {"alert": False, **result.to_dict()}


from .persistence import aggregate_stats, list_findings, recent_runs


# --- Multi-Repo Aggregation Endpoints ---
@app.get("/aggregate/multi-repo")
async def aggregate_multi_repo(repos: str = "", min_findings: int = 0, max_results: int = 50):
    """Aggregate findings and runs across multiple repositories."""
    repo_list = [r.strip() for r in repos.split(",") if r.strip()]
    stats = aggregate_stats()
    filtered = [
        r
        for r in stats["repos"]
        if (not repo_list or r["repo"] in repo_list) and r["findings"] >= min_findings
    ]
    return {"repos": filtered[:max_results], "total": len(filtered)}


# --- Severity Scoring Aggregation ---
@app.get("/aggregate/severity")
async def aggregate_severity(repo: str = "", branch: str = "", limit: int = 100):
    """Aggregate findings by severity and trust (internal vs untrusted)."""
    findings = list(list_findings(repo=repo or None, branch=branch or None, limit=limit))
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    trust_counts = {"untrusted": 0, "internal": 0}
    for f in findings:
        raw = f.get("raw", {})
        sev = raw.get("severity", "info")
        if sev in severity_counts:
            severity_counts[sev] += 1
        if f.get("internal"):
            trust_counts["internal"] += 1
        else:
            trust_counts["untrusted"] += 1
    return {"severity": severity_counts, "trust": trust_counts, "total": len(findings)}


"""
Enhanced Governance App with Multi-Platform Support and Enhanced PR Comments
Supports GitHub, Coolify, GitLab, and other Git platforms
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .comment_generator import CommentGenerator
from .config import Platform, get_settings
from .persistence import init_db, record_run
from .platform_client import GitPlatformClient, create_platform_client
from .processors.events import EventProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:  # optional redis import
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None

app = FastAPI(title="Enhanced Governance App", version="0.2.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    logger.info(f"Governance app started with platform: {settings.platform}")


settings = get_settings()

# Create platform-specific client
try:
    platform_config = settings.get_platform_config()
    client: GitPlatformClient = create_platform_client(settings.platform, platform_config)
    logger.info(f"Initialized {settings.platform} client successfully")
except Exception as e:
    logger.error(f"Failed to initialize platform client: {e}")
    raise

# Initialize components
comment_generator = CommentGenerator()
processor = EventProcessor(client, comment_generator)


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "platform": settings.platform,
        "features": {
            "enhanced_comments": settings.enhanced_comments,
            "comment_generation": settings.comment_generation_enabled,
            "check_runs": settings.check_run_enabled,
        },
    }


# Alias /health for container orchestration probes (Dockerfile HEALTHCHECK expects /health)
@app.get("/health")
async def health():  # pragma: no cover - trivial alias
    return await healthz()


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


@app.get("/runs/{run_id}/findings")
async def run_findings(
    run_id: int,
    limit: int = 100,
    offset: int = 0,
):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    items = list(
        list_findings(
            run_id=run_id,
            limit=limit,
            offset=offset,
        )
    )
    return {
        "items": items,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "run_id": run_id,
    }


_delivery_cache: dict[str, float] = {}
_metrics = {
    "stats_cache_hits": 0,
    "stats_cache_misses": 0,
    "replay_blocks": 0,
    "webhook_processed": 0,
    "comments_generated": 0,
    "check_runs_created": 0,
}
_redis_client = None
_redis_ttl = int(os.getenv("WEBHOOK_REPLAY_WINDOW_SECONDS", "300"))
if os.getenv("REDIS_URL") and redis is not None:
    try:
        _redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))  # type: ignore
        _redis_client.ping()
    except Exception:  # pragma: no cover
        _redis_client = None

    def get_webhook_headers(request: Request) -> tuple[str, str, str]:
        """Extract webhook headers based on platform"""
        platform = Platform(settings.platform)

        if platform == Platform.GITHUB:
            event = request.headers.get("X-GitHub-Event", "unknown")
            signature = request.headers.get("X-Hub-Signature-256", "")
            delivery_id = request.headers.get("X-GitHub-Delivery", "")
        elif platform == Platform.COOLIFY:
            event = request.headers.get(
                "X-Coolify-Event", request.headers.get("X-Event-Type", "unknown")
            )
            signature = request.headers.get(
                "X-Coolify-Signature", request.headers.get("X-Hub-Signature-256", "")
            )
            delivery_id = request.headers.get(
                "X-Coolify-Delivery", request.headers.get("X-Request-ID", "")
            )
        elif platform == Platform.GITLAB:
            event = request.headers.get("X-Gitlab-Event", "unknown")
            signature = request.headers.get("X-Gitlab-Token", "")
            delivery_id = request.headers.get("X-Gitlab-Event-UUID", "")
        elif platform == Platform.BITBUCKET:
            event = request.headers.get("X-Event-Key", "unknown")
            signature = request.headers.get("X-Hub-Signature", "")
            delivery_id = request.headers.get("X-Request-UUID", "")
        else:
            # Fallback - try common header names
            event = request.headers.get("X-Event-Type", request.headers.get("X-Event", "unknown"))
            signature = request.headers.get(
                "X-Hub-Signature-256", request.headers.get("X-Signature", "")
            )
            delivery_id = request.headers.get(
                "X-Delivery-ID", request.headers.get("X-Request-ID", "")
            )

        return event, signature, delivery_id


def get_webhook_headers(request: Request) -> tuple[str, str, str]:
    """Extract webhook headers based on platform"""
    platform = Platform(settings.platform)

    if platform == Platform.GITHUB:
        event = request.headers.get("X-GitHub-Event", "unknown")
        signature = request.headers.get("X-Hub-Signature-256", "")
        delivery_id = request.headers.get("X-GitHub-Delivery", "")
    elif platform == Platform.COOLIFY:
        event = request.headers.get(
            "X-Coolify-Event", request.headers.get("X-Event-Type", "unknown")
        )
        signature = request.headers.get(
            "X-Coolify-Signature", request.headers.get("X-Hub-Signature-256", "")
        )
        delivery_id = request.headers.get(
            "X-Coolify-Delivery", request.headers.get("X-Request-ID", "")
        )
    elif platform == Platform.GITLAB:
        event = request.headers.get("X-Gitlab-Event", "unknown")
        signature = request.headers.get("X-Gitlab-Token", "")
        delivery_id = request.headers.get("X-Gitlab-Event-UUID", "")
    elif platform == Platform.BITBUCKET:
        event = request.headers.get("X-Event-Key", "unknown")
        signature = request.headers.get("X-Hub-Signature", "")
        delivery_id = request.headers.get("X-Request-UUID", "")
    else:
        # Fallback - try common header names
        event = request.headers.get("X-Event-Type", request.headers.get("X-Event", "unknown"))
        signature = request.headers.get(
            "X-Hub-Signature-256", request.headers.get("X-Signature", "")
        )
        delivery_id = request.headers.get("X-Delivery-ID", request.headers.get("X-Request-ID", ""))

    return event, signature, delivery_id


@app.post("/webhook")
async def webhook(request: Request):
    started = time.time()
    cid = str(uuid.uuid4())
    body = await request.body()

    # Extract platform-specific headers
    event, sig_header, delivery_id = get_webhook_headers(request)

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

        # Verify webhook signature using platform-specific client
        if settings.webhook_secret:
            try:
                is_valid = await client.verify_webhook_signature(body, sig_header)
                if not is_valid:
                    raise HTTPException(status_code=401, detail="Invalid signature")
            except Exception as e:
                logger.error(f"Signature verification failed: {e}")
                raise HTTPException(status_code=401, detail="Signature verification failed")

    payload = await request.json()

    # Parse webhook event using platform abstraction
    try:
        webhook_event = await client.parse_webhook_event(dict(request.headers), payload)
        logger.info(
            f"Processing {webhook_event.event_type} event for {webhook_event.repository.full_name}"
        )
    except Exception as e:
        logger.error(f"Failed to parse webhook event: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    # Process the event
    result = {"status": "unhandled", "event": event}

    if webhook_event.event_type in ["push", "Push Hook"]:
        result = await processor.handle_push_event(webhook_event)
        if result.get("status") == "ok":
            record_run(
                webhook_event.repository.full_name,
                result.get("branch", "unknown"),
                result.get("workflows_scanned", 0),
                result.get("findings", []),
            )
    elif webhook_event.event_type in [
        "pull_request",
        "Merge Request Hook",
        "pullrequest:created",
        "pullrequest:updated",
    ]:
        result = await processor.handle_pull_request_event(webhook_event)

    elapsed = time.time() - started
    log = {
        "correlation_id": cid,
        "platform": settings.platform,
        "event": event,
        "repository": webhook_event.repository.full_name,
        "status": result.get("status"),
        "elapsed_ms": int(elapsed * 1000),
        "findings_count": (
            sum(len(f.get("issues", [])) for f in result.get("findings", []))
            if result.get("status") == "ok"
            else 0
        ),
    }
    logger.info(json.dumps(log))
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
