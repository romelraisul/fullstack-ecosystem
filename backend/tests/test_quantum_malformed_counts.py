import httpx
import pytest

from backend.app.main import app, set_quantum_post_processor


class QuantumMalformedCountsClient:
    """Simulates successful HTTP responses but with malformed/non-dict counts payloads
    for bell and ghz to exercise defensive sorting / fallback branches in run_qcae.
    """

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        # health OK
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
            # counts returns a list instead of dict
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"counts": ["not", "a", "dict"]},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        if "/api/quantum/ghz" in url:
            # counts missing entirely
            return type(
                "Resp",
                (),
                {
                    "status_code": 200,
                    "json": lambda self=None: {"note": "no counts"},
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
def mock_quantum_malformed(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumMalformedCountsClient)
    return QuantumMalformedCountsClient


@pytest.mark.asyncio
async def test_quantum_malformed_counts_paths(mock_quantum_malformed):
    # Clear any post processor to focus on malformed counts fallback.
    set_quantum_post_processor(None)
    # Ensure inventory contains qcae only (minimal) so full-experiment focuses on this path
    app.state.systems_inventory = [
        {"slug": "qcae", "maturity": "inferred", "category": "quantum", "api_base": "/api"}
    ]
    from backend.app.main import orchestrate_full_experiment  # inline import to avoid circulars

    # Invoke the endpoint coroutine directly
    resp = await orchestrate_full_experiment(request=None, body={"shots": 8})
    # We still expect ok status even if counts malformed; top lists should degrade to empty lists
    qt = resp["quantum"]
    assert qt["bell_top"] in ([], None) or all(isinstance(t, tuple) for t in qt["bell_top"])
    assert qt["ghz_top"] in ([], None) or all(isinstance(t, tuple) for t in qt["ghz_top"])
    # Ensure result structure sanity
    assert resp["total"] == 1
    assert "enterprise_summary" in resp
