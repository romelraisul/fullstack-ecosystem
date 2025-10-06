import httpx
from fastapi.testclient import TestClient

from backend.app.main import app


class QuantumBellThenGHZFailClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
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
            return R(200, {"status": "ok"})
        if "/api/quantum/bell" in url:
            return R(200, {"counts": {"00": 20, "11": 15}})
        if "/api/quantum/ghz" in url:
            # Simulate failure
            raise httpx.ConnectError("ghz upstream down", request=httpx.Request("GET", url))
        return R(404, {})


def test_quantum_full_experiment_ghz_failure(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumBellThenGHZFailClient)
    app.state.systems_inventory = [
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        }
    ]
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 64})
    assert r.status_code == 200
    j = r.json()
    systems = j.get("systems", {})
    qcae_entry = systems.get("qcae")
    # Should record an error for qcae
    assert (
        qcae_entry
        and qcae_entry.get("ok") is False
        and "ghz" in (qcae_entry.get("error") or "").lower()
    )
