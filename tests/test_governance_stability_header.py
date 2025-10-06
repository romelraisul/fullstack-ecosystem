import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.main import GovernanceStabilityHeaderMiddleware


def test_governance_stability_header_injected(tmp_path):
    # Create mock governance-summary.json
    summary = {"stability_ratio": 0.87654, "semver_policy_status": "ok"}
    summary_file = tmp_path / "governance-summary.json"
    summary_file.write_text(json.dumps(summary), encoding="utf-8")

    app = FastAPI()
    app.add_middleware(GovernanceStabilityHeaderMiddleware, path=str(summary_file), ttl=0)

    @app.get("/ping")
    def ping():
        return {"pong": True}

    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 200
    hdr = r.headers.get("X-Governance-Stability")
    assert hdr is not None, "Expected stability header present"
    # Expect formatted percent with two decimals
    assert hdr.endswith("%")
    # Convert back to float ensuring approximate equality
    val = float(hdr.rstrip("%"))
    assert 87.5 < val < 88.0
