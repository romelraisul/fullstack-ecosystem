import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


# Case A: all candidate endpoints return non-2xx (status only, no exceptions)
class AllStatusClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        class R:
            def __init__(self):
                self.status_code = 503
                self.headers = {"content-type": "text/plain"}

            def raise_for_status(self):
                # no raise (loop proceeds through candidates)
                return None

        return R()


# Case B: first raise exception, then final candidate non-2xx
class MixedErrorThenStatusClient(AllStatusClient):
    def __init__(self, *a, **k):
        self.calls = {}

    async def get(self, url, *a, **k):
        slug_part = url.split("/")[-1]
        count = self.calls.get(slug_part, 0)
        self.calls[slug_part] = count + 1
        if count == 0:
            raise httpx.ConnectError("injected-connect-failure", request=httpx.Request("GET", url))
        return await super().get(url, *a, **k)


def test_generic_http_all_status(monkeypatch):
    inv = [
        {
            "slug": "staticsvc",
            "api_base": "http://static.example",
            "category": "net",
            "maturity": "beta",
        }
    ]
    app.state.systems_inventory = inv
    monkeypatch.setattr(httpx, "AsyncClient", AllStatusClient)
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r.status_code == 200
    j = r.json()
    # Find staticsvc entry (may appear in sample or systems dictionary)
    entries = j.get("sample", []) + list(j.get("systems", {}).values())
    err = next((x for x in entries if isinstance(x, dict) and x.get("slug") == "staticsvc"), None)
    assert err and not err.get("ok") and "status" in (err.get("error") or "")


def test_generic_http_exception_then_status(monkeypatch):
    inv = [
        {
            "slug": "mixsvc",
            "api_base": "http://mixed.example",
            "category": "net",
            "maturity": "beta",
        }
    ]
    app.state.systems_inventory = inv
    monkeypatch.setattr(httpx, "AsyncClient", MixedErrorThenStatusClient)
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r.status_code == 200
    j = r.json()
    entries = j.get("sample", []) + list(j.get("systems", {}).values())
    err = next((x for x in entries if isinstance(x, dict) and x.get("slug") == "mixsvc"), None)
    assert err and not err.get("ok") and "injected-connect-failure" in (err.get("error") or "")
