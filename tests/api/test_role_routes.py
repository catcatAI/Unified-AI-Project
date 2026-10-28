# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P3-1: the role catalogue is readable but not writable."""

import pytest
from ai.roleplay import Role, runtime
from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator
from api.routes.role_routes import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    orchestrator = MultiRoleOrchestrator()
    orchestrator.register(Role(role_id="main", display_name="Angela", context_scope="shared"))
    orchestrator.register(
        Role(role_id="role_b", display_name="Gemma 角色", backend_slot="llamacpp-gemma")
    )
    runtime.set_role_orchestrator(orchestrator)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client
    runtime.reset_role_orchestrator()


def test_lists_roles_with_their_binding(client):
    response = client.get("/roles")
    assert response.status_code == 200
    roles = {r["role_id"]: r for r in response.json()["roles"]}
    assert set(roles) == {"main", "role_b"}
    assert roles["role_b"]["backend_slot"] == "llamacpp-gemma"
    assert roles["role_b"]["memory_namespace"] == "role_b"
    assert roles["main"]["context_scope"] == "shared"


def test_no_mutation_endpoint_exists(client):
    assert client.post("/roles", json={"role_id": "role_z"}).status_code in (404, 405)
