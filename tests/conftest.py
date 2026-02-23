import os
import asyncio
import pytest
from fastapi.testclient import TestClient

# Ensure required env vars for Settings before importing app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from src.core.app import create_app
import src.db.connection as dbconn
import src.db.migrations as migrations
from src.core.config import settings


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch):
    async def noop_initialize(_settings):
        return None

    async def noop_close():
        return None

    async def fake_fetch_one(query, *args):
        q = (query or "").strip().lower()
        if q.startswith("select 1"):
            return {"one": 1}
        return None

    async def fake_fetch_all(query, *args):
        return []

    async def fake_execute(query, *args):
        return None

    async def fake_run_migrations():
        return None

    monkeypatch.setattr(dbconn.DatabasePool, "initialize", noop_initialize)
    monkeypatch.setattr(dbconn.DatabasePool, "close", noop_close)
    monkeypatch.setattr(dbconn.DatabasePool, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(dbconn.DatabasePool, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(dbconn.DatabasePool, "execute", fake_execute)
    monkeypatch.setattr(migrations.MigrationManager, "run_all_migrations", fake_run_migrations)

    # Make tests run with debug logging
    settings.debug = True
    settings.log_level = "DEBUG"

    yield


@pytest.fixture()
def client():
    # Create a fresh app instance to ensure lifespan startup/shutdown runs cleanly
    with TestClient(create_app()) as client:
        yield client
