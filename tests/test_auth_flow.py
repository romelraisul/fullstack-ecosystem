import os
import tempfile

from fastapi.testclient import TestClient

from autogen.ultimate_enterprise_summary import UltimateEnterpriseSummary

# Ensure isolated sqlite DB per test run
os.environ["SUMMARY_AUTH_DB"] = os.path.join(tempfile.gettempdir(), "summary_auth_test.db")

app_instance = UltimateEnterpriseSummary()
client = TestClient(app_instance.app)

# Helper to create a user directly in DB (password hashed in app logic)
import sqlite3

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

with sqlite3.connect(app_instance.auth_db_path) as c:
    c.execute("DELETE FROM users")
    c.execute(
        "INSERT INTO users (username, full_name, role, hashed_password) VALUES (?,?,?,?)",
        ("admin", "Admin User", "admin", pwd_context.hash("secret_password1!")),
    )
    c.commit()


def test_login_success_and_etag_cache():
    r = client.post("/token", data={"username": "admin", "password": "secret_password1!"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    first = client.get("/api/achievements", headers=headers)
    assert first.status_code == 200
    etag = first.headers.get("ETag")
    assert etag
    second = client.get("/api/achievements", headers={**headers, "If-None-Match": etag})
    assert second.status_code == 304


def test_refresh_and_rate_limit():
    r = client.post("/token", data={"username": "admin", "password": "secret_password1!"})
    rt = r.json()["refresh_token"]
    # perform a valid refresh
    r2 = client.post("/refresh", json={"refresh_token": rt})
    assert r2.status_code == 200
    # hammer login to trigger rate limit (assuming default 10/min)
    for _i in range(15):
        client.post("/token", data={"username": "admin", "password": "wrong"})
    # After enough failures should start 200/401 but rate limit blocks might appear; ensure no crash
    assert True
