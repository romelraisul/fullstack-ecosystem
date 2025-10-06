import httpx
import pytest

from backend.app.main import app, set_quantum_post_processor


class QuantumGHZSortTypeErrorClient:
    """Bell succeeds with normal counts; GHZ returns counts mapping whose values include non-comparable types (e.g., list and int) causing sorting to raise."""

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
            # Non-comparable values: int and list to trigger TypeError in sorted key lambda
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": {"000": 3, "111": [2]}},
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
def mock_quantum_ghz_sort_exception(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumGHZSortTypeErrorClient)
    return QuantumGHZSortTypeErrorClient


@pytest.mark.asyncio
async def test_quantum_ghz_sort_exception_path(mock_quantum_ghz_sort_exception):
    set_quantum_post_processor(None)
    app.state.systems_inventory = [
        {"slug": "qcae", "maturity": "inferred", "category": "quantum", "api_base": "/api"}
    ]
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 4})
    # Sorting GHZ counts fails; run_qcae should return error for qcae
    qentry = resp["systems"]["qcae"]
    assert qentry["ok"] is False
    assert "error" in qentry
    assert resp["errors"] == 1
