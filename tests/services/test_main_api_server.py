import pytest
from fastapi.testclient import TestClient
from fastapi.testclient import TestClient
from src.services.main_api_server import app, initialize_services, shutdown_services

# Use a pytest fixture to create the TestClient
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_read_main(client: TestClient):
    """Tests the root endpoint '/'."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Unified AI Project API"}

def test_get_status(client: TestClient):
    """Tests the status endpoint '/status'."""
    response = client.get("/status")
    assert response.status_code == 200
    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] == "running"
