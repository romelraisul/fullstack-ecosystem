import httpx
import pytest

from backend.app.main import app, set_quantum_post_processor


class QuantumGHZJsonErrorClient:
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
                    "json": lambda self=None: {"counts": {"00": 9, "11": 8}},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/api/quantum/ghz" in url:
            # Valid status but JSON extraction fails
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: (_ for _ in ()).throw(
                        RuntimeError("json decode fail")
                    ),
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
def mock_quantum_ghz_json_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumGHZJsonErrorClient)
    return QuantumGHZJsonErrorClient


@pytest.mark.asyncio
async def test_quantum_ghz_json_error_path(mock_quantum_ghz_json_error):
    set_quantum_post_processor(None)
    app.state.systems_inventory = [
        {"slug": "qcae", "maturity": "inferred", "category": "quantum", "api_base": "/api"}
    ]
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 4})
    qentry = resp["systems"]["qcae"]
    assert qentry["ok"] is False
    assert "json decode fail" in qentry["error"]
