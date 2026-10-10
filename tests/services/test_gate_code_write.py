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


@pytest.mark.parametrize(
    "text",
    [
        "直接輸出完整Unity C#代碼，不要任何前言",
        "寫一個Unity類建車身",
        "幫我生成排序函數",
        "繼續，直接給完整代碼",
    ],
)
def test_message_level_write_detected(text):
    assert GateExecutionOwner.is_code_write_request(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "關機",
        "刪除/tmp舊檔",
        "寫一封信",
        "執行 ```python\nprint(1)\n```",
        "第一個字符就是```csharp加上代碼",
    ],
)
def test_message_level_write_rejected(text):
    assert GateExecutionOwner.is_code_write_request(text) is False


def test_lone_fence_mention_is_not_code():
    """'第一個字符就是```csharp' is an instruction, not a carried block."""
    assert GateExecutionOwner._has_no_executable_code("第一個字符就是```csharp輸出代碼") is True
    assert GateExecutionOwner._has_no_executable_code("執行 ```python\nprint(1)\n```") is False


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
