import pytest
from datetime import datetime
from src.auth.service import create_access_token


def test_get_file_content_empty(client, monkeypatch):
    # Ensure item exists and is a FILE, but no file_content row
    async def fake_fetch_one(query, *args):
        q = (query or "").lower()
        if "from items where" in q:
            return {"id": args[0], "type": "FILE"}
        if "from file_contents" in q:
            return None
        return None

    monkeypatch.setattr("src.db.connection.DatabasePool.fetch_one", fake_fetch_one)

    token = create_access_token(user_id="u1", username="u", role="USER").access_token
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/files/any-file/content", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == ""
    assert "etag" in body


def test_put_file_content_updates_and_returns_etag(client, monkeypatch):
    async def fake_fetch_one(query, *args):
        q = (query or "").lower()
        if "from items where" in q:
            return {"id": args[0], "type": "FILE"}
        if "insert into file_contents" in q:
            return {"content": args[1], "updated_at": datetime.utcnow()}
        return None

    async def fake_execute(query, *args):
        return None

    monkeypatch.setattr("src.db.connection.DatabasePool.fetch_one", fake_fetch_one)
    monkeypatch.setattr("src.db.connection.DatabasePool.execute", fake_execute)

    token = create_access_token(user_id="u1", username="u", role="USER").access_token
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"content": "hello world"}
    resp = client.put("/files/any-file/content", headers=headers, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == "hello world"
    assert "etag" in body
