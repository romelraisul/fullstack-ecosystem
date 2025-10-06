import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from backend.app.main import app  # type: ignore


@pytest.fixture(scope="module")
def client():
    # Use localhost base_url to satisfy TrustedHostMiddleware allowed_hosts
    return TestClient(app, base_url="http://localhost")


def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("service") == "ecosystem-api"


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_metrics_endpoint_basic(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text.splitlines()
    # Expect at least one of the core app metrics
    assert any(l.startswith("app_startups_total") for l in body)
