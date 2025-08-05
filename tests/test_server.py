""Tests for the OSCMCP server."""
import asyncio
import pytest
from fastapi.testclient import TestClient
from oscmcp import server, cli

@pytest.fixture
def test_app():
    """Create a test FastAPI app with test settings."""
    return cli.app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app)

@pytest.fixture(autouse=True)
async def setup_teardown():
    """Setup and teardown for tests."""
    # Setup
    await server.initialize()
    yield
    # Teardown
    await server.shutdown()

@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the server initializes and shuts down properly."""
    # Test is already initialized by the fixture
    assert server._initialized is True
    
    # Test shutdown
    await server.shutdown()
    assert server._initialized is False
    
    # Re-initialize for other tests
    await server.initialize()

@pytest.mark.asyncio
async def test_get_info():
    """Test getting server information."""
    info = await server.get_info()
    assert "name" in info
    assert "version" in info
    assert "description" in info
    assert "capabilities" in info
    assert isinstance(info["capabilities"], list)

def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

@pytest.mark.parametrize("endpoint", [
    "/docs",
    "/redoc",
])
def test_documentation_endpoints(test_client, endpoint):
    """Test documentation endpoints."""
    response = test_client.get(endpoint)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_execute_command(test_client):
    """Test executing a command through the MCP interface."""
    test_command = {
        "command": "test",
        "params": {"test_param": "test_value"}
    }
    
    response = test_client.post("/mcp/execute", json=test_command)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
