import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from advanced_backend import app, sync_agents_to_db
from persistence import init_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    os.environ["DATABASE_URL"] = "sqlite:///./data/test_platform.db"
    init_db()
    sync_agents_to_db()
    yield
    if os.path.exists("./data/test_platform.db"):
        os.remove("./data/test_platform.db")

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["agents_count"] == 81

def get_auth_headers(username="testuser"):
    reg_data = {"username": username, "password": "password123"}
    client.post("/api/v1/auth/register", json=reg_data)
    login_data = {"username": username, "password": "password123"}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_agents():
    headers = get_auth_headers("user_list")
    response = client.get("/api/v1/agents", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 81

def test_get_agent():
    headers = get_auth_headers("user_get")
    response = client.get("/api/v1/agents/research_1", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == "research_1"

def test_create_conversation():
    headers = get_auth_headers("user_conv")
    data = {
        "agent_id": "coding_1",
        "initial_messages": [{"role": "user", "content": "Hello agent!"}]
    }
    response = client.post("/api/v1/conversations", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["agent_id"] == "coding_1"

def test_auth_flow():
    headers = get_auth_headers("user_flow")
    resp = client.get("/api/v1/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "user_flow"

def test_unauthorized_access():
    response = client.get("/api/v1/agents")
    assert response.status_code == 401

def test_add_message():
    headers = get_auth_headers("user_msg")
    # Create convo
    data = {"agent_id": "coding_1"}
    resp = client.post("/api/v1/conversations", json=data, headers=headers)
    conv_id = resp.json()["id"]
    
    # Add message
    msg = {"role": "user", "content": "Tell me a joke."}
    response = client.post(f"/api/v1/conversations/{conv_id}/messages", json=msg, headers=headers)
    assert response.status_code == 200
    assert len(response.json()["payload_json"]["messages"]) == 2
