import httpx
import pytest

from backend.app.main import app, set_quantum_post_processor


class QuantumGHZExceptionClient:
    """Health and bell succeed; GHZ call raises to exercise run_qcae exception branch after partial success."""

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
                    "json": lambda self=None: {"counts": {"00": 7, "11": 6}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/api/quantum/ghz" in url:
            raise RuntimeError("ghz failure after bell success")
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
def mock_quantum_ghz_exception(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumGHZExceptionClient)
    return QuantumGHZExceptionClient


@pytest.mark.asyncio
async def test_quantum_ghz_exception_path(mock_quantum_ghz_exception):
    set_quantum_post_processor(None)
    app.state.systems_inventory = [
        {"slug": "qcae", "maturity": "inferred", "category": "quantum", "api_base": "/api"}
    ]
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 8})
    # Failure due to GHZ error should mark qcae error and propagate error count
    assert resp["errors"] == 1 and resp["ok"] == 0
    qentry = resp["systems"]["qcae"]
    assert qentry["ok"] is False
    assert "ghz failure" in qentry["error"]
