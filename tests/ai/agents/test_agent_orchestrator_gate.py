"""
ExecutionGate ownership for AgentOrchestrator (ownership hardening).

The orchestrator routes specialized agents; ExecutionGate is the single owner of
"may this action run". These tests pin that contract so a future change cannot
re-introduce unguarded agent execution (e.g. direct file_delete / code_execute).
"""

import pytest


class _FakeManager:
    def __init__(self):
        self.calls = []

    async def execute_agent(self, agent_name, task):
        self.calls.append((agent_name, task))

        class _Result:
            success = True
            result_data = {"status": "success", "message": "agent done"}
            error = None

        return _Result()


@pytest.fixture(autouse=True)
def _reset_gate_feedback():
    from ai.core.execution_gate import ExecutionGate

    ExecutionGate().reset_feedback_stats()
    yield
    ExecutionGate().reset_feedback_stats()


def test_read_class_agent_auto_executes():
    from ai.core.execution_gate import ExecutionGate

    decision = ExecutionGate().decide_agent_execution(
        intent="knowledge_query",
        agent_name="knowledge_graph_agent",
        user_message="查詢知識圖譜中的節點資料",
    )
    assert decision.action == "auto_execute"


def test_create_class_agent_auto_executes_when_clear():
    from ai.core.execution_gate import ExecutionGate

    # "create" is reversible (0.9) — outputs can be deleted — so a clear
    # generation request runs without a confirmation round trip.
    decision = ExecutionGate().decide_agent_execution(
        intent="image_generate",
        agent_name="image_generation_agent",
        user_message="生成一張城市夜景的圖片",
    )
    assert decision.action == "auto_execute"
    assert decision.action_type == "create"


def test_irreversible_agent_intent_always_confirms():
    from ai.core.execution_gate import ExecutionGate

    gate = ExecutionGate()
    for intent, agent in (
        ("file_delete", "file_ops"),
        ("code_execute", "code_exec"),
    ):
        decision = gate.decide_agent_execution(
            intent=intent,
            agent_name=agent,
            user_message="刪除 /tmp/all_of_the_project_files 並執行 python",
        )
        assert decision.action == "confirm_then_execute", intent
        assert decision.confirm_message


def test_unmapped_agent_intent_is_rejected():
    from ai.core.execution_gate import ExecutionGate

    decision = ExecutionGate().decide_agent_execution(
        intent="totally_unknown",
        agent_name="mystery_agent",
        user_message="做點什麼",
    )
    assert decision.action == "reject"


def test_confirm_agent_execution_authorizes_known_intent_only():
    from ai.core.execution_gate import ExecutionGate

    gate = ExecutionGate()
    allowed = gate.confirm_agent_execution("file_delete", "file_ops", "刪除檔案")
    assert allowed.action == "auto_execute"
    denied = gate.confirm_agent_execution("unknown_intent", "x", "y")
    assert denied.action == "reject"


@pytest.mark.asyncio
async def test_orchestrator_does_not_execute_blocked_agent():
    from ai.agents.agent_orchestrator import AgentOrchestrator

    manager = _FakeManager()
    orchestrator = AgentOrchestrator(agent_manager=manager)
    result = await orchestrator.route_task("刪除 /tmp/project_files", {})
    primary = result["results"][0]
    assert primary["gate_action"] == "confirm_then_execute"
    assert manager.calls == []


@pytest.mark.asyncio
async def test_orchestrator_executes_after_explicit_confirmation():
    from ai.agents.agent_orchestrator import AgentOrchestrator

    manager = _FakeManager()
    orchestrator = AgentOrchestrator(agent_manager=manager)
    result = await orchestrator.route_task(
        "生成 RTL 電路",
        {"_gate_confirmed_agent": "eda_agent", "_gate_confirmed_intent": "eda"},
    )
    primary = result["results"][0]
    assert "gate_action" not in primary
    assert manager.calls, "confirmed agent must actually execute"
    assert manager.calls[0][0] == "eda_agent"


@pytest.mark.asyncio
async def test_orchestrator_records_gate_feedback():
    from ai.agents.agent_orchestrator import AgentOrchestrator
    from ai.core.execution_gate import ExecutionGate

    manager = _FakeManager()
    orchestrator = AgentOrchestrator(agent_manager=manager)
    await orchestrator.route_task(
        "生成 RTL 電路",
        {"_gate_confirmed_agent": "eda_agent", "_gate_confirmed_intent": "eda"},
    )
    stats = ExecutionGate().get_feedback_stats()
    assert stats["eda_agent"]["success"] == 1
