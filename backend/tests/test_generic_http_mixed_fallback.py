import httpx
import pytest

from backend.app.main import app


class GenericHTTPMixedClient:
    """Simulates three candidate attempts:
    1. /health raises exception
    2. /metrics returns 200 but non-JSON (headers claim text/plain) so still ok path short-circuits
       (we then adjust to force continuation by marking status non-2xx)
    3. / root returns 503 to finalize fallback error path capturing last_exc vs status logic.
    We map sequence by detecting the suffix of URL called in order.
    """

    call_index = 0

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        # Candidate order in code: /health, /metrics, /, /systems/{slug}
        if url.endswith("/health"):
            GenericHTTPMixedClient.call_index += 1
            raise RuntimeError("boom health")
        if url.endswith("/metrics"):
            GenericHTTPMixedClient.call_index += 1
            # Return 200 but we want loop to continue (simulate not acceptable), so use 418 (non-2xx) to force continue
            return type(
                "Resp",
                (),
                {
                    "status_code": 418,
                    "json": lambda self=None: {},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "text/plain"},
                },
            )()
        if url.rstrip("/").endswith("api") or url.endswith("/"):
            GenericHTTPMixedClient.call_index += 1
            return type(
                "Resp",
                (),
                {
                    "status_code": 503,
                    "json": lambda self=None: {"error": "unavailable"},
                    "raise_for_status": lambda self=None: None,
                    "headers": {"content-type": "application/json"},
                },
            )()
        # fallback
        return type(
            "Resp",
            (),
            {
                "status_code": 500,
                "json": lambda self=None: {},
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "application/json"},
            },
        )()


@pytest.fixture
def mock_generic_http_mixed(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", GenericHTTPMixedClient)
    return GenericHTTPMixedClient


@pytest.mark.asyncio
async def test_generic_http_mixed_fallback(mock_generic_http_mixed):
    # Minimal inventory including one generic system (not special-case quantum ones)
    app.state.systems_inventory = [
        {
            "slug": "alpha-mega-system-framework",
            "maturity": "inferred",
            "category": "core",
            "api_base": "/api",  # relative triggers gateway/internal base logic
        }
    ]
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 4})
    # Should have total 1 system and error count 1 because all candidates failed to produce 2xx
    assert resp["total"] == 1
    assert resp["errors"] == 1
    # Ensure enterprise summary reflects failure
    cat = next(iter(resp["enterprise_summary"]["by_category"].values()))
    assert cat["errors"] == 1
