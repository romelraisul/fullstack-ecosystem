import httpx
import pytest

from backend.app.main import app, set_quantum_post_processor


class QuantumShapeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        if url.endswith("/health"):
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"status": "ok"},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/api/quantum/bell" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": {"00": 5, "11": 4}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/api/quantum/ghz" in url:
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": {"000": 3, "111": 2}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        return type(
            "Resp",
            (),
            {
                "status_code": 404,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "application/json"},
            },
        )()


@pytest.fixture
def mock_quantum_shape(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumShapeClient)
    return QuantumShapeClient


@pytest.mark.asyncio
async def test_quantum_postprocessor_unexpected_shape(mock_quantum_shape):
    # Hook returns a scalar string instead of dict/list to ensure we still attach it transparently.
    set_quantum_post_processor(lambda info: "weird-shape")
    app.state.systems_inventory = [
        {"slug": "qcae", "maturity": "inferred", "category": "quantum", "api_base": "/api"}
    ]
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 16})
    qentry = next(r for r in resp["systems"].values() if r and r.get("slug") == "qcae")
    assert qentry["post_info"] == "weird-shape"
    # Clean up hook
    set_quantum_post_processor(None)
