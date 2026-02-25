import random
import numpy as np
from fastapi.testclient import TestClient

from src.services.main_api_server import app
from src.api.v1.endpoints import audio as audio_mod
from src.services.audio_service import AudioService


def setup_module(module):
    random.seed(1234)
    np.random.seed(1234)
    audio_mod._audio_service = AudioService(config={"sampler_config": {"particle_count": 5}})


def test_audio_scan_basic_response_structure():
    client = TestClient(app)
    payload = b"\x00" * 2048
    resp = client.post("/api/v1/audio/scan", data=payload, headers={"Content-Type": "application/octet-stream"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert isinstance(data["timestamp"], str)

    scene = data["scene_stats"]

    assert isinstance(data["detected_sources_count"], int)
    assert data["detected_sources_count"] == scene["particle_count"]
    assert data["detected_sources_count"] > 0
    assert data["attention_mode"] in {"SCAN", "FOCUS", "TRACK", "IDLE"}
    assert scene["status"] in {"idle", "active"}
    assert 0.0 <= float(scene.get("average_intensity", 0.0)) <= 1.0

    focus = data.get("current_focus")
    if focus is not None:
        assert set(["profile_id", "name", "label", "intensity"]).issubset(focus.keys())
        assert isinstance(focus["profile_id"], str)
        assert isinstance(focus["name"], str)
        assert isinstance(focus["label"], str)
        assert isinstance(focus["intensity"], (int, float))


def test_audio_register_user_returns_profile():
    client = TestClient(app)
    payload = b"\x01" * 1024
    resp = client.post("/api/v1/audio/register_user", data=payload, headers={"Content-Type": "application/octet-stream"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert isinstance(data["profile_id"], str)
    assert data["name"] == "User"


def test_audio_control_post_and_get_agree_on_enabled_flag():
    client = TestClient(app)

    # POST control
    resp_post = client.post("/api/v1/audio/control", json={"enabled": False})
    assert resp_post.status_code == 200
    jp = resp_post.json()
    assert jp == {"status": "success", "module": "audio", "enabled": False, "mode": "post_method"}

    # GET control
    resp_get = client.get("/api/v1/audio/control", params={"enabled": True})
    assert resp_get.status_code == 200
    jg = resp_get.json()
    assert jg == {"status": "success", "module": "audio", "enabled": True, "mode": "get_method"}
