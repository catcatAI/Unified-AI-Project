# ANGELA-MATRIX: [L3] [β] [B] [L2]

from unittest.mock import patch

import pytest
from core.interfaces.protocols import LLMResponse
from services.llm.router import AngelaLLMService


@pytest.mark.asyncio
async def test_force_llm_context_bypasses_template_route() -> None:
    service = object.__new__(AngelaLLMService)
    service.stats = {"total_requests": 0}
    calls = []

    async def fake_route(user_message, context, start_time):
        calls.append((user_message, context, start_time))
        return LLMResponse(text="forced", backend="test-llm", model="test-model")

    service._route_step_main_llm = fake_route
    result = await service.generate_response_full(
        "template-shaped input",
        {"force_llm": True},
    )

    assert result.backend == "test-llm"
    assert result.text == "forced"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_force_llm_upgrades_scheduled_context_digest() -> None:
    service = object.__new__(AngelaLLMService)
    messages = [{"role": "system", "content": "[Digested Context]\n- 舊摘要"}]
    calls = []

    class FakeScheduler:
        async def digest_with_llm(self, text, conversation_id, llm_service=None):
            calls.append((text, conversation_id, llm_service))
            return "- 新摘要"

    with patch(
        "services.llm.context_scheduler.get_context_scheduler",
        return_value=FakeScheduler(),
    ):
        await service._upgrade_digested_context(
            messages, {"force_llm": True, "conversation_id": "conv-eda"}
        )

    assert messages[0]["content"] == "[Digested Context — LLM]\n- 新摘要"
    assert calls[0][1] == "conv-eda"
    assert calls[0][2] is service


@pytest.mark.asyncio
async def test_backend_calls_use_waiting_scheduler_owner() -> None:
    service = object.__new__(AngelaLLMService)
    calls = []

    class FakeBackend:
        async def generate(self, **kwargs):
            calls.append(kwargs)
            return LLMResponse(text="scheduled", backend="test", model="test")

    class FakeScheduler:
        async def submit(self, coro, timeout=0.0, label=""):
            calls.append({"timeout": timeout, "label": label})
            return await coro

    with patch("core.waiting_scheduler.get_waiting_scheduler", return_value=FakeScheduler()):
        result = await service._submit_backend_call(
            FakeBackend(),
            prompt="hello",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.2,
            max_tokens=32,
            timeout=4.0,
            label="test",
        )

    assert result is not None
    assert result.text == "scheduled"
    assert calls[0]["timeout"] == 4.0
    assert calls[0]["label"] == "test"
