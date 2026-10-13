import numpy as np
from api.v1.endpoints import vision as vision_mod
from fastapi.testclient import TestClient
from services.main_api_server import app
from services.vision_service import VisionService


def setup_module(module):
    np.random.seed(7)
    # keep default service; vision endpoints use internal VisionService instance
    # If needed, we could override like: vision_mod._vision_service = VisionService()


def test_vision_sampling_structure_and_consistency():
    client = TestClient(app)
    body = {
        "center": [0.4, 0.6],
        "scale": 1.2,
        "deformation": 0.1,
        "distribution": "GAUSSIAN",
    }
    r = client.post("/api/v1/vision/sampling", json=body)
    assert r.status_code == 200
    j = r.json()

    assert j["status"] == "success"
    assert isinstance(j["timestamp"], str)
    stats = j["sampling_stats"]
    assert set(["status", "sample_count", "focus_distribution"]).issubset(stats.keys())
    assert isinstance(stats["sample_count"], int)
    assert stats["sample_count"] > 0
    # internal consistency
    assert j["attention_mode"] in {"SCAN", "FOCUS", "TRACK", "IDLE"}


def test_vision_perceive_returns_next_focus_and_memory_stats():
    client = TestClient(app)
    img = b"\x89PNG\r\n" + (b"\x00" * 1024)
    r = client.post(
        "/api/v1/vision/perceive", content=img, headers={"Content-Type": "application/octet-stream"}
    )
    assert r.status_code == 200
    j = r.json()

    assert j["status"] == "success"
    assert isinstance(j["perceived_objects_count"], int)
    assert "next_focus_point" in j and isinstance(j["next_focus_point"], list)
    assert "memory_stats" in j and isinstance(j["memory_stats"].get("total_remembered", 0), int)


def test_vision_control_post_get_match():
    client = TestClient(app)
    rp = client.post("/api/v1/vision/control", json={"enabled": False})
    assert rp.status_code == 200
    assert rp.json() == {
        "status": "success",
        "module": "vision",
        "enabled": False,
        "requested": False,
    }

    rg = client.get("/api/v1/vision/control", params={"enabled": True})
    assert rg.status_code == 200
    assert rg.json() == {
        "status": "success",
        "module": "vision",
        "enabled": True,
        "requested": True,
    }


def test_vision_control_bare_get_is_a_read_not_a_write():
    """A status probe must not re-enable the module.

    The GET handler used to default ``enabled=True`` and call ``set_enabled``
    unconditionally, so ``POST /mobile/module-control {"enabled": false}``
    looked broken: the very next ``GET /vision/control`` turned vision back on.
    """
    client = TestClient(app)
    try:
        assert (
            client.post("/api/v1/vision/control", json={"enabled": False}).json()["enabled"]
            is False
        )

        probe = client.get("/api/v1/vision/control")
        assert probe.status_code == 200
        j = probe.json()
        assert j["enabled"] is False, "bare GET must not mutate module state"
        assert j["requested"] is False
        assert j["module"] == "vision"

        # an explicit query param still writes (documented GET control form)
        explicit = client.get("/api/v1/vision/control", params={"enabled": True})
        assert explicit.status_code == 200
        assert explicit.json()["enabled"] is True
    finally:
        client.post("/api/v1/vision/control", json={"enabled": True})
