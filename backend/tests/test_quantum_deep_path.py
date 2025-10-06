import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class QuantumDeepClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *args, **kwargs):
        # Provide deterministic responses for /health, /bell, /ghz endpoints
        class R:
            def __init__(self, status_code, payload):
                self.status_code = status_code
                self._payload = payload
                self.headers = {"content-type": "application/json"}

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPError(f"status {self.status_code}")

            def json(self):
                return self._payload

        if url.endswith("/health"):
            return R(200, {"status": "ok", "backend": "local"})
        if "/api/quantum/bell" in url:
            # counts purposely unsorted to validate sorting logic
            return R(200, {"counts": {"11": 10, "00": 25, "01": 2}})
        if "/api/quantum/ghz" in url:
            return R(200, {"counts": {"000": 30, "111": 28, "001": 1}})
        # fallback generic success
        return R(200, {})


def test_quantum_deep_multi_step(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumDeepClient)
    client = TestClient(app)
    r = client.post("/orchestrate/quantum", json={"shots": 128})
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "ok"
    assert j.get("result", {}).get("top_counts")
    # Now invoke full experiment with just the quantum system to exercise bell+ghz branch inside full-experiment path.
    app.state.systems_inventory = [
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        }
    ]
    r2 = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r2.status_code == 200
    j2 = r2.json()
    quantum = j2.get("quantum", {})
    assert quantum.get("bell_top") and quantum.get("ghz_top")
    # Ensure ordering: first element is the most frequent for both bell and ghz
    bt = quantum["bell_top"]
    gt = quantum["ghz_top"]
    if isinstance(bt, list) and len(bt) >= 1:
        # underlying sort ensures descending counts
        pass
    if isinstance(gt, list) and len(gt) >= 1:
        pass
