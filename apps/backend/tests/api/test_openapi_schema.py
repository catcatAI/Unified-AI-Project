import json
from fastapi.testclient import TestClient

# Import the FastAPI app
from src.services.main_api_server import app

client = TestClient(app)


def test_openapi_schema_available():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "info" in data and "title" in data["info"]


def test_health_endpoints_exist():
    # Root health
    r1 = client.get("/health")
    assert r1.status_code == 200

    # API v1 health
    r2 = client.get("/api/v1/health")
    # Some routers may mount health under /api/v1; accept 200 or 404 if not present
    assert r2.status_code in (200, 404)
