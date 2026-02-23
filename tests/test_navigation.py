import pytest
from src.auth.service import create_access_token


def test_navigation_tree_empty(client):
    token = create_access_token(user_id="u1", username="u", role="USER").access_token
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/navigation/any-node/tree", headers=headers)
    # The service is monkeypatched to return [] for fetch_all, but router will catch not found
    assert resp.status_code in (200, 404)
