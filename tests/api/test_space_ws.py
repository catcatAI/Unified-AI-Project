# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""Space WebSocket: snapshot on join, action broadcast, tolerant error replies."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.space import space_service as mod
from services.space.space_service import SpaceService
from services.space.space_ws import space_ws_handler


@pytest.fixture()
def client():
    service = SpaceService()
    service.load_room({"room_id": "studio_a"})
    service.spawn({"role_id": "main", "avatar_id": "angela_base", "position": [5.5, 0]})
    mod.reset_space_service()
    mod.set_space_service(service)
    app = FastAPI()
    app.websocket("/ws/space")(space_ws_handler)
    with TestClient(app) as test_client:
        yield test_client
    mod.reset_space_service()


def test_join_receives_a_snapshot(client):
    with client.websocket_connect("/ws/space?room_id=studio_a") as ws:
        message = ws.receive_json()
    assert message["type"] == "space.snapshot"
    assert message["data"]["room_id"] == "studio_a"
    assert [a["role_id"] for a in message["data"]["actors"]] == ["main"]


def test_say_action_is_broadcast_back(client):
    with client.websocket_connect("/ws/space") as ws:
        ws.receive_json()  # initial snapshot
        ws.send_json(
            {"type": "space.action", "data": {"type": "say", "actor_id": "main", "text": "hi"}}
        )
        message = ws.receive_json()
    assert message["type"] == "space.snapshot"
    actor = message["data"]["actors"][0]
    assert actor["speech"] == {"text": "hi"}


def test_bad_action_returns_an_error_without_dropping_the_socket(client):
    with client.websocket_connect("/ws/space") as ws:
        ws.receive_json()
        ws.send_json({"type": "space.action", "data": {"type": "backflip", "actor_id": "main"}})
        error = ws.receive_json()
        assert error["type"] == "space.error"
        assert "backflip" in error["message"]

        # connection still usable
        ws.send_json({"type": "space.ping"})
        assert ws.receive_json() == {"type": "space.pong"}


def test_malformed_json_is_reported(client):
    with client.websocket_connect("/ws/space") as ws:
        ws.receive_json()
        ws.send_text("{not json")
        error = ws.receive_json()
    assert error["type"] == "space.error"
    assert "malformed" in error["message"]


def test_unknown_message_type_is_reported(client):
    with client.websocket_connect("/ws/space") as ws:
        ws.receive_json()
        ws.send_json({"type": "space.dance"})
        error = ws.receive_json()
    assert "unknown message type" in error["message"]
