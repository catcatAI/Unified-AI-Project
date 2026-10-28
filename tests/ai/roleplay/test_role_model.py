# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Unit tests for the Phase 0 multi-role data model (Role / RoleContext)."""

import pytest
from ai.persona.persona_engine import PersonaState
from ai.roleplay import DEFAULT_TOKEN_BUDGET, ContextScope, Role, RoleContext


# --------------------------------------------------------------------------
# ContextScope
# --------------------------------------------------------------------------
def test_context_scope_values():
    assert ContextScope.SHARED.value == "shared"
    assert ContextScope.PRIVATE.value == "private"
    assert ContextScope.HYBRID.value == "hybrid"


def test_context_scope_is_str_enum():
    assert ContextScope("hybrid") is ContextScope.HYBRID
    assert ContextScope.SHARED == "shared"


# --------------------------------------------------------------------------
# Role
# --------------------------------------------------------------------------
def test_role_defaults():
    role = Role(role_id="role_b", display_name="Gemma 角色")
    assert role.context_scope is ContextScope.PRIVATE
    assert role.shared_memory_read is True
    assert role.shared_memory_write is False
    assert role.backend_slot is None
    assert role.temperature_override is None


def test_role_namespace_defaults_to_role_id():
    assert Role(role_id="role_c", display_name="Qwen 角色").memory_namespace == "role_c"


def test_role_keeps_explicit_namespace():
    role = Role(role_id="role_c", display_name="Q", memory_namespace="ns_qwen")
    assert role.memory_namespace == "ns_qwen"


def test_role_rejects_empty_id():
    with pytest.raises(ValueError):
        Role(role_id="   ", display_name="x")


def test_role_rejects_write_without_read():
    with pytest.raises(ValueError):
        Role(role_id="r", display_name="r", shared_memory_read=False, shared_memory_write=True)


def test_role_rejects_out_of_range_temperature():
    with pytest.raises(ValueError):
        Role(role_id="r", display_name="r", temperature_override=0.0)
    with pytest.raises(ValueError):
        Role(role_id="r", display_name="r", temperature_override=2.5)


def test_role_rejects_non_positive_max_tokens():
    with pytest.raises(ValueError):
        Role(role_id="r", display_name="r", max_tokens_override=0)


def test_role_display_name_falls_back_to_id():
    assert Role(role_id="role_b", display_name="  ").display_name == "role_b"


def test_role_persona_state_is_per_instance():
    a = Role(role_id="a", display_name="A")
    b = Role(role_id="b", display_name="B")
    a.persona_state.display_name = "changed"
    assert b.persona_state.display_name == "Angela"
    assert isinstance(b.persona_state, PersonaState)


def test_role_resolved_backend_forces_slot():
    role = Role(role_id="role_b", display_name="B", backend_slot="llamacpp-gemma")
    assert role.resolved_backend("deepseek-flash") == "llamacpp-gemma"


def test_role_resolved_backend_falls_back_to_active():
    role = Role(role_id="main", display_name="Angela")
    assert role.resolved_backend("deepseek-flash") == "deepseek-flash"


def test_primary_role_flag():
    assert Role(role_id="main", display_name="A", context_scope=ContextScope.SHARED).is_primary
    assert not Role(role_id="role_b", display_name="B").is_primary


def test_role_dict_roundtrip():
    role = Role(
        role_id="role_b",
        display_name="Gemma 角色",
        backend_slot="llamacpp-gemma",
        context_scope=ContextScope.HYBRID,
        temperature_override=0.6,
        max_tokens_override=512,
    )
    clone = Role.from_dict(role.to_dict())
    assert clone == role


def test_role_from_dict_parses_scope_string():
    role = Role.from_dict({"role_id": "main", "display_name": "Angela", "context_scope": "shared"})
    assert role.context_scope is ContextScope.SHARED


def test_role_from_dict_ignores_unknown_keys():
    role = Role.from_dict({"role_id": "r", "display_name": "R", "unknown": 1})
    assert role.role_id == "r"


# --------------------------------------------------------------------------
# RoleContext
# --------------------------------------------------------------------------
def test_context_default_visible_to_is_self():
    assert RoleContext(role_id="role_b").visible_to == {"role_b"}


def test_context_default_budget():
    assert RoleContext(role_id="r").token_budget == DEFAULT_TOKEN_BUDGET


def test_context_rejects_empty_role_id():
    with pytest.raises(ValueError):
        RoleContext(role_id="")


def test_context_rejects_zero_budget():
    with pytest.raises(ValueError):
        RoleContext(role_id="r", token_budget=0)


def test_merged_includes_own_overlay():
    ctx = RoleContext(role_id="role_b")
    ctx.add_private({"role": "user", "content": "秘密"})
    assert [m["content"] for m in ctx.merged_messages()] == ["秘密"]


def test_merged_hides_overlay_from_other_role():
    ctx = RoleContext(role_id="role_b")
    ctx.add_private({"role": "user", "content": "秘密"})
    assert ctx.merged_messages(viewer="role_c") == []


def test_merged_filters_shared_messages_by_visibility():
    ctx = RoleContext(role_id="role_b")
    ctx.add_shared({"content": "只給 B"}, visible_to={"role_b"})
    ctx.add_shared({"content": "只給 C"}, visible_to={"role_c"})
    assert [m["content"] for m in ctx.merged_messages("role_b")] == ["只給 B"]
    assert [m["content"] for m in ctx.merged_messages("role_c")] == ["只給 C"]


def test_merged_public_message_visible_to_all():
    ctx = RoleContext(role_id="role_b")
    ctx.add_shared({"content": "公開"})
    assert ctx.merged_messages("role_c") == [{"content": "公開"}]


def test_merged_order_shared_then_overlay():
    ctx = RoleContext(role_id="main")
    ctx.add_shared({"content": "base"})
    ctx.add_private({"content": "overlay"})
    assert [m["content"] for m in ctx.merged_messages()] == ["base", "overlay"]


def test_shared_base_is_reference_not_copy():
    ctx = RoleContext(role_id="main")
    shared = ctx.shared_base
    ctx.add_shared({"content": "new"})
    assert shared is ctx.shared_base
    assert len(shared) == 1


def test_add_private_widens_visibility():
    ctx = RoleContext(role_id="role_b")
    ctx.add_private({"content": "給 C 看"}, visible_to=["role_c"])
    assert "role_c" in ctx.visible_to
    assert ctx.merged_messages("role_c") == [{"content": "給 C 看"}]


def test_estimate_tokens_scales_with_content():
    ctx = RoleContext(role_id="r")
    assert ctx.estimate_tokens() == 0
    ctx.add_private({"content": "x" * 400})
    assert ctx.estimate_tokens() == 100


def test_estimate_tokens_validates_chars_per_token():
    with pytest.raises(ValueError):
        RoleContext(role_id="r").estimate_tokens(chars_per_token=0)


def test_is_over_budget_boundary():
    ctx = RoleContext(role_id="r", token_budget=10)
    ctx.add_private({"content": "x" * 40})  # exactly 10 tokens
    assert ctx.is_over_budget() is False
    ctx.add_private({"content": "y" * 4})
    assert ctx.is_over_budget() is True
