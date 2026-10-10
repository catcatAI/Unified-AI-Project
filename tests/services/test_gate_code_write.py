# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""Code-WRITE requests (no code in message) fall through to LLM generation
instead of the execute gate (live 2026-10-10: gemma blocked by confirm)."""

from types import SimpleNamespace

import pytest
from services.execution.gate_execution import GateExecutionOwner


def _plan(qtype):
    return SimpleNamespace(query_type=qtype)


@pytest.mark.parametrize(
    "text",
    [
        "寫一個python函數計算費波那契數列",
        "幫我寫一段排序代碼",
        "write a python function",
    ],
)
def test_code_write_detected(text):
    assert GateExecutionOwner._is_code_write_request(_plan("code"), text) is True


@pytest.mark.parametrize(
    "text",
    [
        "執行 ```python\nprint(1)\n```",
        "運行 `print(1)`",
        "for i in range(3):\n    print(i)",
    ],
)
def test_code_execute_not_bypassed(text):
    assert GateExecutionOwner._is_code_write_request(_plan("code"), text) is False


def test_non_code_plan_never_bypassed():
    assert GateExecutionOwner._is_code_write_request(_plan("math"), "寫一個函數") is False
    assert GateExecutionOwner._is_code_write_request(_plan("code"), "") is False


def test_llm_availability_no_side_effects(monkeypatch):
    import services.llm.router as router_mod

    class FakeBackend:
        value = "llamacpp"

    # No service built yet: must NOT initialize, just report False.
    monkeypatch.setattr(router_mod, "_llm_service", None, raising=False)
    assert GateExecutionOwner._llm_generation_available() is False

    fake_svc = SimpleNamespace(backends={FakeBackend(): FakeBackend()})
    monkeypatch.setattr(router_mod, "_llm_service", fake_svc, raising=False)
    assert GateExecutionOwner._llm_generation_available() is True

    class UnifiedBackend:
        value = "unified"

    fake_svc2 = SimpleNamespace(backends={UnifiedBackend(): UnifiedBackend()})
    monkeypatch.setattr(router_mod, "_llm_service", fake_svc2, raising=False)
    assert GateExecutionOwner._llm_generation_available() is False
