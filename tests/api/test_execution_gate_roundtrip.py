"""
ExecutionGate confirm round-trip through chat_routes (handler + agent paths).

The gate is the single owner of "may this action run": irreversible actions must
ask for confirmation, and the confirmation must be the ONLY thing that executes.
"""

import pytest


class _FakeActionResult(dict):
    pass


class _FakeModelBus:
    def __init__(self):
        self.calls = []

    async def execute_handler(self, handler_id, message, context):
        self.calls.append((handler_id, message))
        return {"type": handler_id, "success": True, "result": {"deleted": True}}


class _FakeChatService:
    def __init__(self):
        self.model_bus = _FakeModelBus()


class TestExecutionGateConfirmRoundTrip:
    @pytest.mark.asyncio
    async def test_delete_requires_confirmation_then_executes_on_confirm(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        from ai.core.execution_gate import ExecutionGate

        ExecutionGate().reset_feedback_stats()
        chat_svc = _FakeChatService()
        monkeypatch.setattr(chat_routes, "_get_chat_service", _async_return(chat_svc))
        monkeypatch.setattr(chat_routes, "sessions", chat_routes.TTLSessionManager())
        session_id = "gate-roundtrip-1"

        first = await chat_routes._handle_execution_gate(
            "刪除 /tmp/angela_gate_probe", chat_svc, {}, "1.0", session_id
        )

        assert first is not None
        assert first["source"] == "gate_confirm"
        assert chat_svc.model_bus.calls == [], "must not execute before confirmation"

        second = await chat_routes._handle_execution_gate(
            "好", chat_svc, {}, "1.0", session_id
        )

        assert second is not None
        assert second["source"] == "gate_executed"
        assert chat_svc.model_bus.calls == [("file_ops", "刪除 /tmp/angela_gate_probe")]

    @pytest.mark.asyncio
    async def test_cancel_does_not_execute(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        from ai.core.execution_gate import ExecutionGate

        ExecutionGate().reset_feedback_stats()
        chat_svc = _FakeChatService()
        monkeypatch.setattr(chat_routes, "_get_chat_service", _async_return(chat_svc))
        monkeypatch.setattr(chat_routes, "sessions", chat_routes.TTLSessionManager())
        session_id = "gate-roundtrip-2"

        await chat_routes._handle_execution_gate(
            "刪除 /tmp/angela_gate_probe2", chat_svc, {}, "1.0", session_id
        )
        cancelled = await chat_routes._handle_execution_gate(
            "算了", chat_svc, {}, "1.0", session_id
        )

        assert cancelled is not None
        assert cancelled["source"] == "gate_cancel"
        assert chat_svc.model_bus.calls == []

    @pytest.mark.asyncio
    async def test_confirm_without_backend_reports_failure(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        from ai.core.execution_gate import ExecutionGate

        ExecutionGate().reset_feedback_stats()
        chat_svc = _FakeChatService()
        monkeypatch.setattr(chat_routes, "_get_chat_service", _async_return(chat_svc))
        monkeypatch.setattr(chat_routes, "sessions", chat_routes.TTLSessionManager())
        session_id = "gate-roundtrip-4"

        await chat_routes._handle_execution_gate(
            "刪除 /tmp/angela_gate_probe4", chat_svc, {}, "1.0", session_id
        )
        chat_svc.model_bus = None
        result = await chat_routes._handle_execution_gate(
            "好", chat_svc, {}, "1.0", session_id
        )

        assert result is not None
        assert result["source"] == "gate_execute_failed"

    @pytest.mark.asyncio
    async def test_pending_action_is_single_use(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        from ai.core.execution_gate import ExecutionGate

        ExecutionGate().reset_feedback_stats()
        chat_svc = _FakeChatService()
        monkeypatch.setattr(chat_routes, "_get_chat_service", _async_return(chat_svc))
        monkeypatch.setattr(chat_routes, "sessions", chat_routes.TTLSessionManager())
        session_id = "gate-roundtrip-3"

        await chat_routes._handle_execution_gate(
            "刪除 /tmp/angela_gate_probe3", chat_svc, {}, "1.0", session_id
        )
        await chat_routes._handle_execution_gate("好", chat_svc, {}, "1.0", session_id)
        third = await chat_routes._handle_execution_gate(
            "好", chat_svc, {}, "1.0", session_id
        )

        assert len(chat_svc.model_bus.calls) == 1, "confirmation must not be replayable"
        assert third is None or third.get("source") != "gate_confirm"


def _async_return(value):
    async def _inner():
        return value

    return _inner
