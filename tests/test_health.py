def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "environment" in body


def test_info(client):
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "TextFile Manager API"
