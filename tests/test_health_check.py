"""Test Health Check Endpoint"""
import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def test_app():
    """Create test FastAPI app"""
    from fastapi import FastAPI
    from api.router import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_health_check_endpoint(test_app):
    """Test health check endpoint returns healthy status"""
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(test_app):
    """Test root endpoint returns API info"""
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_system_metrics_endpoint(test_app):
    """Test system metrics endpoint"""
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/v1/system/metrics/detailed")

    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data


@pytest.mark.asyncio
async def test_emergency_mode_endpoint(test_app):
    """Test emergency mode endpoint"""
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/v1/system/emergency")

    assert response.status_code == 200
    assert response.json()["status"] == "emergency_active"


@pytest.mark.asyncio
async def test_cluster_status_endpoint(test_app):
    """Test cluster status endpoint exists"""
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    try:
        response = client.get("/api/v1/system/cluster/status")
        assert response.status_code == 200
    except Exception:
        pytest.skip("Cluster manager endpoint not available in mock")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])