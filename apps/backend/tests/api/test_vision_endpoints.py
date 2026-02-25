import numpy as np
from fastapi.testclient import TestClient

from src.services.main_api_server import app
from src.api.v1.endpoints import vision as vision_mod
from src.services.vision_service import VisionService


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
    r = client.post("/api/v1/vision/perceive", data=img, headers={"Content-Type": "application/octet-stream"})
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
    assert rp.json() == {"status": "success", "module": "vision", "enabled": False, "mode": "post_method"}

    rg = client.get("/api/v1/vision/control", params={"enabled": True})
    assert rg.status_code == 200
    assert rg.json() == {"status": "success", "module": "vision", "enabled": True, "mode": "get_method"}
