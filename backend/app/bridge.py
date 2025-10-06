from fastapi import APIRouter, HTTPException
from prometheus_client import Counter, Gauge
from pydantic import BaseModel, Field

try:
    # Use dynamic REGISTRY reference if tests monkeypatch it (prom_core.REGISTRY)
    import prometheus_client.core as _prom_core  # type: ignore

    _registry = getattr(_prom_core, "REGISTRY", None)
except Exception:  # pragma: no cover
    _registry = None
import json
import time
from pathlib import Path

DATA_PATH = Path("/app/app/bridge_data.json")

router = APIRouter(prefix="/bridge", tags=["bridge"])


def _existing_metric(name: str):
    try:
        live = getattr(_prom_core, "REGISTRY", None)
        if live and hasattr(live, "_names_to_collectors"):
            return live._names_to_collectors.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None
    return None


_SEEN = set()


def _safe_counter(name: str, doc: str, **kw):
    if name in _SEEN:
        ex = _existing_metric(name)
        if ex:
            return ex
    try:
        c = Counter(name, doc, **kw)
        _SEEN.add(name)
        return c
    except Exception:
        ex = _existing_metric(name)
        if ex:
            return ex

        class _NoOp:
            def labels(self, **_k):
                return self

            def inc(self, *a, **k):
                return None

        return _NoOp()


def _safe_gauge(name: str, doc: str, **kw):
    if name in _SEEN:
        ex = _existing_metric(name)
        if ex:
            return ex
    try:
        g = Gauge(name, doc, **kw)
        _SEEN.add(name)
        return g
    except Exception:
        ex = _existing_metric(name)
        if ex:
            return ex

        class _NoOp:
            def labels(self, **_k):
                return self

            def set(self, *a, **k):
                return None

        return _NoOp()


bridge_inputs_total = _existing_metric("bridge_inputs_total") or _safe_counter(
    "bridge_inputs_total", "Total research inputs created", registry=_registry
)
bridge_experiments_total = _existing_metric("bridge_experiments_total") or _safe_counter(
    "bridge_experiments_total", "Total experiments approved", registry=_registry
)
bridge_inputs_by_status = _existing_metric("bridge_inputs_by_status") or _safe_gauge(
    "bridge_inputs_by_status",
    "Current number of inputs by status",
    labelnames=("status",),
    registry=_registry,
)
bridge_inputs_by_owner = _existing_metric("bridge_inputs_by_owner") or _safe_gauge(
    "bridge_inputs_by_owner",
    "Current number of inputs by owner",
    labelnames=("owner",),
    registry=_registry,
)

VALID_STATUSES = ("new", "reviewing", "approved", "rejected")


def _recompute_status_gauge(data):
    counts = dict.fromkeys(VALID_STATUSES, 0)
    for i in data.get("inputs", []):
        s = (i.get("status") or "").lower()
        if s in counts:
            counts[s] += 1
    for s, v in counts.items():
        bridge_inputs_by_status.labels(status=s).set(v)


def _recompute_owner_gauge(data):
    counts = {}
    for i in data.get("inputs", []):
        owner = (i.get("owner") or "").strip()
        if not owner:
            continue
        counts[owner] = counts.get(owner, 0) + 1
    # Set gauges for observed owners
    for owner, v in counts.items():
        bridge_inputs_by_owner.labels(owner=owner).set(v)


class ResearchInput(BaseModel):
    id: int
    title: str = Field(..., min_length=3, max_length=200)
    problem: str = Field(..., min_length=3)
    hypothesis: str | None = None
    impact_score: int = Field(5, ge=1, le=10)
    tags: list[str] = []
    owner: str | None = None
    status: str = "new"  # new -> reviewing -> approved/rejected
    created_at: float


class CreateInput(BaseModel):
    title: str
    problem: str
    hypothesis: str | None = None
    impact_score: int = 5
    tags: list[str] = []
    owner: str | None = None


class Experiment(BaseModel):
    id: int
    input_id: int
    objective: str
    owner: str | None = None
    status: str = "approved"
    created_at: float


def _load():
    if not DATA_PATH.exists():
        return {"inputs": [], "experiments": []}
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/inputs", response_model=list[ResearchInput])
def list_inputs(owner: str | None = None, tag: str | None = None, status: str | None = None):
    items = _load()["inputs"]
    if owner:
        items = [i for i in items if (i.get("owner") or "").lower() == owner.lower()]
    if tag:
        items = [i for i in items if tag.lower() in [t.lower() for t in i.get("tags", [])]]
    if status:
        items = [i for i in items if (i.get("status") or "").lower() == status.lower()]
    return items


@router.post("/inputs", response_model=ResearchInput)
def create_input(payload: CreateInput):
    data = _load()
    new_id = (data["inputs"][-1]["id"] + 1) if data["inputs"] else 1
    item = ResearchInput(
        id=new_id,
        title=payload.title.strip(),
        problem=payload.problem.strip(),
        hypothesis=(payload.hypothesis or "").strip() or None,
        impact_score=payload.impact_score,
        tags=[t.strip() for t in (payload.tags or []) if t.strip()],
        owner=(payload.owner or "").strip() or None,
        created_at=time.time(),
    )
    data["inputs"].append(item.dict())
    _save(data)
    bridge_inputs_total.inc()
    _recompute_status_gauge(data)
    _recompute_owner_gauge(data)
    return item


class UpdateOwner(BaseModel):
    owner: str | None


@router.patch("/inputs/{input_id}/owner", response_model=ResearchInput)
def set_owner(input_id: int, body: UpdateOwner):
    data = _load()
    for i in data["inputs"]:
        if i["id"] == input_id:
            i["owner"] = (body.owner or "").strip() or None
            _save(data)
            _recompute_status_gauge(data)
            _recompute_owner_gauge(data)
            return i
    raise HTTPException(status_code=404, detail="input not found")


class UpdateStatus(BaseModel):
    status: str = Field(..., pattern=r"^(new|reviewing|approved|rejected)$")


@router.patch("/inputs/{input_id}/status", response_model=ResearchInput)
def set_status(input_id: int, body: UpdateStatus):
    data = _load()
    for i in data["inputs"]:
        if i["id"] == input_id:
            i["status"] = body.status
            _save(data)
            _recompute_status_gauge(data)
            _recompute_owner_gauge(data)
            return i
    raise HTTPException(status_code=404, detail="input not found")


@router.post("/experiments/{input_id}", response_model=Experiment)
def approve_experiment(input_id: int, objective: str):
    data = _load()
    match = next((i for i in data["inputs"] if i["id"] == input_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="input not found")
    new_id = (data["experiments"][-1]["id"] + 1) if data["experiments"] else 1
    exp = Experiment(
        id=new_id,
        input_id=input_id,
        objective=objective.strip(),
        created_at=time.time(),
    )
    data["experiments"].append(exp.dict())
    _save(data)
    bridge_experiments_total.inc()
    return exp


@router.get("/experiments", response_model=list[Experiment])
def list_experiments():
    return _load()["experiments"]


# Initialize gauges on import so dashboards have values immediately
try:
    _data = _load()
    _recompute_status_gauge(_data)
    _recompute_owner_gauge(_data)
except Exception:
    # Safe best-effort init
    pass
