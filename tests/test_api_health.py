"""Test the FastAPI health endpoints."""

from fastapi.testclient import TestClient

from oscmcp.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_diagnostics():
    r = client.get("/api/v1/diagnostics")
    assert r.status_code == 200
    data = r.json()
    assert "tool_count" in data
    assert "system" in data
