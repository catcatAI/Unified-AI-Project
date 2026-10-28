# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P2-5: HTTP-level multi-role chat — the route layer actually passes role_id.

The pipeline is stubbed (it needs an LLM backend); everything above it is real:
TestClient → FastAPI route → role resolution → response shape. The stub
deliberately calls the real `_apply_role_binding`, so an unknown role fails with
the same 400 production would return.
"""

import pytest
from ai.roleplay import Role, runtime
from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator
from api.routes import chat_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def registry():
    orchestrator = MultiRoleOrchestrator()
    orchestrator.register(Role(role_id="main", display_name="Angela", context_scope="shared"))
    orchestrator.register(
        Role(role_id="role_b", display_name="Gemma 角色", backend_slot="llamacpp-gemma")
    )
    orchestrator.register(Role(role_id="role_c", display_name="Qwen 角色"))
    runtime.set_role_orchestrator(orchestrator)
    yield orchestrator
    runtime.reset_role_orchestrator()


@pytest.fixture()
def client(monkeypatch, registry):
    captured = []

    async def fake_handle(**kwargs):
        chat_routes._apply_role_binding(kwargs.get("extra_context") or {})
        captured.append(kwargs)
        role_id = (kwargs.get("extra_context") or {}).get("role_id", "main")
        return {"response_text": f"reply:{role_id}", "backend": "fake"}

    monkeypatch.setattr(chat_routes, "_handle_chat_request", fake_handle)
    app = FastAPI()
    app.include_router(chat_routes.router)
    with TestClient(app) as test_client:
        yield test_client, captured


def test_unified_passes_role_id_through(client):
    http, captured = client
    response = http.post("/chat/unified", json={"message": "hi", "role_id": "role_b"})
    assert response.status_code == 200
    assert response.json()["response_text"] == "reply:role_b"
    assert captured[0]["extra_context"]["role_id"] == "role_b"


def test_unified_without_role_stays_single_persona(client):
    http, captured = client
    response = http.post("/chat/unified", json={"message": "hi"})
    assert response.status_code == 200
    assert "role_id" not in captured[0]["extra_context"]


def test_unified_unknown_role_is_400(client):
    http, captured = client
    response = http.post("/chat/unified", json={"message": "hi", "role_id": "nobody"})
    assert response.status_code == 400
    assert captured == []


def test_group_asks_every_role_and_separates_sessions(client):
    http, captured = client
    response = http.post("/chat/group", json={"message": "hi", "role_ids": ["main", "role_b"]})
    assert response.status_code == 200
    body = response.json()
    assert body["role_ids"] == ["main", "role_b"]
    assert set(body["replies"]) == {"main", "role_b"}
    assert body["replies"]["role_b"]["response_text"] == "reply:role_b"
    sessions = [call["session_id"] for call in captured]
    assert sessions == [f"{body['session_id']}::main", f"{body['session_id']}::role_b"]


def test_group_dedupes_roles(client):
    http, captured = client
    response = http.post(
        "/chat/group", json={"message": "hi", "role_ids": ["role_b", "role_b", "role_c"]}
    )
    assert response.status_code == 200
    assert response.json()["role_ids"] == ["role_b", "role_c"]
    assert len(captured) == 2


def test_group_rejects_more_than_the_cap(client):
    http, captured = client
    response = http.post(
        "/chat/group",
        json={"message": "hi", "role_ids": ["main", "role_b", "role_c", "role_d", "role_e"]},
    )
    assert response.status_code == 400
    assert captured == []


@pytest.mark.parametrize("payload", [{"message": "hi"}, {"message": "hi", "role_ids": []}])
def test_group_requires_roles(client, payload):
    http, _ = client
    assert http.post("/chat/group", json=payload).status_code == 400


def test_group_unknown_role_fails_before_answering(client):
    http, captured = client
    response = http.post("/chat/group", json={"message": "hi", "role_ids": ["main", "nobody"]})
    assert response.status_code == 400
    assert len(captured) == 1  # "main" answered, the unknown role stopped the turn


def test_group_accepts_a_roles_alias(client):
    http, captured = client
    response = http.post("/chat/group", json={"message": "hi", "roles": ["role_c"]})
    assert response.status_code == 200
    assert captured[0]["extra_context"]["role_id"] == "role_c"
