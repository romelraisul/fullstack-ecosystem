import os
import sys
from typing import Any

from fastapi.testclient import TestClient

# Ensure we can import the FastAPI app from backend/app/main.py
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.main import app  # type: ignore


def test_systems_and_summary():
    with TestClient(app, base_url="http://localhost") as client:
        r = client.get("/systems")
        r.raise_for_status()
        systems = r.json()
        assert isinstance(systems, list)

        r2 = client.get("/systems/integration-summary")
        r2.raise_for_status()
        summary: dict[str, Any] = r2.json()
        assert isinstance(summary, dict)
        assert summary.get("total") == len(systems)
        # when all systems have api_base, these are equal; allow <= for generality
        assert summary.get("with_api_base") <= summary.get("total")
