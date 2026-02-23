import pytest
from datetime import datetime

from src.auth.service import create_access_token


def test_register_user(client, monkeypatch):
    calls = {"count": 0}

    async def fake_fetch_one(query, *args):
        calls["count"] += 1
        q = (query or "").lower()
        # simple heuristics: existence check queries contain 'from users where'
        if "from users where" in q and calls["count"] == 1:
            return None
        # insert returning
        if "returning" in q and "insert into users" in q:
            return {
                "id": "1111-2222",
                "username": args[0],
                "email": args[1],
                "role": "USER",
                "created_at": datetime.utcnow(),
            }
        # fallback
        return None

    monkeypatch.setattr("src.db.connection.DatabasePool.fetch_one", fake_fetch_one)
    async def fake_hash(pwd):
        return "$fake$hash"

    monkeypatch.setattr("src.users.service.hash_password", fake_hash)

    payload = {"username": "bob", "email": "bob@example.com", "password": "strongpass"}
    resp = client.post("/users", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "bob"
    assert body["email"] == "bob@example.com"


def test_demo_user_returns_credentials(client, monkeypatch):
    async def fake_fetch_one(query, *args):
        q = (query or "").lower()
        if "where username" in q:
            return {"username": "demo", "email": "demo@example.com"}
        return None

    monkeypatch.setattr("src.db.connection.DatabasePool.fetch_one", fake_fetch_one)
    resp = client.get("/users/demo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "demo"
    assert "password" in body
