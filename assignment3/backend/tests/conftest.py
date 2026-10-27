"""Every test runs against a TEMPORARY SQLite file with the mock model.
Never touches backend/steady.db and never makes a paid model call."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STEADY_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LIVE_CALL_LIMIT", "50")
    monkeypatch.setenv("ALLOW_FAILURE_SIMULATION", "1")
    from main import app
    with TestClient(app) as c:      # runs startup -> init_db on the temp file
        yield c


@pytest.fixture
def sid(client):
    return client.post("/api/sessions", json={}).json()["session_id"]
