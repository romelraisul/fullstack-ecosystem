def test_admin_permissions_endpoint_requires_auth(client):
    r = client.get("/api/v1/admin/permissions")
    assert r.status_code in (401, 403)


def test_admin_permissions_success(client, admin_headers):
    r = client.get("/api/v1/admin/permissions", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "permissions" in data
    assert data["total_permissions"] >= 1
