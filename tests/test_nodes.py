import pytest
from src.auth.service import create_access_token


def test_list_nodes_returns_empty_root(client):
    # Create a token for a normal user
    token = create_access_token(user_id="u1", username="u", role="USER").access_token
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/items", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
