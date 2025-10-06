from fastapi.testclient import TestClient

from backend.app.main import app


def test_delegate_empty_filtered_targets():
    with TestClient(app) as client:
        # No inventory set; targets provided won't match -> expect empty planned + dry_run
        r = client.post(
            "/orchestrate/delegate", json={"targets": ["non-existent"], "dry_run": True}
        )
        assert r.status_code == 200
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("planned") == []
        assert j.get("executed") == []
        assert j.get("dry_run") is True
