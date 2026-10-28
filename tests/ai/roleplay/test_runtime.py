# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Role registry runtime: config loading, defaults, and unknown-id behaviour."""

import pytest
from ai.roleplay import Role, runtime
from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator


def write_roles(tmp_path, text):
    cfg = tmp_path / "roles.yaml"
    cfg.write_text(text, encoding="utf-8")
    return cfg


def test_load_roles_reads_scopes_and_slots(tmp_path):
    cfg = write_roles(
        tmp_path,
        """
roles:
  - role_id: main
    display_name: Angela
    context_scope: shared
  - role_id: role_b
    display_name: B
    backend_slot: llamacpp-gemma
    memory_namespace: ns_b
""",
    )
    roles = runtime.load_roles(cfg)
    assert [r.role_id for r in roles] == ["main", "role_b"]
    assert roles[0].context_scope.value == "shared"
    assert roles[1].backend_slot == "llamacpp-gemma"
    assert roles[1].memory_namespace == "ns_b"


def test_missing_config_disables_role_play(tmp_path):
    assert runtime.load_roles(tmp_path / "nope.yaml") == []


def test_invalid_role_specs_are_skipped_not_fatal(tmp_path):
    cfg = write_roles(
        tmp_path,
        """
roles:
  - role_id: ""
    display_name: broken
  - role_id: role_b
    display_name: B
""",
    )
    roles = runtime.load_roles(cfg)
    assert [r.role_id for r in roles] == ["role_b"]


def test_env_override_points_at_another_config(tmp_path, monkeypatch):
    cfg = write_roles(tmp_path, "roles: []\n")
    monkeypatch.setenv("ANGELA_ROLES_CONFIG", str(cfg))
    assert runtime.default_config_path() == cfg


def test_shipped_config_registers_three_roles():
    roles = runtime.load_roles()
    assert [r.role_id for r in roles] == ["main", "role_b", "role_c"]
    assert roles[1].backend_slot == "llamacpp-gemma"


@pytest.fixture()
def registry():
    orchestrator = MultiRoleOrchestrator()
    orchestrator.register(Role(role_id="main", display_name="Angela", context_scope="shared"))
    orchestrator.register(
        Role(
            role_id="role_b",
            display_name="B",
            backend_slot="llamacpp-gemma",
            memory_namespace="ns_b",
        )
    )
    runtime.set_role_orchestrator(orchestrator)
    yield orchestrator
    runtime.reset_role_orchestrator()


def test_resolve_role_returns_the_configured_role(registry):
    role = runtime.resolve_role("role_b")
    assert role is not None
    assert role.memory_namespace == "ns_b"


def test_resolve_role_unknown_returns_none(registry):
    assert runtime.resolve_role("nobody") is None
    assert runtime.resolve_role("  ") is None


def test_get_orchestrator_is_lazy_and_cached(monkeypatch):
    runtime.reset_role_orchestrator()
    monkeypatch.setattr(runtime, "load_roles", lambda path=None: [])
    first = runtime.get_role_orchestrator()
    assert runtime.get_role_orchestrator() is first
    runtime.reset_role_orchestrator()
