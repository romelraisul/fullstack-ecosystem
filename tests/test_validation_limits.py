def test_validation_limits_endpoint(client, admin_headers):
    r = client.get("/api/v1/admin/security/validation/limits", headers=admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "success"
    assert "validation_limits" in data
    assert "messages" in data["validation_limits"]
