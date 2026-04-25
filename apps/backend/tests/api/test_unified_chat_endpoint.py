import os

from fastapi.testclient import TestClient

# Avoid GUI backend import during headless CI/test environments
os.environ.setdefault("PYSTRAY_BACKEND", "dummy")

from src.services import main_api_server as api_module
from src.services.main_api_server import app


def test_unified_chat_endpoint_returns_context_defaults():
    client = TestClient(app)
    response = client.post("/api/v1/chat/unified", json={"message": "hello"})
    assert response.status_code == 200
    payload = response.json()

    assert "context" in payload
    assert payload["context"]["tenant_id"] == "default_tenant"
    assert payload["context"]["persona_id"] == "angela_default"
    assert payload["context"]["client_id"] == "unknown_client"
    assert payload["session_namespace"].startswith("default_tenant::angela_default::")
    assert "migration_note" in payload


def test_unified_chat_endpoint_accepts_explicit_context():
    client = TestClient(app)
    body = {
        "message": "ping",
        "tenant_id": "tenant_alpha",
        "persona_id": "angela_desktop",
        "user_id": "desktop_user",
        "client_id": "desktop_electron",
        "session_id": "tenant_alpha::angela_desktop::fixed",
    }
    response = client.post("/api/v1/chat/unified", json=body)
    assert response.status_code == 200
    payload = response.json()

    assert payload["context"]["tenant_id"] == "tenant_alpha"
    assert payload["context"]["persona_id"] == "angela_desktop"
    assert payload["context"]["user_id"] == "desktop_user"
    assert payload["context"]["client_id"] == "desktop_electron"
    assert payload["session_id"] == "tenant_alpha::angela_desktop::fixed"
    assert payload["session_namespace"] == "tenant_alpha::angela_desktop::fixed"


def test_unified_chat_session_isolation_by_persona():
    client = TestClient(app)
    api_module.sessions.clear()

    shared_session_id = "shared-session"

    a = {
        "message": "hello from A",
        "tenant_id": "tenant_alpha",
        "persona_id": "persona_A",
        "session_id": shared_session_id,
    }
    b = {
        "message": "hello from B",
        "tenant_id": "tenant_alpha",
        "persona_id": "persona_B",
        "session_id": shared_session_id,
    }

    res_a = client.post("/api/v1/chat/unified", json=a)
    res_b = client.post("/api/v1/chat/unified", json=b)

    assert res_a.status_code == 200
    assert res_b.status_code == 200
    payload_a = res_a.json()
    payload_b = res_b.json()

    assert payload_a["session_namespace"] == "tenant_alpha::persona_A::shared-session"
    assert payload_b["session_namespace"] == "tenant_alpha::persona_B::shared-session"
    assert payload_a["session_namespace"] != payload_b["session_namespace"]


def test_unified_chat_default_session_id_is_not_double_prefixed():
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/unified",
        json={"message": "hello", "tenant_id": "t1", "persona_id": "p1"},
    )
    assert response.status_code == 200
    payload = response.json()

    # Public session id stays simple for frontend compatibility
    assert payload["session_id"].startswith("sess-")
    # Internal namespace key contains exactly one namespace prefix
    assert payload["session_namespace"].startswith("t1::p1::")
    assert "::t1::p1::" not in payload["session_namespace"]
