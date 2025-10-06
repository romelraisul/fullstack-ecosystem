#!/usr/bin/env python3
"""Simple smoke test for auth flow.

Usage:
  python scripts/smoke_auth.py --base http://localhost:8000 --user admin --password changeme
"""

import argparse
import sys

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://localhost:8000")
parser.add_argument("--user", required=True)
parser.add_argument("--password", required=True)
args = parser.parse_args()

base = args.base.rstrip("/")

client = httpx.Client(timeout=10.0)

try:
    r = client.post(base + "/token", data={"username": args.user, "password": args.password})
    if r.status_code != 200:
        print("LOGIN FAIL", r.status_code, r.text)
        sys.exit(1)
    tok = r.json()["access_token"]
    refresh = r.json().get("refresh_token")
    print("Login OK. Access len:", len(tok))
    h = {"Authorization": f"Bearer {tok}"}
    r2 = client.get(base + "/api/achievements", headers=h)
    print("Achievements:", r2.status_code, len(r2.text))
    if refresh:
        r3 = client.post(base + "/refresh", json={"refresh_token": refresh})
        print("Refresh:", r3.status_code)
    m = client.get(base + "/metrics")
    print("Metrics length:", len(m.text))
    print("SMOKE SUCCESS")
except Exception as e:
    print("Smoke test error:", e)
    sys.exit(2)
finally:
    client.close()
