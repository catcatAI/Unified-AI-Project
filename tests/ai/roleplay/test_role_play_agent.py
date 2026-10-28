# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Unit tests for RolePlayAgent (P1-1/P1-2) with a fake LLM and memory writer."""

import pytest
from ai.agents.base.base_agent import BaseAgent
from ai.persona.persona_engine import get_persona_engine
from ai.roleplay import ContextScope, Role
from ai.roleplay.role_play_agent import RolePlayAgent


class FakeLLM:
    """Records the kwargs it was called with and returns a canned reply."""

    def __init__(self, reply="我是角色 B。", raises=None):
        self.reply = reply
        self.raises = raises
        self.calls = []

    async def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.raises is not None:
            raise self.raises
        return self.reply

    @property
    def last(self):
        return self.calls[-1]


class FakeMemory:
    def __init__(self, raises=None):
        self.entries = []
        self.raises = raises

    async def __call__(self, **kwargs):
        if self.raises is not None:
            raise self.raises
        self.entries.append(kwargs)


def make_role(role_id="role_b", **kwargs):
    return Role(role_id=role_id, display_name="Gemma 角色", **kwargs)


def make_agent(role=None, **kwargs):
    llm = kwargs.pop("llm", FakeLLM())
    memory = kwargs.pop("memory", FakeMemory())
    return (
        RolePlayAgent(role or make_role(), llm_service=llm, memory_writer=memory, **kwargs),
        llm,
        memory,
    )


# --------------------------------------------------------------------------
# identity / wiring
# --------------------------------------------------------------------------
def test_agent_is_a_base_agent():
    agent, _, _ = make_agent()
    assert isinstance(agent, BaseAgent)


def test_agent_id_is_derived_from_role():
    agent, _, _ = make_agent(make_role("role_c"))
    assert agent.agent_id == "roleplay-role_c"
    assert "role_c" in agent.agent_name


def test_capabilities_expose_role_play():
    agent, _, _ = make_agent()
    assert agent.capabilities[0]["name"] == "role_play_respond"


def test_agent_uses_its_own_persona_engine():
    agent, _, _ = make_agent(make_role("role_persona_test"))
    assert agent.persona_engine is get_persona_engine("role_persona_test")
    assert agent.persona_engine is not get_persona_engine()


def test_agent_context_starts_empty():
    agent, _, _ = make_agent()
    assert agent.context.merged_messages() == []


# --------------------------------------------------------------------------
# respond(): happy path
# --------------------------------------------------------------------------
async def test_respond_returns_reply():
    agent, _, _ = make_agent(llm=FakeLLM("早安，我是角色 B。"))
    result = await agent.respond("早安")
    assert result["status"] == "success"
    assert result["reply"] == "早安，我是角色 B。"
    assert result["role_id"] == "role_b"


async def test_respond_forces_role_backend_slot():
    role = make_role(backend_slot="llamacpp-gemma")
    agent, llm, _ = make_agent(role)
    result = await agent.respond("hi", active_backend="deepseek-flash")
    assert result["backend_slot"] == "llamacpp-gemma"
    assert llm.last["backend_slot"] == "llamacpp-gemma"


async def test_respond_falls_back_to_active_backend():
    agent, llm, _ = make_agent()
    result = await agent.respond("hi", active_backend="deepseek-flash")
    assert result["backend_slot"] == "deepseek-flash"
    assert llm.last["backend_slot"] == "deepseek-flash"


async def test_respond_passes_temperature_and_max_tokens_overrides():
    role = make_role(temperature_override=0.3, max_tokens_override=256)
    agent, llm, _ = make_agent(role)
    await agent.respond("hi")
    assert llm.last["temperature"] == 0.3
    assert llm.last["max_tokens"] == 256


async def test_respond_passes_none_when_no_overrides():
    agent, llm, _ = make_agent()
    await agent.respond("hi")
    assert llm.last["temperature"] is None
    assert llm.last["max_tokens"] is None


async def test_respond_system_prompt_carries_persona_and_role():
    agent, llm, _ = make_agent()
    await agent.respond("hi", al_state={"fatigue": 0.9, "stress": 0.1, "valence": 0.5})
    system = llm.last["messages"][0]
    assert system["role"] == "system"
    assert "[Tone: tired_yet_diligent]" in system["content"]
    assert "[Role: Gemma 角色]" in system["content"]


async def test_respond_reports_message_count():
    agent, llm, _ = make_agent()
    result = await agent.respond("hi")
    assert result["messages_sent"] == len(llm.last["messages"]) == 2  # system + user


# --------------------------------------------------------------------------
# context placement
# --------------------------------------------------------------------------
async def test_private_role_writes_into_overlay():
    agent, _, _ = make_agent()
    await agent.respond("hi")
    assert agent.context.shared_base == []
    assert [m["content"] for m in agent.context.private_overlay] == ["hi", "我是角色 B。"]


async def test_private_overlay_is_invisible_to_other_roles():
    agent, _, _ = make_agent()
    await agent.respond("秘密")
    assert agent.context.merged_messages(viewer="role_c") == []


async def test_shared_role_writes_into_shared_base():
    role = make_role("main", context_scope=ContextScope.SHARED)
    agent, _, _ = make_agent(role)
    await agent.respond("大家好")
    assert agent.context.private_overlay == []
    assert [m["content"] for m in agent.context.shared_base] == ["大家好", "我是角色 B。"]
    # 共享基底沒有 visible_to → 其他角色也看得到
    assert agent.context.merged_messages(viewer="role_c")[0]["content"] == "大家好"


async def test_private_role_exposes_over_budget_flag():
    agent, _, _ = make_agent(token_budget=1)
    result = await agent.respond("x" * 100)
    assert result["over_budget"] is True


# --------------------------------------------------------------------------
# memory namespace
# --------------------------------------------------------------------------
async def test_memory_write_uses_default_namespace():
    agent, _, memory = make_agent()
    await agent.respond("hi")
    assert memory.entries == [
        {"namespace": "role_b", "role_id": "role_b", "content": "我是角色 B。"}
    ]


async def test_memory_write_uses_explicit_namespace():
    role = make_role("role_c", memory_namespace="ns_qwen")
    agent, _, memory = make_agent(role)
    result = await agent.respond("hi")
    assert memory.entries[0]["namespace"] == "ns_qwen"
    assert result["memory_namespace"] == "ns_qwen"


async def test_memory_failure_does_not_break_the_reply():
    agent, _, _ = make_agent(memory=FakeMemory(raises=RuntimeError("ham down")))
    result = await agent.respond("hi")
    assert result["status"] == "success"
    assert result["reply"] == "我是角色 B。"


async def test_no_memory_writer_is_fine():
    agent = RolePlayAgent(make_role(), llm_service=FakeLLM(), memory_writer=None)
    assert (await agent.respond("hi"))["status"] == "success"


# --------------------------------------------------------------------------
# degraded paths
# --------------------------------------------------------------------------
async def test_missing_llm_reports_unavailable():
    agent = RolePlayAgent(make_role(), llm_service=None)
    result = await agent.respond("hi")
    assert result["status"] == "unavailable"
    assert result["reply"] is None


async def test_llm_failure_reports_error_and_keeps_overlay_clean():
    agent, _, _ = make_agent(llm=FakeLLM(raises=RuntimeError("backend down")))
    result = await agent.respond("hi")
    assert result["status"] == "error"
    assert "backend down" in result["error"]
    # 使用者的話留著（可重試），但沒有假的助理訊息
    assert [m["content"] for m in agent.context.private_overlay] == ["hi"]


async def test_empty_message_is_rejected():
    agent, _, _ = make_agent()
    with pytest.raises(ValueError):
        await agent.respond("   ")


# --------------------------------------------------------------------------
# response shapes accepted from the LLM layer
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("plain", "plain"),
        ({"content": "dict-content"}, "dict-content"),
        ({"text": "dict-text"}, "dict-text"),
        ({"reply": "dict-reply"}, "dict-reply"),
    ],
)
async def test_extract_text_shapes(raw, expected):
    assert RolePlayAgent._extract_text(raw) == expected


async def test_extract_text_from_object_with_content_attribute():
    class Resp:
        content = "object-content"

    assert RolePlayAgent._extract_text(Resp()) == "object-content"
