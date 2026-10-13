from fastapi.testclient import TestClient
from services.main_api_server import app


def test_api_v1_root_and_health():
    client = TestClient(app)

    r_root = client.get("/api/v1/")
    assert r_root.status_code == 200
    assert r_root.json().get("message") == "Unified AI Project API"

    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    assert r_health.json().get("status") == "healthy"


def test_system_emergency_mode_roundtrip():
    """POST trigger must set a real process-wide compute override.

    The old endpoint was a GET that returned "emergency_active" without
    touching anything. Now: POST on → compute_bool("garden_snn") False;
    GET reports active; POST clear → override gone again.
    """
    from core.system.config.magic_numbers import (
        clear_emergency_compute,
        compute_bool,
        get_emergency_override,
    )

    client = TestClient(app)
    try:
        r = client.post("/api/v1/system/emergency")
        assert r.status_code == 200
        j = r.json()
        assert j["status"] == "emergency_active"
        assert j["mode"] == "text-only"
        assert "action" in j
        assert "garden_snn" in j["disabled_features"]
        # The override must actually flip compute decisions.
        assert compute_bool("garden_snn", True) is False
        assert get_emergency_override()  # non-empty

        status = client.get("/api/v1/system/emergency")
        assert status.json()["status"] == "emergency_active"
        assert "garden_snn" in status.json()["disabled_features"]
    finally:
        clear_emergency_compute()

    after = client.get("/api/v1/system/emergency")
    assert after.json()["status"] == "emergency_inactive"
    assert not get_emergency_override()

    r_clear = client.post("/api/v1/system/emergency/clear")
    assert r_clear.status_code == 200
    assert r_clear.json()["status"] == "emergency_cleared"
