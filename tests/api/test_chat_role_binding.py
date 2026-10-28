# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P2-4: chat context → role binding (slot / namespace / trace id)."""

import pytest
from ai.roleplay import Role, runtime
from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator
from api.routes import chat_routes
from api.routes.chat_routes import MAX_GROUP_ROLES, _apply_role_binding
from fastapi import HTTPException


@pytest.fixture()
def registry():
    orchestrator = MultiRoleOrchestrator()
    orchestrator.register(Role(role_id="main", display_name="Angela", context_scope="shared"))
    orchestrator.register(
        Role(
            role_id="role_b",
            display_name="Gemma 角色",
            backend_slot="llamacpp-gemma",
            memory_namespace="ns_b",
        )
    )
    runtime.set_role_orchestrator(orchestrator)
    yield orchestrator
    runtime.reset_role_orchestrator()


def test_no_role_id_changes_nothing():
    context = {"user_id": "u1"}
    _apply_role_binding(context)
    assert "_role_id" not in context
    assert "_memory_namespace" not in context


def test_blank_role_id_is_ignored():
    context = {"role_id": "   "}
    _apply_role_binding(context)
    assert "_role_id" not in context


def test_role_binding_sets_slot_namespace_and_trace(registry):
    context = {"role_id": "role_b"}
    _apply_role_binding(context)
    assert context["_role_id"] == "role_b"
    assert context["_force_backend_slot"] == "llamacpp-gemma"
    assert context["_memory_namespace"] == "ns_b"
    assert context["_role_display_name"] == "Gemma 角色"


def test_primary_role_has_no_forced_slot(registry):
    context = {"role_id": "main"}
    _apply_role_binding(context)
    assert context["_force_backend_slot"] is None
    assert context["_memory_namespace"] == "main"


def test_unknown_role_is_a_400_not_a_silent_angela(registry):
    with pytest.raises(HTTPException) as excinfo:
        _apply_role_binding({"role_id": "nobody"})
    assert excinfo.value.status_code == 400
    assert "unknown role" in str(excinfo.value.detail)


def test_group_turn_is_bounded():
    assert MAX_GROUP_ROLES >= 2


def test_group_route_is_registered():
    paths = {route.path for route in chat_routes.router.routes}
    assert "/chat/group" in paths
