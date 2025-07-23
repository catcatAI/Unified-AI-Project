import pytest
from fastapi.testclient import TestClient
from src.services.main_api_server import app

# Use a pytest fixture to create the TestClient
@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient instance for the FastAPI app.
    The scope is 'module' so it's created only once per test module.
    """
    with TestClient(app) as c:
        yield c

@pytest.mark.timeout(15)
def test_read_main(client: TestClient):
    """Tests the root endpoint '/'."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Unified AI Project API"}

@pytest.mark.timeout(15)
def test_get_status(client: TestClient):
    """Tests the status endpoint '/status'."""
    response = client.get("/status")
    assert response.status_code == 200
    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] == "running"
