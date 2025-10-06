import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from governance_app.app import app, settings
from governance_app.persistence import DB_PATH, init_db

client = TestClient(app)


def setup_function(_):
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def sign(body: bytes) -> str:
    secret = settings.webhook_secret or "devsecret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_replay_protection_duplicate_delivery():
    payload = {"repository": {"full_name": "org/repo"}, "ref": "refs/heads/main", "commits": []}
    body = json.dumps(payload).encode()
    sig = sign(body)
    headers = {
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "deliv-123",
    }
    r1 = client.post("/webhook", data=body, headers=headers)
    assert r1.status_code in (200, 202)
    r2 = client.post("/webhook", data=body, headers=headers)
    assert r2.status_code == 409
