import pytest
from src.auth import create_access_token


def test_login_calls_authenticate(client, monkeypatch):
    async def fake_auth(username, password):
        return {"id": "u1", "username": username, "role": "USER"}

    # Patch the function used by the router module reference
    monkeypatch.setattr("src.auth.router.authenticate_user", fake_auth)

    payload = {"username": "alice", "password": "pwd"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_protected_endpoint_requires_token(client):
    # Attempt to access protected route without token
    resp = client.get("/items")
    assert resp.status_code == 401 or resp.status_code == 403
