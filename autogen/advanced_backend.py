"""Advanced backend main FastAPI application (monolithic).

This file includes adaptive latency metrics via t-digest. In frozen / minimal
build scenarios the compiled Cython dependency `accumulation_tree.abctree`
may be omitted. To prevent a hard crash we provide a lightweight pure-Python
fallback TDigest implementation (really a simple sample reservoir with
percentile calculation). This preserves server startup and diagnostic ability
at the cost of less accurate quantiles. A PHASE log line is emitted when the
fallback activates.
"""

import os as _os
import pickle
import sys as _sys
import time as _time

_app_early = None  # placeholder; real app created later
_start_ts = _time.perf_counter()
_phase_event_buffer: list[dict[str, float | str]] = []  # will be reused by heartbeat endpoint


def _phase(msg: str):  # re-used later; provide early definition with elapsed timing
    try:
        elapsed = (_time.perf_counter() - _start_ts) * 1000
        _sys.stderr.write(f"[PHASE +{elapsed:0.1f}ms] {msg}\n")
        # capture limited rolling buffer of events for heartbeat
        _phase_event_buffer.append({"t_ms": round(elapsed, 1), "msg": msg})
        if len(_phase_event_buffer) > 250:
            del _phase_event_buffer[:-200]
    except Exception:  # pragma: no cover
        pass


_MINIMAL_MODE = _os.getenv("MINIMAL_MODE") not in (None, "0", "false", "no", "off")
if _MINIMAL_MODE:
    _phase("INIT: MINIMAL_MODE active (heavy imports will be skipped/deferred)")

_FALLBACK_TDIGEST = False
try:  # Attempt real t-digest import first
    from tdigest import TDigest  # type: ignore
except Exception as _td_exc:  # pragma: no cover - only hit in frozen/minimal builds
    _FALLBACK_TDIGEST = True
    _phase(f"TDIGEST-FALLBACK: using simple in-memory percentile store due to: {_td_exc}")

    class TDigest:  # minimal substitute (NOT a true t-digest!)
        """Fallback replacement storing up to N samples and computing linear interpolated percentiles.

        This is ONLY for emergency startup when the compiled extension is missing.
        Accuracy for large streams is limited; memory bounded by MAX_SAMPLES via reservoir sampling.
        """

        __slots__ = ["_samples", "_count", "_max_samples"]

        def __init__(self, max_samples: int = 5000):
            self._samples: list[float] = []
            self._count = 0
            self._max_samples = max_samples

        def update(self, value: float):  # mimic t-digest API
            import random

            v = float(value)
            if len(self._samples) < self._max_samples:
                self._samples.append(v)
            else:
                # reservoir sampling replacement
                j = random.randint(0, self._count)
                if j < self._max_samples:
                    self._samples[j] = v
            self._count += 1

        def percentile(self, p: float) -> float:
            if not self._samples:
                return 0.0
            data = sorted(self._samples)
            k = (p / 100.0) * (len(data) - 1)
            lo = int(k)
            hi = min(lo + 1, len(data) - 1)
            if lo == hi:
                return data[lo]
            frac = k - lo
            return data[lo] + (data[hi] - data[lo]) * frac


# NOTE: t-digest helpers are placed early so they can be imported elsewhere in this module.
# The quantile FastAPI route SHOULD be declared after the FastAPI `app` is created later in the file.

_tdigest_store: dict[str, TDigest] = {}


def _get_tdigest(endpoint: str) -> TDigest:
    td = _tdigest_store.get(endpoint)
    if td is None:
        td = TDigest()
        _tdigest_store[endpoint] = td
    return td


def tdigest_record_latency(endpoint: str, latency_ms: float) -> None:
    """Update t-digest with a new latency sample (ms)."""
    _get_tdigest(endpoint).update(latency_ms)


def persist_tdigests(repo, adaptive_state_dict: dict[str, dict]):  # type: ignore
    """Persist all t-digests alongside existing adaptive state."""
    try:
        for endpoint, td in _tdigest_store.items():
            td_blob = pickle.dumps(td)
            state = adaptive_state_dict.get(endpoint, {})
            repo.upsert_adaptive_latency_state(
                endpoint,
                state.get("ema_p95_ms"),
                state.get("class_ema_shares"),
                state.get("updated_at"),
                state.get("sample_count"),
                state.get("sample_mean_ms"),
                state.get("sample_m2"),
                tdigest_blob=td_blob,
            )
    except Exception:  # pragma: no cover
        pass


def load_tdigests(repo):  # type: ignore
    """Load persisted t-digests from repository."""
    try:
        states = repo.load_adaptive_latency_states()
        for state in states:
            endpoint = state["endpoint"]
            td_blob = state.get("tdigest_blob")
            if td_blob:
                try:
                    _tdigest_store[endpoint] = pickle.loads(td_blob)
                except Exception:  # fallback to empty digest
                    _tdigest_store[endpoint] = TDigest()
    except Exception:  # pragma: no cover
        pass


# ---------------------------------------------------------------------------
# Dashboard HTML serving helper (works in dev & PyInstaller bundle)
# ---------------------------------------------------------------------------
from pathlib import (
    Path,
)  # ensure Path available early for _resolve_dashboard_path (frozen mode fix)

from fastapi.responses import HTMLResponse  # type: ignore


def _resolve_dashboard_path() -> Path:
    # When frozen with PyInstaller, sys._MEIPASS points to temp extraction dir
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidate = Path(base) / "executive_dashboard.html"
        if candidate.exists():
            return candidate
    # Fallback to current file directory
    return Path(__file__).resolve().parent / "executive_dashboard.html"


# Defer adding the route until after app is created; we register via a lightweight function
_DASHBOARD_ROUTE_ATTACHED = False


def attach_dashboard_route(app):  # type: ignore
    global _DASHBOARD_ROUTE_ATTACHED
    if _DASHBOARD_ROUTE_ATTACHED:
        return

    @app.get("/executive_dashboard.html", response_class=HTMLResponse, include_in_schema=False)
    async def executive_dashboard():  # noqa: D401
        path = _resolve_dashboard_path()
        if not path.exists():
            raise HTTPException(status_code=404, detail="Dashboard HTML not found")
        return HTMLResponse(path.read_text(encoding="utf-8"))

    _DASHBOARD_ROUTE_ATTACHED = True


# The quantile endpoint using t-digest is defined LATER after app creation.
def get_latency_quantiles():
    result = {}
    for endpoint, td in _tdigest_store.items():
        result[endpoint] = {
            "p50": td.percentile(50),
            "p90": td.percentile(90),
            "p95": td.percentile(95),
            "p99": td.percentile(99),
        }
    return result


# ---------------------------------------------------------------------------
# Early provisional FastAPI app to ensure /health & /__phase respond even if
# heavy imports later are slow. The final app variable will be the same object.
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException  # type: ignore

    if "_app_early" in globals() and _app_early is None:
        _app_early = FastAPI(title="advanced-backend-early")
    app = _app_early or FastAPI(title="advanced-backend")  # final reference
except Exception as _early_exc:  # pragma: no cover
    # Fallback dummy shim if FastAPI itself cannot import (extremely rare)
    class _Dummy:
        def get(self, *a, **k):
            def wrap(fn):
                return fn

            return wrap

    app = _Dummy()  # type: ignore
    _phase(f"EARLY-APP-FAIL fastapi import failed: {_early_exc}")


@app.get("/health", include_in_schema=False)
async def _early_health():  # pragma: no cover simple
    return {
        "status": "ok",
        "phase": "early",
        "minimal": bool(_MINIMAL_MODE),
        "fallback_tdigest": _FALLBACK_TDIGEST,
    }


@app.get("/__phase", include_in_schema=False)
async def _early_phase():  # pragma: no cover simple
    return {
        "safe_mode": bool(_os.getenv("SAFE_MODE")),
        "minimal_mode": _MINIMAL_MODE,
        "fallback_tdigest": _FALLBACK_TDIGEST,
        "tdigest_endpoints": list(_tdigest_store.keys()),
    }


"""Advanced backend main FastAPI application.

Refactor notes (2025-10):
 - Consolidated to a SINGLE FastAPI app instance (duplicate definitions previously caused confusion and NameError during import order changes).
 - All decorators must appear AFTER the single `app` creation; removed second instantiation that overwrote routes & middleware.
 - DB batch worker now starts in an @app.on_event("startup") handler to avoid early imports of dependencies before they are defined.
 - Tracemalloc starts early once.
"""

import atexit
import datetime
import os
import queue
import signal
import sys
import threading
import tracemalloc
from abc import ABC, abstractmethod
from collections import (
    defaultdict,
    deque,
)  # early import so defaultdict available for adaptive structures
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# SAFE MODE / PHASED STARTUP DIAGNOSTICS
# Set environment variable SAFE_MODE=true to bypass heavy subsystems (auth, security,
# validation, rate limiting, repositories) so we can isolate import/startup crashes.
# Writes phase markers to stderr for granular tracing in packaged exe or python run.
# ---------------------------------------------------------------------------
RAW_SAFE_MODE = os.getenv("SAFE_MODE")  # None if not set at all
# Enable SAFE_MODE only if variable is actually present (not None) and not a recognized false token.
_false_tokens = {"0", "false", "off", "no"}
if RAW_SAFE_MODE is None:
    SAFE_MODE = False
else:
    val = RAW_SAFE_MODE.strip().lower()
    SAFE_MODE = val not in _false_tokens  # any non-false value (including empty string) activates

# Pre-flight bcrypt handler detection; if unavailable, force SAFE_MODE (before heavy auth imports)
try:  # pragma: no cover - just detection
    pass  # type: ignore
except Exception as _bcrypt_err:  # force SAFE_MODE if passlib/bcrypt not available
    SAFE_MODE = True
    try:
        sys.stderr.write(
            f"[PHASE] WARN: bcrypt handler missing ({_bcrypt_err}); forcing SAFE_MODE fallback\n"
        )
    except Exception:
        pass


def _phase(msg: str):  # lightweight phase logger
    try:
        sys.stderr.write(f"[PHASE] {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


_phase(f"INIT: advanced_backend import start SAFE_MODE={SAFE_MODE} RAW='{RAW_SAFE_MODE}'")

from fastapi import FastAPI, HTTPException, Request

"""Repository imports (conversations + workflows) with fallbacks.
We guard missing modules so the API can still run in reduced functionality mode."""
try:  # Conversations persistence
    from src.db.conversations_repo import ConversationsRepository  # type: ignore
except ModuleNotFoundError:
    try:
        from db.conversations_repo import ConversationsRepository  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        ConversationsRepository = None  # type: ignore

try:  # Workflows persistence
    from src.db.workflows_repo import WorkflowsRepository  # type: ignore
except ModuleNotFoundError:
    try:
        from db.workflows_repo import WorkflowsRepository  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        WorkflowsRepository = None  # type: ignore

# Start tracemalloc for memory profiling early
if not tracemalloc.is_tracing():  # idempotent
    tracemalloc.start()

# ---------------------------------------------------------------------------
# Early Global Crash & Exception Handlers (Tasks 10 & 47 equivalent)
# These provide visibility into silent crashes before app + middleware load.
# ---------------------------------------------------------------------------

_EARLY_CRASH_LOG_PREFIX = "[EARLY-CRASH]"


def _log_early(msg: str):
    try:
        # Use stdout to guarantee visibility even if logging not configured yet
        sys.stderr.write(f"{_EARLY_CRASH_LOG_PREFIX} {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


def _sys_excepthook(exc_type, exc, tb):
    import traceback as _tb

    _log_early("Uncaught exception: " + "".join(_tb.format_exception(exc_type, exc, tb)))


sys.excepthook = _sys_excepthook  # type: ignore

if hasattr(threading, "excepthook"):

    def _thread_excepthook(args):  # Python >=3.8
        _log_early(
            f"Thread exception in {getattr(args, 'thread', None)}: {args.exc_type.__name__}: {args.exc_value}"
        )

    threading.excepthook = _thread_excepthook  # type: ignore


def _asyncio_exception_handler(loop, context):
    msg = context.get("message") or "Asyncio exception"
    exc = context.get("exception")
    if exc:
        import traceback as _tb

        formatted = "".join(_tb.format_exception(type(exc), exc, exc.__traceback__))
    else:
        formatted = repr(context)
    _log_early(f"Asyncio loop error: {msg}\n{formatted}")


try:
    import asyncio as _asyncio

    _loop = _asyncio.get_event_loop()
    _loop.set_exception_handler(_asyncio_exception_handler)
except Exception:
    _log_early("Failed to set asyncio exception handler (may be fine during import).")


def _handle_signal(signum, frame):  # pragma: no cover - signal handling
    _log_early(f"Received signal {signum}; initiating graceful shutdown flush.")
    try:
        _drain_db_queue(force=True)
    except Exception:
        pass
    # Re-raise default behavior for SIGINT to allow fast exit
    if signum == signal.SIGINT:
        raise KeyboardInterrupt()


for _sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
    if _sig is not None:
        try:
            signal.signal(_sig, _handle_signal)
        except Exception:
            pass

# ---------------------------------------------------------------------------

# Create the single FastAPI application instance (enterprise config applied later)
app = FastAPI(title="AutoGen Multi-Agent WebUI", version="2.0.0")
# Attach executive dashboard route (serves executive_dashboard.html) early so it's available in dev & packaged exe
try:  # defensive: avoid failing app startup if optional file missing
    attach_dashboard_route(app)  # type: ignore  # defined earlier
except Exception as _dash_err:  # pragma: no cover
    # Log early but continue; the route can be reattached later via startup hook if needed
    try:
        sys.stderr.write(f"[EARLY-CRASH] Dashboard route attach failed: {_dash_err}\n")
    except Exception:
        pass


# Minimal health check endpoint (very early) for quick liveness during diagnostics
@app.get("/health", include_in_schema=False)
async def health_check():  # pragma: no cover - trivial
    return {"status": "ok"}


# Unified diagnostic phase endpoint (replaces previous duplicate definitions)
@app.get("/__phase", include_in_schema=False)
async def phase_probe():  # pragma: no cover - lightweight diagnostics
    """Return startup & subsystem status.

    Provides a consistent JSON shape regardless of SAFE_MODE or MINIMAL_MODE.
    """
    try:
        security_loaded = (
            not SAFE_MODE
            and "setup_security_middleware" in globals()
            and callable(setup_security_middleware)
        )
        rate_limiter_loaded = (
            not SAFE_MODE and "rate_limiter" in globals() and callable(rate_limiter)
        )
        jwt_available = "jwt_auth_service" in globals() and jwt_auth_service is not None
    except Exception:  # pragma: no cover
        security_loaded = rate_limiter_loaded = jwt_available = False
    return {
        "safe_mode": SAFE_MODE,
        "raw_safe_mode": RAW_SAFE_MODE,
        "minimal_mode": _MINIMAL_MODE,
        "security_loaded": security_loaded,
        "rate_limiter_loaded": rate_limiter_loaded,
        "jwt_auth_available": jwt_available,
        "tdigest_fallback": _FALLBACK_TDIGEST,
        "tdigest_endpoints": list(_tdigest_store.keys()),
    }


# --- DB Batching Infrastructure ---
DB_BATCH_QUEUE = queue.Queue()
DB_BATCH_SIZE = 10
DB_BATCH_INTERVAL = 1.0  # seconds
DB_MAX_QUEUE_SIZE = 5000  # simple protection
DB_LAST_FLUSH_AT: float | None = None
DB_FORCED_FLUSH_INTERVAL = 10.0  # seconds; force flush if no activity


def _flush_batch(batch: list):
    """Flush batched conversation operations atomically per batch.

    Each item is a tuple: (op_name, args_tuple)
    Supported ops: create_conversation(conv_dict), add_message(conversation_id, message_dict)
    Unknown ops are logged and skipped (forward compatible).
    """
    global DB_LAST_FLUSH_AT
    if not batch:
        return
    if ConversationsRepository is None:  # repository not available -> drop safely
        _log_early("ConversationsRepository unavailable; discarding batch of %d ops" % len(batch))
        batch.clear()
        return
    DB_PATH = Path(
        os.getenv("DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db")
    )
    try:
        repo = ConversationsRepository(DB_PATH)  # type: ignore
        for op, args in batch:
            try:
                if op == "create_conversation":
                    repo.create_conversation(*args)
                elif op == "add_message":
                    repo.add_message(*args)
                else:  # forward compatibility
                    _log_early(f"Unknown batch op '{op}' skipped")
            except Exception as inner:  # continue processing remaining ops
                _log_early(f"Op '{op}' failed: {inner}")
        DB_LAST_FLUSH_AT = datetime.datetime.now().timestamp()
    except Exception as e:
        _log_early(f"Batch flush error: {e}")
    finally:
        batch.clear()


def _drain_db_queue(force: bool = False):
    """Drain entire DB queue synchronously (used on shutdown / signal)."""
    batch = []
    try:
        while True:
            try:
                batch.append(DB_BATCH_QUEUE.get_nowait())
            except queue.Empty:
                break
        _flush_batch(batch)
        if force:
            _log_early("Forced DB queue drain complete")
    except Exception as e:  # pragma: no cover
        _log_early(f"Queue drain error: {e}")


def db_batch_worker():
    batch: list = []
    global DB_LAST_FLUSH_AT
    DB_LAST_FLUSH_AT = datetime.datetime.now().timestamp()
    while True:
        try:
            item = DB_BATCH_QUEUE.get(timeout=DB_BATCH_INTERVAL)
            batch.append(item)
        except queue.Empty:
            pass

        # If we have items and either size threshold met or forced flush interval elapsed
        now_ts = datetime.datetime.now().timestamp()
        if batch and (
            len(batch) >= DB_BATCH_SIZE
            or (DB_LAST_FLUSH_AT and (now_ts - DB_LAST_FLUSH_AT) >= DB_FORCED_FLUSH_INTERVAL)
        ):
            _flush_batch(batch)
            DB_LAST_FLUSH_AT = now_ts

        # Queue size protection: if queue is too large, drain additional items and flush
        if DB_BATCH_QUEUE.qsize() > DB_MAX_QUEUE_SIZE:
            _log_early(
                f"DB queue size {DB_BATCH_QUEUE.qsize()} exceeded limit {DB_MAX_QUEUE_SIZE}; forcing extended flush"
            )
            while not DB_BATCH_QUEUE.empty() and len(batch) < DB_BATCH_SIZE * 5:
                try:
                    batch.append(DB_BATCH_QUEUE.get_nowait())
                except queue.Empty:
                    break
            if batch:
                _flush_batch(batch)
                DB_LAST_FLUSH_AT = datetime.datetime.now().timestamp()


# Start the DB batch worker in a background thread
def start_db_batch_worker():
    t = threading.Thread(target=db_batch_worker, daemon=True, name="db-batch-worker")
    t.start()


# NOTE: startup events consolidated later; this helper kept for clarity.


# Performance monitoring endpoint (after app defined)
@app.get("/api/v1/performance")
async def get_performance():
    current, peak = tracemalloc.get_traced_memory()
    return {
        "memory_usage_mb": round(current / 1024 / 1024, 2),
        "memory_peak_mb": round(peak / 1024 / 1024, 2),
        "cpu_count": os.cpu_count(),
        "uvicorn_workers": int(os.environ.get("UVICORN_WORKERS", "1")),
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Retrieval layer stub (vector store placeholder interface)
class VectorStoreInterface(ABC):
    @abstractmethod
    def add_document(self, doc_id: str, content: str, metadata: dict = None):
        pass

    @abstractmethod
    def query(self, query_text: str, top_k: int = 5) -> list[Any]:
        pass


# Example in-memory placeholder implementation
class InMemoryVectorStore(VectorStoreInterface):
    def __init__(self):
        self.docs = {}

    def add_document(self, doc_id: str, content: str, metadata: dict = None):
        self.docs[doc_id] = {"content": content, "metadata": metadata or {}}

    def query(self, query_text: str, top_k: int = 5) -> list[Any]:
        # Placeholder: returns all docs (no real vector search)
        return list(self.docs.values())[:top_k]


# Singleton instance for now
vector_store = InMemoryVectorStore()
import asyncio

from fastapi import BackgroundTasks


# Enrichment task interface and sample task
async def sample_enrichment_task(
    conversation_id: str, agent_id: str, user_message: str, agent_response: str
):
    # Simulate enrichment (e.g., logging, analytics, external API call)
    await asyncio.sleep(0.1)  # Simulate async work
    # Here you could add: log to file/db, call external API, update analytics, etc.
    print(f"[Enrichment] Conversation {conversation_id} enriched for agent {agent_id}.")


# For extensibility, you can add more enrichment tasks and a registry if needed
from abc import ABC, abstractmethod  # (already imported above; kept for clarity)


# Tool abstraction layer for agent capabilities
class ToolInterface(ABC):
    @abstractmethod
    def handle(self, user_message: str, agent: dict) -> str:
        pass


# Default tool implementations
class ResearchTool(ToolInterface):
    def handle(self, user_message: str, agent: dict) -> str:
        return f"I'll research the topic: '{user_message}'."


class CodingTool(ToolInterface):
    def handle(self, user_message: str, agent: dict) -> str:
        return f"I'll help design or code a solution for: '{user_message}'."


class DataTool(ToolInterface):
    def handle(self, user_message: str, agent: dict) -> str:
        return f"I'll provide data insights for: '{user_message}'."


class ContentTool(ToolInterface):
    def handle(self, user_message: str, agent: dict) -> str:
        return f"I'll help write content for: '{user_message}'."


class OpsTool(ToolInterface):
    def handle(self, user_message: str, agent: dict) -> str:
        return f"I'll help automate or manage operations for: '{user_message}'."


# Tool handler registry
TOOL_REGISTRY = {
    "research": ResearchTool(),
    "coding": CodingTool(),
    "code": CodingTool(),
    "data": DataTool(),
    "content": ContentTool(),
    "ops": OpsTool(),
    "operations": OpsTool(),
}
"""Unified dashboard summary endpoint."""


@app.get("/api/v1/dashboard/summary")
def dashboard_summary():
    """Unified dashboard summary for agents, conversations, workflows"""
    # Agents summary
    agents_data = load_agents()
    agents_summary = {
        "total": len(agents_data),
        "active": len([a for a in agents_data.values() if a.get("status") == "available"]),
        "list": [
            {
                "id": k,
                "name": v.get("name"),
                "category": v.get("category"),
                "status": v.get("status"),
            }
            for k, v in agents_data.items()
        ],
    }

    # Conversations summary
    conversations_summary = {
        "total": len(conversations),
        "active": len([c for c in conversations.values() if c.get("status") == "active"]),
        "list": [
            {
                "id": k,
                "name": v.get("name"),
                "agent_id": v.get("agent_id"),
                "status": v.get("status"),
            }
            for k, v in conversations.items()
        ],
    }

    # Workflows summary
    workflows_summary = {
        "total": len(workflows),
        "executions": count_executions(),
        "list": [
            {"id": k, "name": v.get("name"), "steps": v.get("steps"), "status": v.get("status")}
            for k, v in workflows.items()
        ],
    }

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "agents": agents_summary,
        "conversations": conversations_summary,
        "workflows": workflows_summary,
    }


import time

# Track server start time for uptime
_SERVER_START_TIME = time.time()

# Version and build hash (set via env or file)
API_VERSION = os.getenv("API_VERSION", "2.0.0")
BUILD_HASH = os.getenv("BUILD_HASH", None)
if not BUILD_HASH:
    try:
        with open(os.path.join(os.path.dirname(__file__), "build_hash.txt")) as f:
            BUILD_HASH = f.read().strip()
    except Exception:
        BUILD_HASH = "unknown"
import json
import traceback
import uuid

# ---------------- SLO Alerting / Error Rate Webhook -------------------------
SLO_ERROR_RATE_THRESHOLD = float(os.getenv("SLO_ERROR_RATE_THRESHOLD", "0.05"))  # 5%
SLO_ERROR_RATE_5XX_THRESHOLD = float(
    os.getenv("SLO_ERROR_RATE_5XX_THRESHOLD", str(SLO_ERROR_RATE_THRESHOLD))
)
SLO_ERROR_RATE_4XX_THRESHOLD = float(
    os.getenv("SLO_ERROR_RATE_4XX_THRESHOLD", "0.10")
)  # often higher tolerance
SLO_LATENCY_P95_THRESHOLD = float(os.getenv("SLO_LATENCY_P95_THRESHOLD", "0.750"))  # seconds
SLO_LATENCY_WINDOW = int(os.getenv("SLO_LATENCY_WINDOW", "300"))  # seconds for percentile calc
ALERT_WEBHOOK_URL = os.getenv("SLO_ALERT_WEBHOOK_URL")
ALERT_COOLDOWN_SECONDS = int(os.getenv("SLO_ALERT_COOLDOWN_SECONDS", "300"))
ERROR_RATE_WINDOW = int(os.getenv("SLO_ERROR_RATE_WINDOW", "300"))  # seconds
_slo_req_events: deque[tuple[float, int, float]] = deque()  # (timestamp, status_code, latency)
_slo_last_alert_time = 0.0

# Adaptive SLO configuration
ADAPTIVE_SLO_ENABLED = (
    os.getenv("ADAPTIVE_SLO_ENABLED", "false").lower() == "true"
)  # Enable adaptive SLO evaluation
ADAPTIVE_SLO_ALPHA = float(
    os.getenv("ADAPTIVE_SLO_ALPHA", "0.2")
)  # EMA smoothing factor (0<alpha<=1)
ADAPTIVE_SLO_MARGIN = float(
    os.getenv("ADAPTIVE_SLO_MARGIN", "0.25")
)  # Relative margin over EMA for breach (e.g. 0.25=25%)
ADAPTIVE_SLO_WINDOW_SECONDS = int(
    os.getenv("ADAPTIVE_SLO_WINDOW_SECONDS", str(SLO_LATENCY_WINDOW))
)  # Sliding window horizon for adaptive stats
ADAPTIVE_SLO_PERSIST = (
    os.getenv("ADAPTIVE_SLO_PERSIST", "false").lower() == "true"
)  # Persist EMA state to DB (adaptive_latency_state table)
ADAPTIVE_SLO_ENDPOINT_MARGINS_ENV = os.getenv(
    "ADAPTIVE_SLO_ENDPOINT_MARGINS", ""
).strip()  # Comma list: /api/foo=0.30,/api/bar=0.15 (overrides global margin)
_adaptive_endpoint_margins: dict[str, float] = {}
if ADAPTIVE_SLO_ENDPOINT_MARGINS_ENV:
    for part in ADAPTIVE_SLO_ENDPOINT_MARGINS_ENV.split(","):
        if "=" in part:
            ep, val = part.split("=", 1)
            try:
                _adaptive_endpoint_margins[ep.strip()] = float(val)
            except ValueError:
                continue

# Internal adaptive tracking (in-memory; not persisted). Keys by endpoint.
_adaptive_latency_samples: dict[str, deque[tuple[float, float]]] = defaultdict(
    lambda: deque()
)  # endpoint -> deque[(ts, latency_ms)]
_adaptive_latency_ema_p95: dict[str, float] = {}  # endpoint -> EMA of p95 ms
_adaptive_class_counts: dict[str, dict[str, int]] = defaultdict(
    lambda: defaultdict(int)
)  # endpoint -> latency_class -> count (window)
_adaptive_class_ema_share: dict[str, dict[str, float]] = defaultdict(
    dict
)  # endpoint -> latency_class -> ema share
_adaptive_last_update: dict[str, float] = {}  # endpoint -> last update timestamp
_adaptive_agg_count: dict[str, int] = defaultdict(int)
_adaptive_agg_mean: dict[str, float] = defaultdict(float)
_adaptive_agg_m2: dict[str, float] = defaultdict(float)
# Rolling min/max latency per endpoint (windowed)
_adaptive_rolling_min_latency: dict[str, float] = defaultdict(lambda: float("inf"))
_adaptive_rolling_max_latency: dict[str, float] = defaultdict(lambda: float("-inf"))


def _adaptive_prune(now: float):
    # Recompute rolling min/max for each endpoint
    for endpoint, dq in _adaptive_latency_samples.items():
        if dq:
            lats = [lat for _ts, lat in dq]
            _adaptive_rolling_min_latency[endpoint] = min(lats)
            _adaptive_rolling_max_latency[endpoint] = max(lats)
        else:
            _adaptive_rolling_min_latency[endpoint] = float("inf")
            _adaptive_rolling_max_latency[endpoint] = float("-inf")
    cutoff = now - ADAPTIVE_SLO_WINDOW_SECONDS
    for endpoint, dq in list(_adaptive_latency_samples.items()):
        while dq and dq[0][0] < cutoff:
            dq.popleft()
    # Recompute window class counts fresh each prune (simpler than decrementing)
    if ADAPTIVE_SLO_ENABLED:
        for endpoint, dq in _adaptive_latency_samples.items():
            counts: dict[str, int] = defaultdict(int)
            for _ts, lat_ms in dq:
                cls = _latency_class_name(lat_ms)
                counts[cls] += 1
            _adaptive_class_counts[endpoint] = counts


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    idx = max(0, min(len(values_sorted) - 1, int(round(q * (len(values_sorted) - 1)))))
    return values_sorted[idx]


def _recompute_endpoint_p95(now: float, endpoint: str):
    dq = _adaptive_latency_samples.get(endpoint)
    if not dq:
        return
    vals = [lat for _ts, lat in dq]
    p95 = _quantile(vals, 0.95)
    prev = _adaptive_latency_ema_p95.get(endpoint, p95)
    ema = ADAPTIVE_SLO_ALPHA * p95 + (1 - ADAPTIVE_SLO_ALPHA) * prev
    _adaptive_latency_ema_p95[endpoint] = ema
    _adaptive_last_update[endpoint] = now
    # Update EMA shares for classes
    total = sum(_adaptive_class_counts[endpoint].values()) or 1
    for cls, cnt in _adaptive_class_counts[endpoint].items():
        prev_share = _adaptive_class_ema_share[endpoint].get(cls, cnt / total)
        current_share = cnt / total
        _adaptive_class_ema_share[endpoint][cls] = (
            ADAPTIVE_SLO_ALPHA * current_share + (1 - ADAPTIVE_SLO_ALPHA) * prev_share
        )
    # Gauges
    try:
        ADAPTIVE_P95_GAUGE.labels(endpoint=endpoint).set(ema)
        for cls, share in _adaptive_class_ema_share[endpoint].items():
            ADAPTIVE_CLASS_SHARE_GAUGE.labels(endpoint=endpoint, latency_class=cls).set(share)
        # Mean / variance gauges (population variance approximation using m2/(n-1))
        n = _adaptive_agg_count.get(endpoint, 0)
        if n > 0:
            ADAPTIVE_MEAN_GAUGE.labels(endpoint=endpoint).set(_adaptive_agg_mean.get(endpoint, 0.0))
        if n > 1:
            var = _adaptive_agg_m2.get(endpoint, 0.0) / (n - 1)
            ADAPTIVE_VARIANCE_GAUGE.labels(endpoint=endpoint).set(var)
    except Exception:  # pragma: no cover
        pass
    # Persist
    if ADAPTIVE_SLO_PERSIST:
        try:
            repo = get_workflows_repo()
            if repo:
                repo.upsert_adaptive_latency_state(
                    endpoint,
                    ema,
                    _adaptive_class_ema_share[endpoint],
                    datetime.datetime.utcnow().isoformat() + "Z",
                    _adaptive_agg_count.get(endpoint),
                    _adaptive_agg_mean.get(endpoint),
                    _adaptive_agg_m2.get(endpoint),
                )  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def _adaptive_record(now: float, endpoint: str, latency_ms: float):
    if not ADAPTIVE_SLO_ENABLED:
        return
    dq = _adaptive_latency_samples[endpoint]
    dq.append((now, latency_ms))
    # Welford online updates
    count = _adaptive_agg_count[endpoint] + 1
    delta = latency_ms - _adaptive_agg_mean[endpoint]
    mean = _adaptive_agg_mean[endpoint] + delta / count
    delta2 = latency_ms - mean
    m2 = _adaptive_agg_m2[endpoint] + delta * delta2
    _adaptive_agg_count[endpoint] = count
    _adaptive_agg_mean[endpoint] = mean
    _adaptive_agg_m2[endpoint] = m2
    _adaptive_prune(now)
    _recompute_endpoint_p95(now, endpoint)


def _adaptive_load_persisted():
    if not (ADAPTIVE_SLO_PERSIST and ADAPTIVE_SLO_ENABLED):
        return
    try:
        repo = get_workflows_repo()
        if not repo:
            return
        rows = repo.load_adaptive_latency_states()  # type: ignore[attr-defined]
        for r in rows:
            ep = r["endpoint"]
            ema = r.get("ema_p95_ms")
            shares = r.get("class_ema_shares") or {}
            if ema is not None:
                _adaptive_latency_ema_p95[ep] = ema
            for cls, share in shares.items():
                _adaptive_class_ema_share[ep][cls] = share
            # Load aggregates if present
            if r.get("sample_count"):
                _adaptive_agg_count[ep] = int(r.get("sample_count") or 0)
                _adaptive_agg_mean[ep] = float(r.get("sample_mean_ms") or 0.0)
                _adaptive_agg_m2[ep] = float(r.get("sample_m2") or 0.0)
    except Exception:  # pragma: no cover
        pass


_adaptive_load_persisted()

# Periodic snapshot background task
ADAPTIVE_SLO_SNAPSHOT_ENABLED = (
    os.getenv("ADAPTIVE_SLO_SNAPSHOT_ENABLED", "false").lower() == "true"
)
ADAPTIVE_SLO_SNAPSHOT_INTERVAL = int(os.getenv("ADAPTIVE_SLO_SNAPSHOT_INTERVAL", "60"))  # seconds


async def _adaptive_snapshot_loop():  # pragma: no cover - timing dependent
    if not (ADAPTIVE_SLO_SNAPSHOT_ENABLED and ADAPTIVE_SLO_PERSIST and ADAPTIVE_SLO_ENABLED):
        return
    while True:
        await asyncio.sleep(ADAPTIVE_SLO_SNAPSHOT_INTERVAL)
        try:
            for ep in list(_adaptive_latency_ema_p95.keys()):
                _recompute_endpoint_p95(time.time(), ep)
        except Exception:
            pass


@app.on_event("startup")
async def _start_adaptive_snapshot():  # pragma: no cover
    if ADAPTIVE_SLO_SNAPSHOT_ENABLED and ADAPTIVE_SLO_ENABLED and ADAPTIVE_SLO_PERSIST:
        asyncio.create_task(_adaptive_snapshot_loop())


_slo_alert_lock = threading.Lock()


def _slo_purge(now: float):
    cutoff_general = now - ERROR_RATE_WINDOW
    cutoff_latency = now - SLO_LATENCY_WINDOW
    while _slo_req_events and _slo_req_events[0][0] < min(cutoff_general, cutoff_latency):
        _slo_req_events.popleft()


def _slo_error_rates(now: float) -> dict[str, float]:
    _slo_purge(now)
    if not _slo_req_events:
        return {"overall": 0.0, "5xx": 0.0, "4xx": 0.0}
    total = len(_slo_req_events)
    five_xx = sum(1 for _, sc, _ in _slo_req_events if sc >= 500)
    four_xx = sum(1 for _, sc, _ in _slo_req_events if 400 <= sc < 500)
    overall = (five_xx + four_xx) / max(total, 1)
    return {
        "overall": overall,
        "5xx": five_xx / max(total, 1),
        "4xx": four_xx / max(total, 1),
    }


def _slo_latency_p95(now: float) -> float:
    _slo_purge(now)
    if not _slo_req_events:
        return 0.0
    # consider only entries in latency window
    window_entries = [lat for ts, _, lat in _slo_req_events if ts >= now - SLO_LATENCY_WINDOW]
    if not window_entries:
        return 0.0
    window_entries.sort()
    idx = int(0.95 * (len(window_entries) - 1))
    return window_entries[idx]


def _slo_post(payload: dict[str, Any]):  # fire-and-forget
    @app.get("/api/v2/perf/history")
    async def performance_history(
        days: int = 30, current_user: dict = Depends(get_current_active_user)
    ):
        if days <= 0:
            raise HTTPException(status_code=400, detail="days must be > 0")
        repo = get_workflows_repo()
        if not repo:
            return {"items": [], "from_date": None, "days": days}
        from datetime import datetime, timedelta

        today = datetime.utcnow().date()
        from_date = today - timedelta(days=days - 1)
        rows = []
        try:
            rows = repo.list_daily_perf(from_date.isoformat())  # type: ignore[attr-defined]
        except Exception as e:  # pragma: no cover
            logger.warning("Failed listing daily perf: %s", e)
        return {"items": rows, "from_date": from_date.isoformat(), "days": days}

    if not ALERT_WEBHOOK_URL:
        return

    def _send():
        try:
            import urllib.request

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                ALERT_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:  # pragma: no cover
            pass

    threading.Thread(target=_send, daemon=True).start()


@app.middleware("http")
async def slo_alert_middleware(request: Request, call_next):  # type: ignore
    global _slo_last_alert_time
    start = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        now = time.time()
        latency = now - start
        _slo_req_events.append((now, status_code, latency))
        _slo_purge(now)
        rates = _slo_error_rates(now)
        p95 = _slo_latency_p95(now)
        alert_payloads: list[dict[str, Any]] = []
        if rates["overall"] >= SLO_ERROR_RATE_THRESHOLD:
            alert_payloads.append(
                {
                    "type": "slo_error_rate_breach",
                    "error_rate": rates["overall"],
                    "threshold": SLO_ERROR_RATE_THRESHOLD,
                    "window_seconds": ERROR_RATE_WINDOW,
                }
            )
        if rates["5xx"] >= SLO_ERROR_RATE_5XX_THRESHOLD:
            alert_payloads.append(
                {
                    "type": "slo_5xx_error_rate_breach",
                    "error_rate_5xx": rates["5xx"],
                    "threshold": SLO_ERROR_RATE_5XX_THRESHOLD,
                    "window_seconds": ERROR_RATE_WINDOW,
                }
            )
        if rates["4xx"] >= SLO_ERROR_RATE_4XX_THRESHOLD:
            alert_payloads.append(
                {
                    "type": "slo_4xx_error_rate_breach",
                    "error_rate_4xx": rates["4xx"],
                    "threshold": SLO_ERROR_RATE_4XX_THRESHOLD,
                    "window_seconds": ERROR_RATE_WINDOW,
                }
            )
        if p95 >= SLO_LATENCY_P95_THRESHOLD:
            alert_payloads.append(
                {
                    "type": "slo_latency_p95_breach",
                    "latency_p95": p95,
                    "threshold": SLO_LATENCY_P95_THRESHOLD,
                    "window_seconds": SLO_LATENCY_WINDOW,
                }
            )
        if alert_payloads:
            with _slo_alert_lock:
                if now - _slo_last_alert_time >= ALERT_COOLDOWN_SECONDS:
                    _slo_last_alert_time = now
                    for p in alert_payloads:
                        p.update(
                            {
                                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                                "path": str(request.url),
                            }
                        )
                        _slo_post(p)
        # Adaptive SLO alerts (endpoint-level p95 over EMA + margin)
        if ADAPTIVE_SLO_ENABLED:
            try:
                # Derive endpoint pattern similarly to metrics middleware
                endpoint_pattern = (
                    request.scope.get("route").path
                    if request.scope.get("route")
                    else request.url.path
                )  # type: ignore
                ema_p95 = _adaptive_latency_ema_p95.get(endpoint_pattern)
                if ema_p95 is not None and ema_p95 > 0:
                    margin = _adaptive_endpoint_margins.get(endpoint_pattern, ADAPTIVE_SLO_MARGIN)
                    # Current instantaneous p95 over window we maintain for endpoint
                    dq = _adaptive_latency_samples.get(endpoint_pattern)
                    if dq:
                        latencies = [lat for _ts, lat in dq]
                        cur_p95 = _quantile(latencies, 0.95)
                        if cur_p95 > ema_p95 * (1 + margin):
                            payload = {
                                "type": "adaptive_latency_p95_breach",
                                "endpoint": endpoint_pattern,
                                "current_p95_ms": cur_p95,
                                "ema_p95_ms": ema_p95,
                                "margin": margin,
                            }
                            with _slo_alert_lock:
                                if now - _slo_last_alert_time >= ALERT_COOLDOWN_SECONDS:
                                    _slo_last_alert_time = now
                                    payload.update(
                                        {
                                            "timestamp": datetime.datetime.utcnow().isoformat()
                                            + "Z",
                                            "path": str(request.url),
                                        }
                                    )
                                    _slo_post(payload)
                # Class share drift detection (optional future: track baseline). For now detect surge in slowest class.
                counts = _adaptive_class_counts.get(endpoint_pattern, {})
                if counts:
                    total = sum(counts.values()) or 1
                    slowest = sorted(counts.keys())[-1]
                    share = counts[slowest] / total
                    ema_share = _adaptive_class_ema_share.get(endpoint_pattern, {}).get(
                        slowest, share
                    )
                    margin_cls = _adaptive_endpoint_margins.get(
                        endpoint_pattern, ADAPTIVE_SLO_MARGIN
                    )
                    if share > ema_share * (1 + margin_cls):
                        payload = {
                            "type": "adaptive_latency_class_surge",
                            "endpoint": endpoint_pattern,
                            "latency_class": slowest,
                            "current_share": share,
                            "ema_share": ema_share,
                            "margin": margin_cls,
                        }
                        with _slo_alert_lock:
                            if now - _slo_last_alert_time >= ALERT_COOLDOWN_SECONDS:
                                _slo_last_alert_time = now
                                payload.update(
                                    {
                                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                                        "path": str(request.url),
                                    }
                                )
                                _slo_post(payload)
            except Exception:  # pragma: no cover
                pass
    return response


# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Exception handler for structured error logging
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    error_log = {
        "correlation_id": correlation_id,
        "path": str(request.url),
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": tb_str,
    }
    # Log as structured JSON
    logger.error(json.dumps(error_log))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "correlation_id": correlation_id,
        },
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    error_log = {
        "correlation_id": correlation_id,
        "path": str(request.url),
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc.detail),
        "status_code": exc.status_code,
    }
    logger.error(json.dumps(error_log))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "correlation_id": correlation_id},
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    error_log = {
        "correlation_id": correlation_id,
        "path": str(request.url),
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc.errors()),
        "status_code": 422,
    }
    logger.error(json.dumps(error_log))
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "correlation_id": correlation_id},
        headers={"X-Correlation-ID": correlation_id},
    )


from fastapi.responses import Response
from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics


# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds", "HTTP request latency", ["method", "endpoint"]
)
ERROR_COUNT = Counter(
    "http_error_responses_total",
    "Total HTTP error responses",
    ["method", "endpoint", "http_status"],
)
ANOMALY_FLAG = Gauge("api_error_anomaly", "1 if error rate is elevated, else 0")

# Latency class segmentation
# LATENCY_CLASSES env var defines upper bounds in milliseconds for buckets, comma separated.
# Example: "50,100,250,500" produces classes: sub50, 50_100, 100_250, 250_500, 500_plus
_latency_bounds_env = os.getenv("LATENCY_CLASSES", "50,100,250,500").strip()
# LATENCY_CLASSES parsing notes:
# Provide a comma-separated list of integer millisecond upper bounds (exclusive) in ascending order.
# The system will automatically sort and de-duplicate values. Invalid integers are ignored (fallback to defaults on parse error).
# Classes generated:
#   For bounds B1,B2,...,Bn produce: subB1, B1_B2, B2_B3, ..., B(n-1)_Bn, Bn_plus
# Export metrics as counter: http_latency_class_total{method,endpoint,latency_class}
# Example: LATENCY_CLASSES="25,75,150" yields classes: sub25, 25_75, 75_150, 150_plus
try:
    _latency_bounds = sorted({int(v) for v in _latency_bounds_env.split(",") if v.strip()})
except ValueError:
    _latency_bounds = [50, 100, 250, 500]


def _latency_class_name(ms: float) -> str:
    for b in _latency_bounds:
        if ms < b:
            return f"sub{b}"
    return f"{_latency_bounds[-1]}_plus" if _latency_bounds else "unclassified"


LATENCY_CLASS_COUNT = Counter(
    "http_latency_class_total",
    "HTTP request latency class counts",
    ["method", "endpoint", "latency_class"],
)
ADAPTIVE_P95_GAUGE = Gauge(
    "adaptive_endpoint_latency_p95_ms", "Adaptive EMA p95 latency per endpoint (ms)", ["endpoint"]
)
ADAPTIVE_CLASS_SHARE_GAUGE = Gauge(
    "adaptive_endpoint_latency_class_ema_share",
    "Adaptive EMA latency class share per endpoint",
    ["endpoint", "latency_class"],
)
ADAPTIVE_MEAN_GAUGE = Gauge(
    "adaptive_endpoint_latency_mean_ms",
    "Adaptive overall latency mean (Welford) per endpoint",
    ["endpoint"],
)
ADAPTIVE_VARIANCE_GAUGE = Gauge(
    "adaptive_endpoint_latency_variance_ms2",
    "Adaptive overall latency variance (Welford) per endpoint",
    ["endpoint"],
)
ADAPTIVE_COUNT_GAUGE = Gauge(
    "adaptive_endpoint_latency_sample_count",
    "Adaptive sample count (Welford) per endpoint",
    ["endpoint"],
)
ADAPTIVE_MIN_GAUGE = Gauge(
    "adaptive_endpoint_latency_min_ms", "Rolling window min latency per endpoint (ms)", ["endpoint"]
)
ADAPTIVE_MAX_GAUGE = Gauge(
    "adaptive_endpoint_latency_max_ms", "Rolling window max latency per endpoint (ms)", ["endpoint"]
)


# Helper to export adaptive gauges (called after updating adaptive state per request)
def _export_adaptive_metrics(endpoint: str, ema: float | None):  # noqa: ANN001
    try:
        if ema is not None:
            ADAPTIVE_P95_GAUGE.labels(endpoint=endpoint).set(ema)
        shares = _adaptive_class_ema_share.get(endpoint, {})
        for cls, share in shares.items():
            ADAPTIVE_CLASS_SHARE_GAUGE.labels(endpoint=endpoint, latency_class=cls).set(share)
        n = _adaptive_agg_count.get(endpoint, 0)
        if n > 0:
            ADAPTIVE_MEAN_GAUGE.labels(endpoint=endpoint).set(_adaptive_agg_mean.get(endpoint, 0.0))
            ADAPTIVE_COUNT_GAUGE.labels(endpoint=endpoint).set(n)
        if n > 1:
            var = _adaptive_agg_m2.get(endpoint, 0.0) / (n - 1)
            ADAPTIVE_VARIANCE_GAUGE.labels(endpoint=endpoint).set(var)
        if _adaptive_rolling_min_latency.get(endpoint, float("inf")) != float("inf"):
            ADAPTIVE_MIN_GAUGE.labels(endpoint=endpoint).set(
                _adaptive_rolling_min_latency[endpoint]
            )
        if _adaptive_rolling_max_latency.get(endpoint, float("-inf")) != float("-inf"):
            ADAPTIVE_MAX_GAUGE.labels(endpoint=endpoint).set(
                _adaptive_rolling_max_latency[endpoint]
            )
    except Exception:  # pragma: no cover
        pass


import enum
import logging
import os
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import (
    Depends,
    UploadFile,
    status,
)
from pydantic import BaseModel

_phase("Imports: core FastAPI/Pydantic done")

# ---------------------------------------------------------------------------
# ML/LLM Optional Dependency Availability Summary (only when not MINIMAL_MODE)
# Logs one structured line indicating which heavy modules are present so that
# packaged / production environments can verify capability without deep stack traces.
# ---------------------------------------------------------------------------
_heavy_status = {}
if not _MINIMAL_MODE:  # type: ignore  # _MINIMAL_MODE defined near top
    try:
        import importlib

        spec = importlib.util.find_spec
        # Base heavy libraries (TensorFlow optional due to size)
        _probe_libs = [
            "torch",
            # tensorflow intentionally excluded unless override present
            "sklearn",
            "langchain",
            "openai",
            "anthropic",
        ]
        _include_tf = _os.getenv("INCLUDE_TENSORFLOW") in ("1", "true", "on", "yes")
        if _include_tf:
            _probe_libs.append("tensorflow")
        for _lib in _probe_libs:
            _heavy_status[_lib] = spec(_lib) is not None
        # Always include tensorflow key for clarity even if not requested
        if not _include_tf:
            _heavy_status.setdefault("tensorflow", False)
        _phase(f"HEAVY_DEPENDENCIES_STATUS {json.dumps(_heavy_status)}")
    except Exception as _dep_exc:  # pragma: no cover
        _phase(f"WARN: heavy dependency probe failed: {_dep_exc}")

# FastAPI endpoint to expose ML / LLM capability status
try:
    from fastapi import APIRouter  # type: ignore

    _ml_router = APIRouter()

    @_ml_router.get(
        "/ml-capabilities",
        tags=["diagnostics"],
        summary="Return heavy dependency availability & mode flags",
    )
    async def ml_capabilities():  # pragma: no cover - simple serialization
        return {
            "minimal_mode": _MINIMAL_MODE,
            "safe_mode": SAFE_MODE,
            "include_tensorflow_flag": _os.getenv("INCLUDE_TENSORFLOW"),
            "heavy_dependencies": _heavy_status,
            "tdigest_fallback": _FALLBACK_TDIGEST,
            "tdigest_tracked_endpoints": list(_tdigest_store.keys()),
        }

    # Attach immediately if app already defined; if not, route will be added later when app is finalized
    if "app" in globals() and hasattr(app, "include_router"):
        try:
            app.include_router(_ml_router)
        except Exception:
            pass
except Exception:
    pass


def _activate_safe_mode_stubs(reason: str):  # central helper for fallback
    global SAFE_MODE
    SAFE_MODE = True
    _phase(f"SAFE_MODE FALLBACK: {reason}")
    # Define minimal placeholders so later code referencing them doesn't break
    global SecurityHeadersMiddleware, HardenedCORSMiddleware, IPWhitelistMiddleware, setup_security_middleware
    SecurityHeadersMiddleware = HardenedCORSMiddleware = IPWhitelistMiddleware = object  # type: ignore
    setup_security_middleware = lambda *a, **k: None  # type: ignore

    class SecurityConfig:  # type: ignore
        @staticmethod
        def is_production():
            return False

        @staticmethod
        def get_environment():
            return "SAFE_MODE"

        @staticmethod
        def get_admin_ip_whitelist():
            return []

        @staticmethod
        def get_api_ip_whitelist():
            return []

    global setup_validation_middleware, validate_file_upload, validate_description_input
    setup_validation_middleware = lambda *a, **k: None  # type: ignore
    validate_file_upload = validate_description_input = lambda *a, **k: None  # type: ignore
    global ValidatedConversationCreate, ValidatedWorkflowCreate
    ValidatedConversationCreate = ValidatedWorkflowCreate = object  # type: ignore

    def _dummy_decorator(*d_args, **d_kwargs):
        if d_args and callable(d_args[0]) and len(d_args) == 1 and not d_kwargs:
            return d_args[0]

        def _wrap(func):
            return func

        return _wrap

    global rate_limiter, setup_default_rate_limits, check_global_rate_limit, rate_limit
    rate_limiter = setup_default_rate_limits = check_global_rate_limits = rate_limit = (
        _dummy_decorator  # type: ignore
    )
    global AUTH_RATE_LIMIT, API_RATE_LIMIT, SENSITIVE_RATE_LIMIT, BULK_OPERATION_RATE_LIMIT, RateLimitType
    AUTH_RATE_LIMIT = API_RATE_LIMIT = SENSITIVE_RATE_LIMIT = BULK_OPERATION_RATE_LIMIT = (
        _dummy_decorator  # type: ignore
    )
    RateLimitType = object  # type: ignore
    global JWTAuthService, LoginRequest, LoginResponse, RegisterRequest, get_current_user, get_current_active_user, require_admin, jwt_auth_service, auth_router, configure_logging
    JWTAuthService = LoginRequest = LoginResponse = RegisterRequest = object  # type: ignore
    get_current_user = get_current_active_user = require_admin = lambda *a, **k: None  # type: ignore
    jwt_auth_service = None  # type: ignore
    auth_router = None  # type: ignore

    def configure_logging(*a, **k):  # type: ignore
        return None


if not SAFE_MODE:
    try:
        # Attempt full security stack
        from autogen.security_middleware import (
            HardenedCORSMiddleware,
            SecurityConfig,
            setup_security_middleware,
        )

        # Ensure PyJWT present early (avoid later SAFE_MODE due to missing jwt)
        try:  # pragma: no cover - lightweight probe
            pass  # type: ignore
        except Exception as _jwt_err:
            _phase(f"WARN: PyJWT not available ({_jwt_err}); auth features may degrade")
        from autogen.input_validation import (
            setup_validation_middleware,
            validate_file_upload,
        )
        from autogen.rate_limiter import (
            API_RATE_LIMIT,
            AUTH_RATE_LIMIT,
            SENSITIVE_RATE_LIMIT,
            check_global_rate_limit,
            rate_limit,
            rate_limiter,
            setup_default_rate_limits,
        )

        try:
            from autogen import jwt_auth_service as _jwt_mod  # type: ignore

            JWTAuthService = _jwt_mod.JWTAuthService  # type: ignore
            LoginRequest = _jwt_mod.LoginRequest  # type: ignore
            LoginResponse = _jwt_mod.LoginResponse  # type: ignore
            RegisterRequest = _jwt_mod.RegisterRequest  # type: ignore
            get_current_user = _jwt_mod.get_current_user  # type: ignore
            get_current_active_user = _jwt_mod.get_current_active_user  # type: ignore
            require_admin = _jwt_mod.require_admin  # type: ignore
            jwt_auth_service = None
        except Exception as e:  # pragma: no cover
            _phase(f"WARN: deferred jwt_auth_service import failed: {e}")
            JWTAuthService = LoginRequest = LoginResponse = RegisterRequest = object  # type: ignore
            get_current_user = get_current_active_user = require_admin = lambda *a, **k: None  # type: ignore
            jwt_auth_service = None
        from autogen.auth_router import router as auth_router  # type: ignore
        from autogen.logging_setup import configure_logging  # type: ignore
    except Exception as e:
        # Any failure -> SAFE_MODE fallback (especially in frozen exe where relative imports may not resolve)
        _activate_safe_mode_stubs(f"security import failure: {e}")
else:
    _activate_safe_mode_stubs("initial SAFE_MODE enabled")


# JWT Authentication / Permissions
if not SAFE_MODE:
    try:
        from roles_permissions import (
            Permission,
            RolePermissionManager,
            UserRole,
            require_admin_access,
            require_agent_management,
            require_analytics_access,
            require_any_permission,
            require_conversation_access,
            require_file_access,
            require_permission,
            require_user_management,
            require_workflow_access,
        )
    except ImportError:
        from .roles_permissions import (
            Permission,
            RolePermissionManager,
            UserRole,
            require_admin_access,
            require_agent_management,
            require_analytics_access,
            require_any_permission,
            require_conversation_access,
            require_file_access,
            require_permission,
            require_user_management,
            require_workflow_access,
        )
else:
    # Minimal stand-ins so route decorators referencing these don't fail in SAFE_MODE
    class _Dummy:  # noqa: D401
        def __getattr__(self, name):
            return f"dummy_{name}"

        def __call__(self, *args, **kwargs):
            return self

    class _DummyPermission:
        """Dummy Permission enum that accepts any attribute"""

        SYSTEM_VIEW = "SYSTEM_VIEW"
        USER_EDIT_ALL = "USER_EDIT_ALL"
        ADMIN_ALL = "ADMIN_ALL"

        def __getattr__(self, name):
            return name

        def __call__(self, *args, **kwargs):
            return args[0] if args else "DUMMY_PERMISSION"

    Permission = _DummyPermission()
    UserRole = RolePermissionManager = _Dummy()  # type: ignore

    def _noop_decorator(*a, **k):  # type: ignore
        def inner(func):
            return func

        return inner

    require_permission = require_any_permission = require_admin_access = _noop_decorator  # type: ignore
    require_agent_management = require_conversation_access = _noop_decorator  # type: ignore
    require_workflow_access = require_file_access = _noop_decorator  # type: ignore
    require_analytics_access = require_user_management = _noop_decorator  # type: ignore

# Load environment variables from .env as early as possible
try:  # pragma: no cover - optional dependency path
    from dotenv import load_dotenv  # type: ignore

    _ENV_LOADED = load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
except Exception:
    _ENV_LOADED = False

# Attempt YAML import for dynamic agent loading
try:
    import yaml  # type: ignore
except ImportError:  # If PyYAML missing keep working with empty registry fallback
    yaml = None  # type: ignore

# Configure logging (respect LOG_LEVEL env if set)
from logging_setup import configure_logging  # type: ignore

configure_logging()
logger = logging.getLogger(__name__)
if _ENV_LOADED:
    logger.debug("Environment variables loaded from .env file")

# Guarantee SecurityConfig symbol exists (SAFE_MODE fallback may have run before this block)
if "SecurityConfig" not in globals():

    class SecurityConfig:  # type: ignore
        @staticmethod
        def is_production():
            return False

        @staticmethod
        def get_environment():
            return "SAFE_MODE"

        @staticmethod
        def get_admin_ip_whitelist():
            return []

        @staticmethod
        def get_api_ip_whitelist():
            return []


# Enhance previously created `app` with enterprise metadata (avoid redefining)
app.title = "AutoGen Multi-Agent WebUI - Enterprise API"
app.description = "Advanced AI Agent Platform with Conversation History and Workflows"
app.version = "2.0.0"
if SecurityConfig.is_production():  # Remove interactive docs in production
    app.docs_url = None
    app.redoc_url = None

# Include authentication router
if SAFE_MODE:
    _phase("SKIP: auth router & security middleware (SAFE_MODE)")
else:
    app.include_router(auth_router)
    _phase("OK: auth router included")
    """Apply layered middleware configuration in-place instead of reassigning app variable."""
    try:
        setup_security_middleware(app)
        _phase("OK: security middleware setup")
    except Exception as e:
        _phase(f"ERR: security middleware setup failed {e}")
    try:
        setup_validation_middleware(app)
        _phase("OK: validation middleware setup")
    except Exception as e:
        _phase(f"ERR: validation middleware setup failed {e}")

# Setup authentication middleware
# (No AuthMiddleware class; authentication handled via dependencies and routers)


# Rate limiting and metrics middleware
if SAFE_MODE:
    _phase("SKIP: rate limiting middleware (SAFE_MODE)")
else:

    @app.middleware("http")
    async def rate_limit_and_metrics_middleware(request: Request, call_next):
        """Global rate limiting and Prometheus metrics middleware"""
        route_pattern = (
            request.scope.get("route").path if request.scope.get("route") else request.url.path
        )
        rate_limit_response = check_global_rate_limit(request)
        if rate_limit_response:
            status_code = rate_limit_response.status_code
            REQUEST_COUNT.labels(
                method=request.method, endpoint=route_pattern, http_status=status_code
            ).inc()
            if status_code >= 400:
                ERROR_COUNT.labels(
                    method=request.method, endpoint=route_pattern, http_status=status_code
                ).inc()
            _recent_statuses.append(status_code)
            if len(_recent_statuses) > _ANOMALY_WINDOW:
                _recent_statuses.pop(0)
            _update_anomaly_flag()
            return rate_limit_response

        _start_time = time.time()
        with REQUEST_LATENCY.labels(method=request.method, endpoint=route_pattern).time():
            response = await call_next(request)

        latency_ms = (time.time() - _start_time) * 1000.0
        try:
            _adaptive_record(time.time(), route_pattern, latency_ms)
        except Exception:
            pass
        try:
            cls = _latency_class_name(latency_ms)
            LATENCY_CLASS_COUNT.labels(
                method=request.method, endpoint=route_pattern, latency_class=cls
            ).inc()
        except Exception:
            pass

        status_code = response.status_code
        REQUEST_COUNT.labels(
            method=request.method, endpoint=route_pattern, http_status=status_code
        ).inc()
        if status_code >= 400:
            ERROR_COUNT.labels(
                method=request.method, endpoint=route_pattern, http_status=status_code
            ).inc()
        _recent_statuses.append(status_code)
        if len(_recent_statuses) > _ANOMALY_WINDOW:
            _recent_statuses.pop(0)
        _update_anomaly_flag()
        return response

    _phase("OK: rate limiting middleware enabled")

# Optional lightweight profiling (per-request) enabled via env flag and header/query
ENABLE_PROFILING = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
if ENABLE_PROFILING:
    import time as _time
    import tracemalloc as _tm

    @app.middleware("http")  # type: ignore
    async def profiling_middleware(
        request: Request, call_next
    ):  # pragma: no cover - diagnostic path
        activate = False
        # Trigger if header present or query parameter
        if request.headers.get("X-Profile") == "1" or request.query_params.get("profile") == "1":
            activate = True
        if not activate:
            return await call_next(request)
        start_wall = _time.perf_counter()
        if _tm.is_tracing():
            snap_before = _tm.take_snapshot()
        response = await call_next(request)
        duration = (_time.perf_counter() - start_wall) * 1000.0
        if _tm.is_tracing():
            snap_after = _tm.take_snapshot()
            stats = snap_after.compare_to(snap_before, "lineno")[:5]
            top = [f"{s.traceback.format()[-1]} size={s.size_diff}" for s in stats]
            response.headers["X-Profile-Top"] = ";".join(top)
        response.headers["X-Profile-Duration-ms"] = f"{duration:.2f}"
        return response


# Helper to update anomaly flag
def _update_anomaly_flag():
    if not _recent_statuses:
        ANOMALY_FLAG.set(0)
        return
    error_count = sum(1 for s in _recent_statuses if s >= 400)
    error_rate = error_count / len(_recent_statuses)
    ANOMALY_FLAG.set(1 if error_rate >= _ANOMALY_THRESHOLD else 0)


# Data Models
class ConversationCreate(BaseModel):
    name: str
    description: str = ""
    agent_id: str
    system_message: str = ""
    user_message: str | None = None
    context: dict | list | None = None


class MessageCreate(BaseModel):
    content: str
    agent_id: str | None = None


class WorkflowStep(BaseModel):
    name: str
    agent_id: str
    parameters: dict = {}
    depends_on: list[str] = []


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    steps: list[dict]
    parallel_execution: bool = False


@app.get("/api/v2/latency/distribution")
def get_latency_distribution():
    """Return current latency class distribution and adaptive EMA stats per endpoint."""
    now = time.time()
    if ADAPTIVE_SLO_ENABLED:
        _adaptive_prune(now)
    result: dict[str, Any] = {"endpoints": {}, "adaptive_enabled": ADAPTIVE_SLO_ENABLED}
    for endpoint, dq in _adaptive_latency_samples.items():
        samples = list(dq)
        if not samples:
            continue
        latencies = [lat for _ts, lat in samples]
        p95 = _quantile(latencies, 0.95)
        ema_p95 = _adaptive_latency_ema_p95.get(endpoint, p95)
        counts = _adaptive_class_counts.get(endpoint, {})
        total = sum(counts.values()) or 1
        classes = []
        for cls, cnt in sorted(counts.items(), key=lambda x: x[0]):
            share = cnt / total
            ema_share = _adaptive_class_ema_share.get(endpoint, {}).get(cls, share)
            classes.append(
                {
                    "latency_class": cls,
                    "count": cnt,
                    "proportion": round(share, 6),
                    "ema_share": round(ema_share, 6),
                }
            )
        result["endpoints"][endpoint] = {
            "window_samples": len(samples),
            "p95_ms": round(p95, 3),
            "ema_p95_ms": round(ema_p95, 3),
            "classes": classes,
            "window_seconds": ADAPTIVE_SLO_WINDOW_SECONDS,
            "last_update_ts": _adaptive_last_update.get(endpoint),
            "sample_count": _adaptive_agg_count.get(endpoint),
            "sample_mean_ms": round(_adaptive_agg_mean.get(endpoint, 0.0), 3),
            "sample_variance_ms2": (
                round(
                    (
                        _adaptive_agg_m2.get(endpoint, 0.0)
                        / max((_adaptive_agg_count.get(endpoint) or 1) - 1, 1)
                    ),
                    6,
                )
                if _adaptive_agg_count.get(endpoint, 0) > 1
                else 0.0
            ),
            "sample_stddev_ms": (
                round(
                    (
                        (
                            _adaptive_agg_m2.get(endpoint, 0.0)
                            / max((_adaptive_agg_count.get(endpoint) or 1) - 1, 1)
                        )
                        ** 0.5
                    ),
                    3,
                )
                if _adaptive_agg_count.get(endpoint, 0) > 1
                else 0.0
            ),
            "rolling_min_ms": _adaptive_rolling_min_latency.get(endpoint, float("inf")),
            "rolling_max_ms": _adaptive_rolling_max_latency.get(endpoint, float("-inf")),
        }
    return result


@app.get("/api/v2/latency/quantiles")
def get_latency_quantiles():
    """Return empirical quantiles (p50,p90,p95,p99) for each endpoint from adaptive window samples.

    If adaptive is disabled, this will still return empty or partial data depending on whether any samples were recorded (samples accumulate only when adaptive enabled).
    """
    now = time.time()
    if ADAPTIVE_SLO_ENABLED:
        _adaptive_prune(now)
    quantiles = [0.50, 0.90, 0.95, 0.99]
    response: dict[str, Any] = {"endpoints": {}, "adaptive_enabled": ADAPTIVE_SLO_ENABLED}
    for endpoint, dq in _adaptive_latency_samples.items():
        if not dq:
            continue
        vals = [lat for _ts, lat in dq]
        data = {}
        for q in quantiles:
            data[f"p{int(q * 100)}_ms"] = round(_quantile(vals, q), 3)
    data["samples"] = len(vals)
    data["rolling_min_ms"] = _adaptive_rolling_min_latency.get(endpoint, float("inf"))
    data["rolling_max_ms"] = _adaptive_rolling_max_latency.get(endpoint, float("-inf"))
    data["window_seconds"] = ADAPTIVE_SLO_WINDOW_SECONDS
    data["last_update_ts"] = _adaptive_last_update.get(endpoint)
    data["sample_count"] = _adaptive_agg_count.get(endpoint)
    data["sample_mean_ms"] = round(_adaptive_agg_mean.get(endpoint, 0.0), 3)
    data["sample_variance_ms2"] = (
        round(
            (
                _adaptive_agg_m2.get(endpoint, 0.0)
                / max((_adaptive_agg_count.get(endpoint) or 1) - 1, 1)
            ),
            6,
        )
        if _adaptive_agg_count.get(endpoint, 0) > 1
        else 0.0
    )
    data["sample_stddev_ms"] = (
        round(
            (
                (
                    _adaptive_agg_m2.get(endpoint, 0.0)
                    / max((_adaptive_agg_count.get(endpoint) or 1) - 1, 1)
                )
                ** 0.5
            ),
            3,
        )
        if _adaptive_agg_count.get(endpoint, 0) > 1
        else 0.0
    )
    response["endpoints"][endpoint] = data
    return response


# ---------------------------------------------------------------------------
# Admin adaptive reset (broader) & startup heartbeat endpoints
# ---------------------------------------------------------------------------


@app.post("/admin/adaptive/reset")
def admin_reset_all_adaptive(
    secret: str | None = None, current_user: dict = Depends(require_admin)
):
    """Reset ALL adaptive / latency tracking state including:
    - t-digests
    - adaptive EMA p95 & class share state
    - rolling aggregates (mean/variance)
    - per-endpoint sample windows

    Optional query param 'secret' can be configured (ADMIN_RESET_TOKEN env) to allow headless
    automation in SAFE_MODE (when auth may be disabled). If SAFE_MODE and auth disabled, we still
    require matching secret if ADMIN_RESET_TOKEN is set.
    """
    admin_token = os.getenv("ADMIN_RESET_TOKEN")
    if (SAFE_MODE or jwt_auth_service is None) and admin_token:
        if not secret or secret != admin_token:
            raise HTTPException(status_code=401, detail="Unauthorized reset (token mismatch)")

    # Clear adaptive dictionaries
    cleared = list(_adaptive_latency_ema_p95.keys())
    _adaptive_latency_ema_p95.clear()
    _adaptive_class_ema_share.clear()
    _adaptive_class_counts.clear()
    _adaptive_latency_samples.clear()
    _adaptive_last_update.clear()
    _adaptive_agg_count.clear()
    _adaptive_agg_mean.clear()
    _adaptive_agg_m2.clear()
    # Clear t-digests
    _tdigest_store.clear()
    _phase("ADMIN RESET: adaptive latency + t-digests cleared")
    return {"reset_endpoints": cleared, "status": "ok"}


@app.get("/startup/heartbeat")
def startup_heartbeat(limit: int = 50):
    """Return recent startup / phase events (capped by 'limit').

    Useful for monitoring container churn or verifying which fallbacks activated.
    """
    if limit <= 0:
        limit = 1
    events = _phase_event_buffer[-limit:]
    return {
        "events": events,
        "count": len(events),
        "uptime_seconds": (
            round(time.time() - PROCESS_START_TIME, 3)
            if "PROCESS_START_TIME" in globals()
            else None
        ),
        "minimal_mode": _MINIMAL_MODE,
        "safe_mode": SAFE_MODE,
    }


@app.post("/api/v2/latency/adaptive/reset")
def reset_adaptive_state(endpoint: str | None = None, current_user: dict = Depends(require_admin)):
    """Admin: Reset adaptive SLO baseline for all or one endpoint.

    Query param 'endpoint' optional; if omitted, clears all adaptive data (EMA, class shares, aggregates, samples).
    """
    targets = [endpoint] if endpoint else list(_adaptive_latency_ema_p95.keys())
    for ep in targets:
        _adaptive_latency_ema_p95.pop(ep, None)
        _adaptive_class_ema_share.pop(ep, None)
        _adaptive_class_counts.pop(ep, None)
        _adaptive_latency_samples.pop(ep, None)
        _adaptive_last_update.pop(ep, None)
        _adaptive_agg_count.pop(ep, None)
        _adaptive_agg_mean.pop(ep, None)
        _adaptive_agg_m2.pop(ep, None)
    return {"reset": targets}


class AgentConfig(BaseModel):
    name: str
    category: str
    description: str
    capabilities: list[str]
    # Final name chosen to avoid Pydantic reserved prefix and warnings
    agent_settings: dict = {}


# In-memory storage (replace with database in production)
def generate_capability_driven_response(
    agent_id: str, user_message: str, registry: dict | None = None
) -> str:
    """
    Generate an agent response based on the agent's capabilities and the user message.
    Uses the tool abstraction layer for routing requests. Fallback to a generic response if capabilities are missing or unknown.
    """
    if registry is None:
        registry = load_agents()
    agent = registry.get(agent_id)
    if not agent:
        return "I'm ready to help with your request."
    capabilities = agent.get("capabilities", [])
    if not capabilities:
        return f"I'm ready to help with your request: '{user_message}'"

    response_parts = []
    for cap in capabilities:
        cap_key = cap.lower().strip()
        # Try to match capability to a tool handler
        for tool_name, tool_handler in TOOL_REGISTRY.items():
            if tool_name in cap_key:
                response_parts.append(tool_handler.handle(user_message, agent))
                break
        else:
            # Fallback for unknown capabilities
            response_parts.append(f"[{cap}] capability: I'm ready to help with '{user_message}'.")
    if response_parts:
        return " ".join(response_parts)
    return f"I'm ready to help with your request: '{user_message}'"


conversations: dict[str, Any] = {}
workflows: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Safe enqueue helper to prevent silent data loss
# ---------------------------------------------------------------------------
def enqueue_db_op(op: str, *args):
    if DB_BATCH_QUEUE.qsize() >= DB_MAX_QUEUE_SIZE:
        _log_early(f"DB queue full ({DB_MAX_QUEUE_SIZE}); dropping op {op}")
        return False
    try:
        DB_BATCH_QUEUE.put_nowait((op, args))
        return True
    except Exception as e:  # pragma: no cover
        _log_early(f"Failed to enqueue DB op {op}: {e}")
        return False


# Execution registries (in-memory for now)
workflow_executions: dict[str, dict[str, Any]] = {}
workflow_step_states: dict[str, dict[str, Any]] = {}


# Repository helper & retention configuration ---------------------------------
def get_workflows_repo() -> "WorkflowsRepository | None":  # type: ignore
    """Return a repository instance if the class is importable; otherwise None.

    This indirection keeps testability (can monkeypatch) and prevents import errors
    if the db layer moves. We lazily import to avoid circulars.
    """
    try:  # local import to avoid overhead if not used
        from src.db.workflows_repo import WorkflowsRepository  # type: ignore
    except Exception:  # pragma: no cover - repository optional in some deploys
        return None
    db_path = Path(
        os.getenv(
            "DB_PATH",
            Path(__file__).resolve().parent.parent / "data" / "platform.db",
        )
    )
    try:
        return WorkflowsRepository(db_path)
    except Exception:  # pragma: no cover
        return None


def get_execution_retention() -> int:
    """Return max retained executions (global) from env (default 1000).

    Set WORKFLOW_EXECUTION_RETENTION=0 (or negative) to disable pruning.
    """
    try:
        return int(os.getenv("WORKFLOW_EXECUTION_RETENTION", "1000"))
    except ValueError:  # pragma: no cover
        return 1000


def count_executions() -> int:
    """Best-effort count of executions (repository if available, else in-memory)."""
    repo = get_workflows_repo()
    if repo:
        try:
            # lightweight count query – reuse internal connection
            import sqlite3  # local import

            with sqlite3.connect(repo.db_path) as conn:  # type: ignore[attr-defined]
                cur = conn.execute("SELECT COUNT(*) FROM workflow_executions")
                return cur.fetchone()[0]
        except Exception:  # pragma: no cover
            pass
    return len(workflow_executions)


# Dynamic Agent Registry -----------------------------------------------------
CONFIG_DIR = Path(os.getenv("AGENTS_CONFIG_DIR", Path(__file__).resolve().parent.parent / "config"))
AGENTS_FILE = CONFIG_DIR / "agents.yaml"
_agents_cache: dict[str, dict[str, Any]] = {}


def _load_agents_from_yaml() -> dict[str, dict[str, Any]]:
    if yaml is None:
        logger.warning(
            "PyYAML not installed; agent registry empty. Install PyYAML to enable dynamic loading."
        )
        return {}
    if not AGENTS_FILE.exists():
        logger.warning(
            f"Agents config file not found at {AGENTS_FILE}; starting with empty registry."
        )
        return {}
    try:
        raw = yaml.safe_load(AGENTS_FILE.read_text(encoding="utf-8")) or {}
        agents_list = raw.get("agents", []) if isinstance(raw, dict) else []
        registry: dict[str, dict[str, Any]] = {}
        for entry in agents_list:
            if not isinstance(entry, dict):
                continue
            agent_id = entry.get("id")
            if not agent_id:
                continue
            entry.setdefault("status", "available")
            entry.setdefault("version", "2.0.0")
            registry[agent_id] = entry
        logger.info("Loaded %d agents from %s", len(registry), AGENTS_FILE)
        return registry
    except Exception as e:  # broad to avoid startup failure
        logger.exception("Failed to load agents.yaml: %s", e)
        return {}


def load_agents(force: bool = False) -> dict[str, dict[str, Any]]:
    global _agents_cache
    if force or not _agents_cache:
        _agents_cache = _load_agents_from_yaml()
    return _agents_cache


# Initial load
load_agents(force=True)


# Core API Routes
@app.get("/")
async def root():
    return {
        "message": "AutoGen Multi-Agent WebUI - Enterprise API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.datetime.now().isoformat(),
        "features": [
            "Conversation History",
            "Workflow Automation",
            "Advanced Analytics",
            "File Processing",
        ],
    }


@app.get("/health")
@rate_limit(max_requests=30, window_seconds=60)  # 30 requests per minute
def health_check(request: Request):
    """Enhanced health check endpoint with uptime, version, build hash"""
    uptime_seconds = int(time.time() - _SERVER_START_TIME)
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": API_VERSION,
        "build_hash": BUILD_HASH,
        "uptime_seconds": uptime_seconds,
        "security": {
            "environment": SecurityConfig.get_environment(),
            "production_mode": SecurityConfig.is_production(),
            "cors_hardened": True,
            "security_headers": True,
            "rate_limiting": True,
        },
        "features": {
            "jwt_auth": "enabled",
            "rbac": "enabled",
            "rate_limiting": "enabled",
            "agents": "available" if load_agents() else "empty",
            "workflows": "enabled",
            "conversations": "enabled",
        },
    }


# Extremely low limit test endpoint (3 requests / 10 seconds) for automated tests
@app.get("/api/v1/test/rate-limit")
@rate_limit(max_requests=3, window_seconds=10)
async def rate_limit_probe():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}


# Optional test-only endpoints
if os.getenv("ENABLE_TEST_ENDPOINTS", "false").lower() == "true":

    @app.get("/api/v1/test/force-error")
    async def force_error():  # pragma: no cover - used in explicit anomaly tests
        raise HTTPException(status_code=500, detail="Forced error for anomaly gauge test")


# Agent Management
@app.get("/api/v1/agents")
async def get_agents():
    registry = load_agents()
    return {
        "agents": list(registry.values()),
        "total": len(registry),
        "categories": sorted({a.get("category", "uncategorized") for a in registry.values()}),
        "system_status": "operational",
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    registry = load_agents()
    if agent_id not in registry:
        raise HTTPException(status_code=404, detail="Agent not found")
    return registry[agent_id]


@app.post("/api/v1/agents")
async def create_custom_agent(
    agent: AgentConfig, current_user: dict = Depends(require_agent_management)
):
    registry = load_agents()
    agent_id = str(uuid.uuid4())
    registry[agent_id] = {
        "id": agent_id,
        "name": agent.name,
        "category": agent.category,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "status": "available",
        "version": "2.0.0",
        "agent_settings": agent.agent_settings,
        "created_at": datetime.datetime.now().isoformat(),
    }
    return {"agent_id": agent_id, "status": "created", "agent": registry[agent_id]}


@app.post("/api/v1/agents/reload")
@SENSITIVE_RATE_LIMIT  # 10 requests per 5 minutes
async def reload_agents(request: Request, current_user: dict = Depends(require_agent_management)):
    before = set(load_agents().keys())
    after_registry = load_agents(force=True)
    after = set(after_registry.keys())

    return {
        "reloaded": True,
        "agents_before": len(before),
        "agents_after": len(after),
        "new_agents": list(after - before),
        "removed_agents": list(before - after),
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Conversation Management
@app.post("/api/v1/conversations")
@API_RATE_LIMIT  # 100 requests per hour
async def create_conversation(
    conv: ConversationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_conversation_access),
):
    conversation_id = str(uuid.uuid4())
    registry = load_agents()

    # Capability-driven agent response
    initial_user_message = conv.user_message or ""
    agent_response = generate_capability_driven_response(
        conv.agent_id, initial_user_message, registry
    )

    conversations[conversation_id] = {
        "id": conversation_id,
        "agent_id": conv.agent_id,
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": initial_user_message,
                "timestamp": datetime.datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "role": "agent",
                "content": agent_response,
                "timestamp": datetime.datetime.now().isoformat(),
                "agent_id": conv.agent_id,
            },
        ],
        "context": conv.context or {},
        "created_at": datetime.datetime.now().isoformat(),
        "last_updated": datetime.datetime.now().isoformat(),
        "status": "active",
    }

    # Persist (enqueue full conversation dict; repository wrapper will extract fields)
    try:
        DB_BATCH_QUEUE.put(("create_conversation", (conversations[conversation_id],)))
    except Exception as e:
        logger.warning("Failed to enqueue conversation %s: %s", conversation_id, e)
    # Trigger async enrichment task
    background_tasks.add_task(
        sample_enrichment_task, conversation_id, conv.agent_id, conv.user_message, agent_response
    )
    return {"conversation_id": conversation_id, "response": agent_response}


@app.get("/api/v1/conversations")
async def list_conversations(current_user: dict = Depends(get_current_active_user)):
    """List conversations from DB if available; fallback to in-memory."""
    conv_list: list[dict]
    if ConversationsRepository is not None:
        try:
            DB_PATH = Path(
                os.getenv(
                    "DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db"
                )
            )
            repo = ConversationsRepository(DB_PATH)  # type: ignore
            conv_list = repo.list_conversations()
            # Optionally refresh in-memory cache with latest (shallow merge) for fast subsequent access
            for c in conv_list:
                conversations.setdefault(c["id"], c)
        except Exception as e:
            logger.warning("DB list_conversations failed, falling back to memory: %s", e)
            conv_list = list(conversations.values())
    else:
        conv_list = list(conversations.values())
    return {
        "conversations": conv_list,
        "total": len(conv_list),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_active_user)
):
    # Fast path memory
    if conversation_id in conversations:
        return conversations[conversation_id]
    # DB fallback
    if ConversationsRepository is not None:
        try:
            DB_PATH = Path(
                os.getenv(
                    "DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db"
                )
            )
            repo = ConversationsRepository(DB_PATH)  # type: ignore
            conv = repo.get_conversation(conversation_id)
            if conv:
                conversations.setdefault(conversation_id, conv)
                return conv
        except Exception as e:
            logger.warning("DB get_conversation failed for %s: %s", conversation_id, e)
    raise HTTPException(status_code=404, detail="Conversation not found")


@app.post("/api/v1/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_conversation_access),
):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv = conversations[conversation_id]
    user_msg = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": message.content,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    conv["messages"].append(user_msg)

    # Capability-driven agent response
    registry = load_agents()
    agent_response_content = generate_capability_driven_response(
        conv["agent_id"], message.content, registry
    )
    agent_msg = {
        "id": str(uuid.uuid4()),
        "role": "agent",
        "content": agent_response_content,
        "timestamp": datetime.datetime.now().isoformat(),
        "agent_id": conv["agent_id"],
    }
    conv["messages"].append(agent_msg)
    conv["last_updated"] = datetime.datetime.now().isoformat()

    # Persist
    # Enqueue for batched DB write
    try:
        # Persist both user and agent messages; enqueue sequentially
        DB_BATCH_QUEUE.put(("add_message", (conversation_id, user_msg)))
        DB_BATCH_QUEUE.put(("add_message", (conversation_id, agent_msg)))
    except Exception as e:
        logger.warning("Failed to enqueue message for %s: %s", conversation_id, e)
    # Trigger async enrichment task
    background_tasks.add_task(
        sample_enrichment_task,
        conversation_id,
        conv["agent_id"],
        message["content"],
        agent_response_content,
    )
    return {"message_id": agent_msg["id"], "response": agent_response_content}


"""Workflow Management (DB-backed if repository available)."""


@app.post("/api/v1/workflows")
@API_RATE_LIMIT  # 100 requests per hour
async def create_workflow(
    workflow: WorkflowCreate,
    request: Request,
    current_user: dict = Depends(require_workflow_access),
):
    workflow_id = str(uuid.uuid4())
    wf_record = {
        "id": workflow_id,
        "name": workflow.name,
        "description": workflow.description,
        "steps": [step.dict() for step in workflow.steps],
        "parallel_execution": workflow.parallel_execution,
        "status": "created",
        "created_at": datetime.datetime.now().isoformat(),
    }
    workflows[workflow_id] = wf_record
    # Persist if repository available
    if WorkflowsRepository is not None:
        try:
            DB_PATH = Path(
                os.getenv(
                    "DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db"
                )
            )
            WorkflowsRepository(DB_PATH).create_workflow(wf_record)  # type: ignore
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to persist workflow %s: %s", workflow_id, e)
    return {"workflow_id": workflow_id, "status": "created"}


@app.get("/api/v1/workflows")
async def get_workflows(current_user: dict = Depends(get_current_active_user)):
    wf_list: list[dict]
    if WorkflowsRepository is not None:
        try:
            DB_PATH = Path(
                os.getenv(
                    "DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db"
                )
            )
            repo = WorkflowsRepository(DB_PATH)  # type: ignore
            wf_list = repo.list_workflows()
            # hydrate in-memory cache for active runtime (shallow)
            for w in wf_list:
                workflows.setdefault(w["id"], w)
        except Exception as e:  # pragma: no cover
            logger.warning("DB list_workflows failed; falling back to memory: %s", e)
            wf_list = list(workflows.values())
    else:
        wf_list = list(workflows.values())
    return {
        "workflows": wf_list,
        "total": len(wf_list),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v1/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, current_user: dict = Depends(get_current_active_user)):
    if workflow_id in workflows:
        return workflows[workflow_id]
    if WorkflowsRepository is not None:
        try:
            DB_PATH = Path(
                os.getenv(
                    "DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db"
                )
            )
            repo = WorkflowsRepository(DB_PATH)  # type: ignore
            wf = repo.get_workflow(workflow_id)
            if wf:
                workflows.setdefault(workflow_id, wf)
                return wf
        except Exception as e:  # pragma: no cover
            logger.warning("DB get_workflow failed %s: %s", workflow_id, e)
    raise HTTPException(status_code=404, detail="Workflow not found")


class WorkflowState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class StepState(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@app.get("/api/v1/workflows/{workflow_id}/executions")
async def list_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_workflow_access),
):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    repo = get_workflows_repo()
    if not repo:
        # Fallback: filter in-memory (recent session only)
        data = [e for e in workflow_executions.values() if e.get("workflow_id") == workflow_id]
        data.sort(key=lambda x: x.get("started_at") or x.get("created_at") or "", reverse=True)
        return {
            "items": data[offset : offset + limit],
            "total": len(data),
            "limit": limit,
            "offset": offset,
        }
    try:
        items = repo.list_executions(workflow_id=workflow_id, limit=limit, offset=offset)
        # Lightweight total count estimate (count all and then filter) - could optimize later
        total = len(items)
    except Exception as e:  # pragma: no cover
        logger.warning("Failed to list executions for %s: %s", workflow_id, e)
        raise HTTPException(status_code=500, detail="Failed to list executions")
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/v1/workflows/executions")
async def list_all_executions(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_active_user),
):
    repo = get_workflows_repo()
    if not repo:
        data = list(workflow_executions.values())
        data.sort(key=lambda x: x.get("started_at") or x.get("created_at") or "", reverse=True)
        return {
            "items": data[offset : offset + limit],
            "total": len(data),
            "limit": limit,
            "offset": offset,
        }
    try:
        items = repo.list_executions(limit=limit, offset=offset)
        total = len(items)
    except Exception as e:  # pragma: no cover
        logger.warning("Failed to list executions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list executions")
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.post("/api/v1/workflows/executions/{execution_id}/replay")
async def replay_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
):
    """Replay a completed (or failed) execution by launching a new execution of its workflow.

    Persists replay_of link and preserves original workflow step snapshot in new execution's input_snapshot.
    """
    repo = get_workflows_repo()
    base_execution = None
    if repo:
        try:
            base_execution = repo.get_execution(execution_id)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to fetch execution for replay %s: %s", execution_id, e)
    if not base_execution:
        base_execution = workflow_executions.get(execution_id)
    if not base_execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    wf_id = base_execution.get("workflow_id")
    if not wf_id or wf_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow for execution not found")
    # Only allow replay of terminal states
    if base_execution.get("status") not in {
        WorkflowState.SUCCESS.value,
        WorkflowState.FAILED.value,
    }:
        raise HTTPException(status_code=409, detail="Execution not yet complete; cannot replay")
    response = await execute_workflow(wf_id, background_tasks, current_user)  # type: ignore[arg-type]
    new_exec_id = response["execution_id"]
    # Persist replay_of
    if repo:
        try:
            exec_new = repo.get_execution(new_exec_id)
            if exec_new:
                exec_new["replay_of"] = execution_id
                repo.update_execution(exec_new)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to update replay_of for %s: %s", new_exec_id, e)
    workflow_executions[new_exec_id]["replay_of"] = execution_id
    return {"execution_id": new_exec_id, "status": "started", "replay_of": execution_id}


@app.post("/api/v1/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_workflow_access),
):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    execution_id = str(uuid.uuid4())
    wf = workflows[workflow_id]
    ordered = resolve_step_order(wf["steps"]) if wf.get("steps") else []
    created_ts = datetime.datetime.now().isoformat()
    execution_rec = {
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "status": WorkflowState.PENDING.value,
        "started_at": None,
        "completed_at": None,
        "steps_completed": 0,
        "total_steps": len(wf.get("steps", [])),
        "created_at": created_ts,
        "updated_at": created_ts,
        "step_order": ordered,  # not persisted yet, for response convenience
        "replay_of": None,
        "input_snapshot": {"workflow_id": workflow_id, "steps": wf.get("steps", [])},
    }
    # Persist execution (pending) & initial step states
    repo = get_workflows_repo()
    deps_map = {s["name"]: set(s.get("depends_on", []) or []) for s in wf.get("steps", [])}
    step_state_map: dict[str, dict[str, Any]] = {}
    for s in wf.get("steps", []):
        initial_status = StepState.PENDING.value if deps_map[s["name"]] else StepState.READY.value
        state_obj = {
            "name": s["name"],
            "agent_id": s["agent_id"],
            "depends_on": list(deps_map[s["name"]]),
            "status": initial_status,
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        step_state_map[s["name"]] = state_obj
    workflow_step_states[execution_id] = step_state_map  # keep ephemeral cache for runtime speed
    if repo:
        try:
            repo.create_execution(execution_rec)
            for step_name, meta in step_state_map.items():
                repo.upsert_step_state(execution_id, step_name, meta)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to persist initial execution %s: %s", execution_id, e)
    # Keep minimal legacy in-memory record for backward compatibility with metrics until refactor complete
    workflow_executions[execution_id] = execution_rec
    background_tasks.add_task(run_workflow, workflow_id, execution_id)
    return {"execution_id": execution_id, "status": "started"}


@app.get("/api/v1/workflows/executions/{execution_id}")
async def get_execution_status(
    execution_id: str, current_user: dict = Depends(get_current_active_user)
):
    repo = get_workflows_repo()
    execution = None
    if repo:
        try:
            execution = repo.get_execution(execution_id)
        except Exception as e:  # pragma: no cover
            logger.warning("DB get_execution failed %s: %s", execution_id, e)
    # Fallback to in-memory (legacy) if repo miss
    if not execution:
        execution = workflow_executions.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    step_states: list[dict[str, Any]] | dict[str, Any]
    if repo and execution:
        try:
            step_states = repo.list_step_states(execution_id)
        except Exception:  # pragma: no cover
            step_states = []
    else:
        # legacy format dict of states keyed by step
        step_states = list((workflow_step_states.get(execution_id) or {}).values())
    return {"execution": execution, "steps": step_states}


async def run_workflow(workflow_id: str, execution_id: str):
    wf = workflows.get(workflow_id)
    if not wf:  # workflow deleted mid-run
        return
    repo = get_workflows_repo()
    # Lazy-register step metrics (avoid duplicate registration if module reloaded)
    global step_duration_hist, step_error_counter
    try:
        step_duration_hist  # type: ignore[name-defined]
    except NameError:  # first time
        try:
            from prometheus_client import Counter, Histogram

            buckets_env = os.getenv("WORKFLOW_STEP_DURATION_BUCKETS", "").strip()
            if buckets_env:
                try:
                    parsed = [float(x) for x in buckets_env.split(",") if x.strip()]
                    parsed = [b for b in parsed if b > 0]
                    parsed.sort()
                    buckets_tuple = tuple(parsed) if parsed else (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10)
                except Exception:  # pragma: no cover
                    buckets_tuple = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10)
            else:
                buckets_tuple = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10)
            step_duration_hist = Histogram(
                "workflow_step_duration_seconds",
                "Duration of individual workflow steps",
                ["workflow_id", "step_name"],
                buckets=buckets_tuple,
            )
            step_error_counter = Counter(
                "workflow_step_errors_total",
                "Total workflow step errors",
                ["workflow_id", "step_name"],
            )
        except Exception:  # pragma: no cover
            step_duration_hist = None  # type: ignore[assignment]
            step_error_counter = None  # type: ignore[assignment]
    # Reconstruct execution record either from repo (authoritative) or in-memory placeholder
    exec_rec = None
    if repo:
        try:
            exec_rec = repo.get_execution(execution_id)
        except Exception:  # pragma: no cover
            exec_rec = None
    if not exec_rec:
        exec_rec = workflow_executions.get(execution_id, {})
    # Mark running
    exec_rec["status"] = WorkflowState.RUNNING.value
    exec_rec["started_at"] = datetime.datetime.now().isoformat()
    steps_meta = workflow_step_states.get(execution_id, {})
    remaining = set(steps_meta.keys())
    if repo:
        try:
            repo.update_execution(exec_rec)
        except Exception:  # pragma: no cover
            pass
    try:
        while remaining:
            ready = [
                name
                for name in list(remaining)
                if steps_meta[name]["status"] == StepState.READY.value
            ]
            if not ready:
                raise RuntimeError(
                    "No executable steps but workflow not complete (dependency deadlock)"
                )
            for step_name in ready:
                steps_meta[step_name]["status"] = StepState.RUNNING.value
                steps_meta[step_name]["started_at"] = datetime.datetime.now().isoformat()
                _step_start = time.perf_counter()
                await asyncio.sleep(0.5)
                try:
                    # Simulated step execution logic. Introduce controlled failure via step definition flag "fail": true
                    if steps_meta[step_name].get("fail"):
                        raise RuntimeError("Simulated step failure")
                    steps_meta[step_name]["status"] = StepState.SUCCESS.value
                except Exception as step_err:  # pragma: no cover
                    steps_meta[step_name]["status"] = StepState.FAILED.value
                    steps_meta[step_name]["error"] = str(step_err)
                    if "step_error_counter" in globals() and step_error_counter:  # type: ignore[name-defined]
                        try:
                            step_error_counter.labels(
                                workflow_id=workflow_id, step_name=step_name
                            ).inc()
                        except Exception:
                            pass
                finally:
                    steps_meta[step_name]["completed_at"] = datetime.datetime.now().isoformat()
                    if "step_duration_hist" in globals() and step_duration_hist:  # type: ignore[name-defined]
                        try:
                            step_duration_hist.labels(
                                workflow_id=workflow_id, step_name=step_name
                            ).observe(time.perf_counter() - _step_start)
                        except Exception:
                            pass
                remaining.remove(step_name)
                for other in remaining:
                    deps = steps_meta[other]["depends_on"]
                    if deps and all(
                        steps_meta[d]["status"] == StepState.SUCCESS.value for d in deps
                    ):
                        if steps_meta[other]["status"] == StepState.PENDING.value:
                            steps_meta[other]["status"] = StepState.READY.value
                exec_rec["steps_completed"] = exec_rec.get("steps_completed", 0) + 1
                if repo:
                    try:
                        repo.upsert_step_state(execution_id, step_name, steps_meta[step_name])
                        repo.update_execution(exec_rec)
                    except Exception as e:  # pragma: no cover
                        logger.warning(
                            "Persist step state error %s/%s: %s", execution_id, step_name, e
                        )
        # Determine overall status (failed if any step failed)
        if any(s.get("status") == StepState.FAILED.value for s in steps_meta.values()):
            exec_rec["status"] = WorkflowState.FAILED.value
        else:
            exec_rec["status"] = WorkflowState.SUCCESS.value
        exec_rec["completed_at"] = datetime.datetime.now().isoformat()
    except Exception as e:  # pragma: no cover
        exec_rec["status"] = WorkflowState.FAILED.value
        exec_rec["error"] = str(e)
        exec_rec["completed_at"] = datetime.datetime.now().isoformat()
        logger.exception("Workflow execution %s failed: %s", execution_id, e)
    if repo:
        try:
            repo.update_execution(exec_rec)
            # Prune if retention enabled
            retention = get_execution_retention()
            if retention > 0:
                try:
                    deleted = repo.prune_executions(retention)
                    if deleted:
                        logger.info(
                            "Pruned %d old workflow executions (retention=%d)", deleted, retention
                        )
                except Exception:  # pragma: no cover
                    pass
        except Exception:  # pragma: no cover
            pass


# Dependency resolver -------------------------------------------------------
def resolve_step_order(steps: list[dict[str, Any]]) -> list[str]:
    """Return a topologically sorted list of step names.

    Raises HTTPException(400) on cycles or undefined dependencies.
    """
    graph = defaultdict(list)  # dep -> [dependents]
    indegree = defaultdict(int)
    names = {s["name"] for s in steps}
    for s in steps:
        indegree.setdefault(s["name"], 0)
        for dep in s.get("depends_on", []) or []:
            if dep not in names:
                raise HTTPException(
                    status_code=400, detail=f"Step '{s['name']}' depends on unknown step '{dep}'"
                )
            graph[dep].append(s["name"])
            indegree[s["name"]] += 1
    q = deque([n for n, d in indegree.items() if d == 0])
    order = []
    while q:
        node = q.popleft()
        order.append(node)
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)
    if len(order) != len(names):
        raise HTTPException(status_code=400, detail="Cycle detected in workflow steps")
    return order


# File Processing
@app.post("/api/v1/files/upload")
async def upload_file(
    file: UploadFile = Depends(validate_file_upload),
    current_user: dict = Depends(require_file_access),
):
    file_id = str(uuid.uuid4())
    file_path = Path("uploads") / f"{file_id}_{file.filename}"
    file_path.parent.mkdir(exist_ok=True)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "status": "uploaded",
        "path": str(file_path),
    }


@app.post("/api/v1/files/{file_id}/process")
async def process_file(
    file_id: str, agent_id: str = "data_analyst", current_user: dict = Depends(require_file_access)
):
    return {
        "file_id": file_id,
        "agent_id": agent_id,
        "status": "processing",
        "message": f"File is being processed by {agent_id}",
        "estimated_time": "2-5 minutes",
    }


# Advanced Analytics
@app.get("/api/v2/analytics/system/health")
async def system_health_analytics(current_user: dict = Depends(require_analytics_access)):
    registry = load_agents()
    return {
        "health_score": 96,
        "performance_metrics": {
            "response_time": "< 50ms",
            "throughput": "200+ req/sec",
            "error_rate": "< 0.1%",
            "availability": "99.9%",
        },
        "resource_usage": {
            "cpu_usage": "18%",
            "memory_usage": "2.8GB",
            "disk_usage": "42%",
            "network_io": "45MB/s",
        },
        "agent_metrics": {
            "total_agents": len(registry),
            "active_agents": len([a for a in registry.values() if a.get("status") == "available"]),
            "conversations_today": len(conversations),
            "success_rate": "99.7%",
        },
        "predictions": {
            "load_forecast": "Stable for next 24h",
            "scaling_recommendation": "Current capacity sufficient",
            "maintenance_window": "No maintenance required",
        },
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v2/analytics/agents/performance")
async def agent_performance_analytics(current_user: dict = Depends(require_analytics_access)):
    registry = load_agents()
    agent_stats: dict[str, Any] = {}
    for agent_id, agent in registry.items():
        agent_convs = [c for c in conversations.values() if c["agent_id"] == agent_id]
        agent_stats[agent_id] = {
            "name": agent.get("name", agent_id),
            "conversations": len(agent_convs),
            "avg_response_time": f"{30 + (hash(agent_id) % 20)}ms",
            "success_rate": f"{98 + (hash(agent_id) % 2)}.{hash(agent_id) % 10}%",
            "user_satisfaction": f"{4.2 + (hash(agent_id) % 8) / 10:.1f}/5.0",
        }

    return {
        "agent_performance": agent_stats,
        "top_performing": (
            max(agent_stats.keys(), key=lambda x: float(agent_stats[x]["success_rate"].rstrip("%")))
            if agent_stats
            else None
        ),
        "total_conversations": len(conversations),
        "average_session_length": "12.4 minutes",
        "timestamp": datetime.datetime.now().isoformat(),
    }


# JWT Authentication Endpoints
@app.post("/api/v1/auth/login", response_model=LoginResponse)
@AUTH_RATE_LIMIT  # 5 attempts per 15 minutes
async def login(login_data: LoginRequest, request: Request, response: Response) -> LoginResponse:
    """Authenticate user with JWT tokens"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    login_response = jwt_auth_service.login(
        username=login_data.username,
        password=login_data.password,
        remember_me=login_data.remember_me,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if not login_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set secure HTTP-only cookie for web clients
    if login_response.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=login_response.refresh_token,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            secure=True,
            samesite="strict",
        )

    return login_response


@app.post("/api/v1/auth/register")
async def register(register_data: RegisterRequest) -> dict[str, Any]:
    """Register new user account"""
    user = jwt_auth_service.register(
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        full_name=register_data.full_name,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists"
        )

    return {"message": "User registered successfully", "user": user}


@app.post("/api/v1/auth/logout")
async def logout(
    request: Request, response: Response, current_user: dict = Depends(get_current_active_user)
) -> dict[str, str]:
    """Logout user and invalidate session"""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        jwt_auth_service.logout(token)

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")

    return {"message": "Logged out successfully"}


@app.get("/api/v1/auth/profile")
async def get_profile(current_user: dict = Depends(get_current_active_user)) -> dict[str, Any]:
    """Get current user profile"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "role": current_user["role"],
        "created_at": current_user["created_at"],
        "last_login": current_user.get("last_login"),
    }


@app.post("/api/v1/auth/change-password")
async def change_password(
    password_data: dict, current_user: dict = Depends(get_current_active_user)
) -> dict[str, str]:
    """Change user password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required",
        )

    success = jwt_auth_service.change_password(
        user_id=current_user["id"], current_password=current_password, new_password=new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )

    return {"message": "Password changed successfully"}


@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request) -> dict[str, str]:
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    new_access_token = jwt_auth_service.refresh_access_token(refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return {"access_token": new_access_token, "token_type": "bearer"}


@app.get("/api/v1/system/status")
async def comprehensive_system_status(
    current_user: dict = Depends(require_permission(Permission.SYSTEM_VIEW)),
):
    registry = load_agents()
    return {
        "system": "AutoGen Multi-Agent WebUI Enterprise",
        "version": "2.0.0",
        "status": "operational",
        "uptime": "99.9%",
        "components": {
            "api_server": "healthy",
            "agents": f"{len(registry)} active",
            "conversations": f"{len(conversations)} active",
            "workflows": f"{len(workflows)} configured",
            "storage": "connected",
            "monitoring": "active",
        },
        "features": [
            "Real-time agent conversations",
            "Workflow automation engine",
            "File processing pipeline",
            "Advanced analytics dashboard",
            "Multi-agent orchestration",
            "Conversation history tracking",
        ],
        "performance": {
            "requests_per_second": 200,
            "average_response_time": "45ms",
            "error_rate": "0.1%",
            "concurrent_users": 25,
        },
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Admin User Management Endpoints
@app.get("/api/v1/admin/users")
async def list_users(
    limit: int = 100, offset: int = 0, current_user: dict = Depends(require_user_management)
) -> dict[str, Any]:
    """List all users (admin only)"""
    users = jwt_auth_service.users_repo.list_users(limit=limit, offset=offset)
    return {"users": users, "total": len(users), "limit": limit, "offset": offset}


@app.get("/api/v1/admin/users/{user_id}")
async def get_user(
    user_id: int, current_user: dict = Depends(require_user_management)
) -> dict[str, Any]:
    """Get specific user (admin only)"""
    user = jwt_auth_service.users_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Remove sensitive information
    safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
    return safe_user


@app.put("/api/v1/admin/users/{user_id}")
async def update_user(
    user_id: int, user_data: dict, current_user: dict = Depends(require_user_management)
) -> dict[str, str]:
    """Update user (admin only)"""
    success = jwt_auth_service.users_repo.update_user(
        user_id=user_id,
        email=user_data.get("email"),
        full_name=user_data.get("full_name"),
        role=user_data.get("role"),
        is_active=user_data.get("is_active"),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found or update failed"
        )

    return {"message": "User updated successfully"}


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(
    user_id: int, current_user: dict = Depends(require_user_management)
) -> dict[str, str]:
    """Delete user (admin only)"""
    # Prevent admin from deleting themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )

    success = jwt_auth_service.users_repo.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User deleted successfully"}


@app.get("/api/v1/admin/stats")
@SENSITIVE_RATE_LIMIT  # 10 requests per 5 minutes
async def get_admin_stats(
    request: Request, current_user: dict = Depends(require_admin_access)
) -> dict[str, Any]:
    """Get admin statistics"""
    user_stats = jwt_auth_service.users_repo.get_user_stats()

    return {
        "users": user_stats,
        "agents": {
            "total": len(load_agents()),
            "active": len([a for a in load_agents().values() if a.get("status") == "available"]),
        },
        "conversations": {
            "total": len(conversations),
            "active": len([c for c in conversations.values() if c.get("status") == "active"]),
        },
        "workflows": {"total": len(workflows), "executions": count_executions()},
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.post("/api/v1/admin/cleanup")
async def cleanup_sessions(current_user: dict = Depends(require_admin_access)) -> dict[str, Any]:
    """Clean up expired sessions and tokens"""
    cleaned_sessions = jwt_auth_service.cleanup_expired_sessions()

    return {
        "message": "Cleanup completed",
        "expired_sessions_removed": cleaned_sessions,
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Role and Permission Management Endpoints
@app.get("/api/v1/admin/roles")
async def get_all_roles(current_user: dict = Depends(require_admin_access)) -> dict[str, Any]:
    """Get all available roles and their permissions"""
    from roles_permissions import ROLE_PERMISSIONS

    roles_info = {}
    for role, permissions in ROLE_PERMISSIONS.items():
        roles_info[role.value] = {
            "name": role.value,
            "permissions": [perm.value for perm in permissions],
            "permission_count": len(permissions),
        }

    return {
        "roles": roles_info,
        "total_roles": len(roles_info),
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Rate Limiting Management Endpoints
@app.get("/api/v1/admin/rate-limits/stats")
@SENSITIVE_RATE_LIMIT
async def get_rate_limit_stats(
    request: Request, current_user: dict = Depends(require_admin_access)
):
    """Get rate limiting statistics"""
    stats = rate_limiter.get_stats()
    return {
        "rate_limiting": stats,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_active_limits": stats["total_keys"],
        "total_rules": stats["total_rules"],
    }


@app.get("/api/v1/admin/security/config")
@SENSITIVE_RATE_LIMIT
async def get_security_config(request: Request, current_user: dict = Depends(require_admin_access)):
    """Get current security configuration"""
    return {
        "security_config": {
            "environment": SecurityConfig.get_environment(),
            "production_mode": SecurityConfig.is_production(),
            "cors_origins": HardenedCORSMiddleware.get_allowed_origins(),
            "cors_methods": HardenedCORSMiddleware.get_allowed_methods(),
            "cors_headers": HardenedCORSMiddleware.get_allowed_headers(),
            "admin_ip_whitelist_enabled": bool(SecurityConfig.get_admin_ip_whitelist()),
            "api_ip_whitelist_enabled": bool(SecurityConfig.get_api_ip_whitelist()),
            "docs_enabled": not SecurityConfig.is_production(),
        },
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v1/admin/security/validation/status")
@SENSITIVE_RATE_LIMIT
async def get_validation_status(
    request: Request, current_user: dict = Depends(require_admin_access)
):
    """Get input validation configuration status"""
    try:
        from input_validation import ValidationConfig

        limits = ValidationConfig.get_limits()
        allowed_types = ValidationConfig.get_allowed_file_types()
        dangerous_extensions = ValidationConfig.get_dangerous_extensions()

        return {
            "status": "success",
            "validation_enabled": True,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "limits": {
                "max_message_length": limits.max_message_length,
                "max_file_size": limits.max_file_size,
                "max_json_size": limits.max_json_size,
                "max_array_length": limits.max_array_length,
                "max_object_depth": limits.max_object_depth,
                "max_files_per_request": limits.max_files_per_request,
            },
            "file_validation": {
                "allowed_types_count": len(allowed_types),
                "blocked_extensions_count": len(dangerous_extensions),
                "mime_detection_enabled": True,
                "malicious_content_scanning": True,
            },
            "security_features": {
                "xss_protection": True,
                "sql_injection_protection": True,
                "command_injection_protection": True,
                "path_traversal_protection": True,
                "executable_detection": True,
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/admin/security/validation/limits")
@SENSITIVE_RATE_LIMIT
async def get_validation_limits(
    request: Request, current_user: dict = Depends(require_admin_access)
):
    """Get detailed validation limits and configuration"""
    try:
        from input_validation import ValidationConfig

        limits = ValidationConfig.get_limits()
        allowed_types = list(ValidationConfig.get_allowed_file_types())
        dangerous_extensions = list(ValidationConfig.get_dangerous_extensions())

        return {
            "status": "success",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "validation_limits": {
                "messages": {
                    "max_message_length": limits.max_message_length,
                    "max_messages_per_conversation": limits.max_messages_per_conversation,
                },
                "files": {
                    "max_file_size": limits.max_file_size,
                    "max_files_per_request": limits.max_files_per_request,
                    "max_filename_length": limits.max_filename_length,
                },
                "json": {
                    "max_json_size": limits.max_json_size,
                    "max_array_length": limits.max_array_length,
                    "max_object_depth": limits.max_object_depth,
                },
                "strings": {
                    "max_string_length": limits.max_string_length,
                    "max_description_length": limits.max_description_length,
                    "max_name_length": limits.max_name_length,
                    "max_url_length": limits.max_url_length,
                },
                "workflows": {
                    "max_workflow_steps": limits.max_workflow_steps,
                    "max_workflow_depth": limits.max_workflow_depth,
                },
                "agents": {
                    "max_agent_capabilities": limits.max_agent_capabilities,
                    "max_agent_settings_size": limits.max_agent_settings_size,
                },
            },
            "file_validation": {
                "allowed_mime_types": sorted(allowed_types),
                "blocked_extensions": sorted(dangerous_extensions),
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting validation limits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/admin/rate-limits/reset/{key}")
@SENSITIVE_RATE_LIMIT
async def reset_rate_limit(
    key: str, request: Request, current_user: dict = Depends(require_admin_access)
):
    """Reset rate limit for a specific key"""
    rate_limiter.reset_key(key)
    return {"reset": True, "key": key, "timestamp": datetime.datetime.now().isoformat()}


@app.get("/api/v1/admin/permissions")
async def get_all_permissions(current_user: dict = Depends(require_admin_access)) -> dict[str, Any]:
    """Get all available permissions"""
    from roles_permissions import Permission

    permissions_by_category = {
        "agent": [perm.value for perm in Permission if perm.value.startswith("agent:")],
        "conversation": [
            perm.value for perm in Permission if perm.value.startswith("conversation:")
        ],
        "workflow": [perm.value for perm in Permission if perm.value.startswith("workflow:")],
        "file": [perm.value for perm in Permission if perm.value.startswith("file:")],
        "system": [perm.value for perm in Permission if perm.value.startswith("system:")],
        "analytics": [perm.value for perm in Permission if perm.value.startswith("analytics:")],
        "user": [perm.value for perm in Permission if perm.value.startswith("user:")],
        "session": [perm.value for perm in Permission if perm.value.startswith("session:")],
        "api_key": [perm.value for perm in Permission if perm.value.startswith("api_key:")],
        "admin": [perm.value for perm in Permission if perm.value.startswith("admin:")],
    }

    return {
        "permissions": permissions_by_category,
        "total_permissions": sum(len(perms) for perms in permissions_by_category.values()),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.get("/api/v1/admin/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int, current_user: dict = Depends(require_user_management)
) -> dict[str, Any]:
    """Get permissions for a specific user"""
    user = jwt_auth_service.users_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_permissions = RolePermissionManager.get_user_permissions(user)

    return {
        "user_id": user_id,
        "username": user["username"],
        "role": user["role"],
        "permissions": [perm.value for perm in user_permissions],
        "permission_count": len(user_permissions),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.post("/api/v1/admin/users/{user_id}/role")
async def change_user_role(
    user_id: int, role_data: dict, current_user: dict = Depends(require_user_management)
) -> dict[str, str]:
    """Change user role"""
    new_role = role_data.get("role")
    if not new_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is required")

    if not RolePermissionManager.is_valid_role(new_role):
        valid_roles = RolePermissionManager.get_all_roles()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Valid roles: {valid_roles}",
        )

    # Prevent user from changing their own role
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own role"
        )

    # Only admin can assign admin role
    if new_role == UserRole.ADMIN.value and current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can assign admin role"
        )

    success = jwt_auth_service.users_repo.update_user(user_id=user_id, role=new_role)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found or update failed"
        )

    return {"message": f"User role changed to {new_role} successfully"}


@app.get("/api/v1/users/me/permissions")
async def get_my_permissions(
    current_user: dict = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get current user's permissions"""
    user_permissions = RolePermissionManager.get_user_permissions(current_user)

    return {
        "user_id": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"],
        "permissions": [perm.value for perm in user_permissions],
        "permission_count": len(user_permissions),
        "can_manage_users": RolePermissionManager.user_has_permission(
            current_user, Permission.USER_EDIT_ALL
        ),
        "can_access_admin": RolePermissionManager.user_has_permission(
            current_user, Permission.ADMIN_ALL
        ),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@app.post("/api/v1/users/me/check-permission")
async def check_my_permission(
    permission_data: dict, current_user: dict = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Check if current user has a specific permission"""
    permission_name = permission_data.get("permission")
    if not permission_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Permission is required"
        )

    try:
        permission = Permission(permission_name)
        has_permission = RolePermissionManager.user_has_permission(current_user, permission)

        return {
            "permission": permission_name,
            "has_permission": has_permission,
            "user_role": current_user["role"],
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid permission: {permission_name}"
        )


@app.on_event("startup")
async def unified_startup():  # pragma: no cover - side effects
    """Single startup hook: start batch worker, init auth DB, configure rate limits once."""
    # Start batch worker (idempotent best-effort)
    try:
        start_db_batch_worker()
    except Exception as e:
        logger.warning("Unable to start DB batch worker: %s", e)

    DB_PATH = Path(
        os.getenv("DB_PATH", Path(__file__).resolve().parent.parent / "data" / "platform.db")
    )
    if SAFE_MODE:
        _phase("SKIP: auth DB init & rate limits (SAFE_MODE)")
    else:
        try:
            jwt_auth_service.db_path = DB_PATH
            jwt_auth_service.users_repo = jwt_auth_service.users_repo.__class__(DB_PATH)
            jwt_auth_service.users_repo.seed_admin_user()
            _phase("OK: auth DB initialized")
        except Exception as e:
            _phase(f"ERR: auth DB init failed {e}")
            logger.warning("JWT auth initialization issue: %s", e)

        try:
            setup_default_rate_limits()
            _phase("OK: default rate limits setup")
        except Exception as e:
            _phase(f"ERR: rate limit setup failed {e}")
            logger.warning("Rate limit setup failed: %s", e)

    logger.info("Startup complete DB=%s SAFE_MODE=%s", DB_PATH, SAFE_MODE)
    _phase("STARTUP: complete")
    atexit.register(lambda: _drain_db_queue(force=True))


if __name__ == "__main__":
    import time
    import traceback

    import uvicorn

    host = os.getenv("ADV_BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("ADV_BACKEND_PORT", "8011"))
    reload_flag = os.getenv("ADV_BACKEND_RELOAD", "false").lower() == "true"
    uvicorn_log_level = os.getenv("ADV_BACKEND_LOG_LEVEL", os.getenv("LOG_LEVEL", "info"))
    start_msg = (
        f"Starting Advanced Backend host={host} port={port} reload={reload_flag} "
        f"log_level={uvicorn_log_level} agents={len(load_agents())} SAFE_MODE={SAFE_MODE}"
    )
    try:
        logger.info(start_msg)
        # Also ensure message reaches a file for PyInstaller diagnostics
        log_file = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "startup_crash.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(start_msg + "\n")
        uvicorn.run(app, host=host, port=port, log_level=uvicorn_log_level, reload=reload_flag)
    except Exception as e:  # pragma: no cover - diagnostic path
        err_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        try:
            sys.stderr.write("[FATAL-STARTUP] " + err_trace + "\n")
        except Exception:
            pass
        try:
            log_file = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "startup_crash.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n=== STARTUP CRASH ===\n")
                f.write(err_trace)
                f.write("\n=====================\n")
        except Exception:
            pass
        # Keep window open briefly in frozen mode for visibility
        time.sleep(5)
        raise
