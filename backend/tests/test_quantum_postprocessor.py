import httpx
from fastapi.testclient import TestClient

from backend.app.main import app, set_quantum_post_processor


class QuantumHookClient:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *a, **k):
        class R:
            def __init__(self, sc, payload):
                self.status_code = sc
                self._payload = payload
                self.headers = {"content-type": "application/json"}

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPError("fail")

            def json(self):
                return self._payload

        if url.endswith("/health"):
            return R(200, {"status": "ok"})
        if "/api/quantum/bell" in url:
            return R(200, {"counts": {"00": 3, "11": 2}})
        if "/api/quantum/ghz" in url:
            return R(200, {"counts": {"000": 4, "111": 1}})
        return R(404, {})


def test_quantum_postprocessor_success(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumHookClient)

    def hook(data):
        # return derived parity counts
        return {"bell_len": len(data["bell_top"]), "ghz_len": len(data["ghz_top"])}

    set_quantum_post_processor(hook)
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
    systems = r.json().get("systems", {})
    q = systems.get("qcae")
    assert q and q.get("post_info", {}).get("bell_len") == 2
    set_quantum_post_processor(None)


class QuantumHookErrorClient(QuantumHookClient):
    async def get(self, url, *a, **k):
        return await super().get(url, *a, **k)


def test_quantum_postprocessor_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", QuantumHookErrorClient)

    def hook(data):
        raise RuntimeError("boom")

    set_quantum_post_processor(hook)
    app.state.systems_inventory = [
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        }
    ]
    client = TestClient(app)
    r = client.post("/orchestrate/full-experiment", json={"shots": 32})
    assert r.status_code == 200
    systems = r.json().get("systems", {})
    q = systems.get("qcae")
    assert q and q.get("ok") is False and "postprocess:" in q.get("error", "")
    set_quantum_post_processor(None)
