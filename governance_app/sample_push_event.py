"""Simulation utility for local push webhook testing.

Usage (PowerShell):
  $env:WEBHOOK_SECRET='devsecret'
  python -m uvicorn governance_app.app:app --port 8081 --reload
  python governance_app/sample_push_event.py

Environment overrides:
  GOV_APP_PORT  (default 8081)
  WEBHOOK_SECRET (shared secret; defaults to 'devsecret')
"""

from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "devsecret")
PORT = int(os.getenv("GOV_APP_PORT", "8081"))
HOST = "localhost"

payload = {
    "ref": "refs/heads/main",
    "after": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    "repository": {
        "full_name": "local/test-repo",
        "owner": {"login": "local"},
        "name": "test-repo",
    },
    "commits": [{"id": "deadbeef", "added": [".github/workflows/example.yml"], "modified": []}],
}

body = json.dumps(payload).encode()
digest = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
signature = f"sha256={digest}"

conn = http.client.HTTPConnection(HOST, PORT)
headers = {
    "X-GitHub-Event": "push",
    "X-Hub-Signature-256": signature,
    "Content-Type": "application/json",
    "User-Agent": "governance-app-sim",
}
conn.request("POST", "/webhook", body=body, headers=headers)
resp = conn.getresponse()
print("Status:", resp.status)
print("Response:", resp.read().decode())
conn.close()
