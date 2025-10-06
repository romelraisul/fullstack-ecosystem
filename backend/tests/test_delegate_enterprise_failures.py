import httpx
import pytest

from backend.app.main import app


class DelegateJSONParseFailClient:
    """Simulate delegate endpoint returning 200 with invalid JSON raising during .json()."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        # /orchestrate/delegate internal call
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: (_ for _ in ()).throw(RuntimeError("bad json")),
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "application/json"},
            },
        )()


class DelegateNetworkErrorClient(DelegateJSONParseFailClient):
    async def post(self, url, json=None):
        raise RuntimeError("network down")


@pytest.fixture
def mock_delegate_json_parse_fail(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DelegateJSONParseFailClient)
    return DelegateJSONParseFailClient


@pytest.fixture
def mock_delegate_network_fail(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DelegateNetworkErrorClient)
    return DelegateNetworkErrorClient


@pytest.mark.asyncio
async def test_delegate_enterprise_json_parse_failure(mock_delegate_json_parse_fail):
    # Minimal inventory for light mode
    app.state.systems_inventory = []
    from backend.app.main import orchestrate_delegate_enterprise

    # Expect 500 since ok path requires valid JSON dict
    with pytest.raises(Exception) as ei:
        await orchestrate_delegate_enterprise(
            request=None, body={"compute": "light", "dry_run": False}
        )
    assert "delegate failed" in str(ei.value) or "500" in str(ei.value)


@pytest.mark.asyncio
async def test_delegate_enterprise_network_failure(mock_delegate_network_fail):
    app.state.systems_inventory = []
    from backend.app.main import orchestrate_delegate_enterprise

    with pytest.raises(Exception) as ei:
        await orchestrate_delegate_enterprise(request=None, body={"compute": "light"})
    msg = str(ei.value)
    assert "delegate error" in msg or "500" in msg


class DelegateNon2xxNoJsonClient(DelegateJSONParseFailClient):
    async def post(self, url, json=None):
        # Return 503 with body that is not JSON parseable and skip raising (simulate upstream failure)
        return type(
            "Resp",
            (),
            {
                "status_code": 503,
                "json": lambda self=None: (_ for _ in ()).throw(RuntimeError("no json")),
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "text/plain"},
            },
        )()


@pytest.fixture
def mock_delegate_non2xx_nojson(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DelegateNon2xxNoJsonClient)
    return DelegateNon2xxNoJsonClient


@pytest.mark.asyncio
async def test_delegate_enterprise_non2xx_no_json(mock_delegate_non2xx_nojson):
    app.state.systems_inventory = []
    from backend.app.main import orchestrate_delegate_enterprise

    with pytest.raises(Exception) as ei:
        await orchestrate_delegate_enterprise(request=None, body={"compute": "light"})
    assert "delegate failed" in str(ei.value) or "503" in str(ei.value)


class DelegateListBodyClient(DelegateJSONParseFailClient):
    async def post(self, url, json=None):
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self=None: ["not", "a", "dict"],
                "raise_for_status": lambda self=None: None,
                "headers": {"content-type": "application/json"},
            },
        )()


@pytest.fixture
def mock_delegate_list_body(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DelegateListBodyClient)
    return DelegateListBodyClient


@pytest.mark.asyncio
async def test_delegate_enterprise_list_body_failure(mock_delegate_list_body):
    app.state.systems_inventory = []
    from backend.app.main import orchestrate_delegate_enterprise

    with pytest.raises(Exception) as ei:
        await orchestrate_delegate_enterprise(request=None, body={"compute": "light"})
    # Should raise generic delegate failed due to non-dict data
    assert "delegate failed" in str(ei.value)


@pytest.mark.asyncio
async def test_full_experiment_empty_inventory():
    # Exercise zero inventory percent calculation (overall_ok_pct path with total==0)
    app.state.systems_inventory = []
    from backend.app.main import orchestrate_full_experiment

    resp = await orchestrate_full_experiment(request=None, body={"shots": 4})
    assert resp["total"] == 0
    assert resp["enterprise_summary"]["overall_ok_pct"] == 0.0
