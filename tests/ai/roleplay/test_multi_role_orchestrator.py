# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Unit tests for MultiRoleOrchestrator (P2-1)."""

import pytest
from ai.roleplay import ContextScope, Role
from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator


class FakeLLM:
    def __init__(self, reply="ok"):
        self.reply = reply
        self.calls = []

    async def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.reply

    @property
    def last(self):
        return self.calls[-1]


class FakeMemory:
    def __init__(self):
        self.entries = []

    async def __call__(self, **kwargs):
        self.entries.append(kwargs)


def role(role_id, **kwargs):
    return Role(role_id=role_id, display_name=role_id, **kwargs)


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------
def test_register_returns_agent_and_tracks_role():
    orch = MultiRoleOrchestrator(llm_service=FakeLLM())
    agent = orch.register(role("role_b"))
    assert orch.get("role_b") is agent
    assert orch.roles == ["role_b"]


def test_register_duplicate_role_id_raises():
    orch = MultiRoleOrchestrator()
    orch.register(role("role_b"))
    with pytest.raises(ValueError):
        orch.register(role("role_b"))


def test_register_second_shared_role_raises():
    orch = MultiRoleOrchestrator()
    orch.register(role("main", context_scope=ContextScope.SHARED))
    with pytest.raises(ValueError):
        orch.register(role("main2", context_scope=ContextScope.SHARED))


def test_primary_role_id_tracks_shared_role():
    orch = MultiRoleOrchestrator()
    orch.register(role("role_b"))
    assert orch.primary_role_id is None
    orch.register(role("main", context_scope=ContextScope.SHARED))
    assert orch.primary_role_id == "main"


def test_unregister_removes_role():
    orch = MultiRoleOrchestrator()
    orch.register(role("role_b"))
    assert orch.unregister("role_b") is True
    assert orch.roles == []
    assert orch.unregister("role_b") is False


def test_register_inherits_orchestrator_services():
    llm, memory = FakeLLM(), FakeMemory()
    orch = MultiRoleOrchestrator(llm_service=llm, memory_writer=memory)
    agent = orch.register(role("role_b"))
    assert agent.llm_service is llm
    assert agent.memory_writer is memory


def test_per_role_service_overrides_orchestrator_default():
    default_llm, role_llm = FakeLLM(), FakeLLM("專屬")
    orch = MultiRoleOrchestrator(llm_service=default_llm)
    agent = orch.register(role("role_b"), llm_service=role_llm)
    assert agent.llm_service is role_llm


# --------------------------------------------------------------------------
# turns
# --------------------------------------------------------------------------
async def test_turn_routes_to_the_named_role():
    orch = MultiRoleOrchestrator(llm_service=FakeLLM("B 的回覆"))
    orch.register(role("role_b"))
    result = await orch.turn("role_b", "hi")
    assert result["reply"] == "B 的回覆"
    assert result["role_id"] == "role_b"


async def test_turn_unknown_role_raises():
    orch = MultiRoleOrchestrator()
    with pytest.raises(KeyError):
        await orch.turn("nobody", "hi")


async def test_turn_applies_default_backend():
    llm = FakeLLM()
    orch = MultiRoleOrchestrator(llm_service=llm, default_backend="deepseek-flash")
    orch.register(role("role_b"))
    await orch.turn("role_b", "hi")
    assert llm.last["backend_slot"] == "deepseek-flash"


async def test_role_slot_beats_orchestrator_default():
    llm = FakeLLM()
    orch = MultiRoleOrchestrator(llm_service=llm, default_backend="deepseek-flash")
    orch.register(role("role_b", backend_slot="llamacpp-gemma"))
    result = await orch.turn("role_b", "hi")
    assert result["backend_slot"] == "llamacpp-gemma"


async def test_group_turn_asks_every_role_in_order():
    llm = FakeLLM("回覆")
    orch = MultiRoleOrchestrator(llm_service=llm)
    orch.register(role("role_b"))
    orch.register(role("role_c"))
    results = await orch.group_turn("大家早")
    assert list(results) == ["role_b", "role_c"]
    assert len(llm.calls) == 2


async def test_group_turn_accepts_explicit_subset():
    llm = FakeLLM()
    orch = MultiRoleOrchestrator(llm_service=llm)
    orch.register(role("role_b"))
    orch.register(role("role_c"))
    results = await orch.group_turn("hi", role_ids=["role_c"])
    assert list(results) == ["role_c"]
    assert len(llm.calls) == 1


async def test_group_turn_empty_registry_returns_empty():
    assert await MultiRoleOrchestrator().group_turn("hi") == {}


async def test_group_turn_propagates_per_role_memory_namespace():
    memory = FakeMemory()
    orch = MultiRoleOrchestrator(llm_service=FakeLLM("回覆"), memory_writer=memory)
    orch.register(role("role_b"))
    orch.register(role("role_c", memory_namespace="ns_qwen"))
    await orch.group_turn("hi")
    namespaces = [entry["namespace"] for entry in memory.entries]
    assert namespaces == ["role_b", "ns_qwen"]


# --------------------------------------------------------------------------
# shared vs private in a group turn
# --------------------------------------------------------------------------
async def test_primary_reply_is_visible_to_other_roles():
    orch = MultiRoleOrchestrator(llm_service=FakeLLM("主 AI 的回覆"))
    primary = orch.register(role("main", context_scope=ContextScope.SHARED))
    secondary = orch.register(role("role_b"))
    await orch.group_turn("hi")
    seen = [m["content"] for m in primary.context.merged_messages(viewer="role_b")]
    assert seen == ["hi", "主 AI 的回覆"]
    # 私有角色之間互不相見
    assert secondary.context.merged_messages(viewer="main") == []


async def test_private_role_reply_stays_private():
    orch = MultiRoleOrchestrator(llm_service=FakeLLM("B 的秘密"))
    primary = orch.register(role("main", context_scope=ContextScope.SHARED))
    secondary = orch.register(role("role_b"))
    await orch.group_turn("hi")
    assert secondary.context.shared_base == []  # 私有角色不寫共享基底
    assert primary.context.private_overlay == []  # 主 AI 看不到 B 的私有訊息
