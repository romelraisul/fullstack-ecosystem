import os
import tempfile

import pytest
from fastapi.testclient import TestClient


# Ensure DB path isolated per test run
@pytest.fixture(scope="session")
def test_db_path():
    with tempfile.TemporaryDirectory() as tmp:
        db_file = os.path.join(tmp, "platform.db")
        os.environ["DB_PATH"] = db_file
        yield db_file


@pytest.fixture(scope="session")
def client(test_db_path):  # noqa: F811
    # Import after setting DB_PATH
    from autogen.advanced_backend import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a user, returning auth headers."""
    # Register (ignore if exists)
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "tester",
            "email": "tester@example.com",
            "password": "StrongPass123!",
            "full_name": "Tester",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "tester", "password": "StrongPass123!", "remember_me": False},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    """Seeds admin (startup should have created) and logs in."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123", "remember_me": False},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
