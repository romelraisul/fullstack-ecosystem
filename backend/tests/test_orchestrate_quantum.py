import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.mark.parametrize(
    "fixture_name,shots,expected_status,expect_error",
    [
        ("mock_quantum_success", 128, 200, False),
        ("mock_quantum_health_fail", 64, 503, True),
        ("mock_quantum_bell_fail", 64, 500, True),
    ],
)
def test_orchestrate_quantum_variants(fixture_name, shots, expected_status, expect_error, request):
    # Activate fixture dynamically
    request.getfixturevalue(fixture_name)
    with TestClient(app) as client:
        r = client.post("/orchestrate/quantum", json={"shots": shots})
        assert r.status_code == expected_status
        if expected_status == 200:
            j = r.json()
            assert j.get("status") == "ok"
            assert j.get("kind") == "bell"
            # Sanitization may clamp out-of-range, allow either asked or 512
            assert j.get("shots") in (shots, 512)
            assert isinstance(j.get("result", {}).get("top_counts"), list)
        else:
            # Error responses should carry detail
            j = r.json()
            assert "detail" in j


def test_orchestrate_quantum_shots_sanitization(mock_quantum_success):
    with TestClient(app) as client:
        too_low = client.post("/orchestrate/quantum", json={"shots": 0})
        assert too_low.status_code == 200
        assert too_low.json().get("shots") == 512
        too_high = client.post("/orchestrate/quantum", json={"shots": 500000})
        assert too_high.status_code == 200
        assert too_high.json().get("shots") == 512
