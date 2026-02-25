from fastapi.testclient import TestClient

from src.services.main_api_server import app


def test_api_v1_root_and_health():
    client = TestClient(app)

    r_root = client.get("/api/v1/")
    assert r_root.status_code == 200
    assert r_root.json().get("message") == "Unified AI Project API"

    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    assert r_health.json().get("status") == "healthy"


def test_system_emergency_flag_structure():
    client = TestClient(app)
    r = client.get("/api/v1/system/emergency")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "emergency_active"
    assert j["mode"] == "text-only"
    assert "action" in j
