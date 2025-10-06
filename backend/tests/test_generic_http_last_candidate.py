import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class LastCandidateSuccessClient:
    def __init__(self, *a, **k):
        self.counter = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        # Return failures for first three candidate paths, success for last
        class R:
            def __init__(self, sc):
                self.status_code = sc
                self.headers = {"content-type": "text/plain"}

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPError("status fail")

            def json(self):
                return {}

        if url.endswith("/health"):
            return R(503)
        if url.endswith("/metrics"):
            return R(404)
        if url.endswith("/"):
            return R(500)
        # last path like /systems/slug succeed
        return R(200)


def test_generic_http_last_candidate_success(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", LastCandidateSuccessClient)
    app.state.systems_inventory = [
        {
            "slug": "tailsvc",
            "api_base": "http://tail.example",
            "category": "edge",
            "maturity": "stable",
        }
    ]
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r.status_code == 200
    sample = r.json().get("sample", [])
    entry = next((e for e in sample if e.get("slug") == "tailsvc"), None)
    assert entry and entry.get("ok") is True and entry.get("status") == 200
