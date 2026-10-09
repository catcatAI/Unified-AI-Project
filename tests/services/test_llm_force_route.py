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


def _recall_service():
    from services.llm.router import AngelaLLMService

    return object.__new__(AngelaLLMService)


def _fact_context(content="User taught Angela: 我的貓叫咪咪", relevance=0.9):
    return {
        "retrieved_context": [
            {"role": "long_term_memory", "content": content, "relevance": relevance}
        ]
    }


@pytest.mark.asyncio
async def test_recall_user_fact_answers_from_memory():
    """Taught facts shadow social templates when the query overlaps (no LLM needed)."""
    service = _recall_service()
    result = await service._recall_user_fact("我的貓叫什麼名字？", _fact_context(), 0.0)
    assert result is not None
    assert "咪咪" in result.text
    assert result.backend == "memory"
    assert result.hit_source == "user_fact"


@pytest.mark.asyncio
async def test_recall_user_fact_ignores_unrelated_query():
    """Greetings must still reach templates: no shared chunk, no interception."""
    service = _recall_service()
    result = await service._recall_user_fact("你好", _fact_context(), 0.0)
    assert result is None


@pytest.mark.asyncio
async def test_recall_user_fact_ignores_non_memory_entries(monkeypatch):
    """Only long_term_memory role counts, never prompt/dictionary entries."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {"retrieved_context": [{"role": "system", "content": "我的貓叫咪咪"}]}
    assert await service._recall_user_fact("我的貓叫什麼名字？", context, 0.0) is None


@pytest.mark.asyncio
async def test_recall_user_fact_ignores_conversation_history(monkeypatch):
    """Session history shares the memory role but lacks the taught prefix."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User: 我的貓叫什麼名字？\nAngela: 我是Angela AI",
                "relevance": 0.99,
            }
        ]
    }
    assert await service._recall_user_fact("我的貓叫什麼名字？", context, 0.0) is None


@pytest.mark.asyncio
async def test_recall_user_fact_empty_context(monkeypatch):
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    assert await service._recall_user_fact("我的貓叫什麼名字？", {}, 0.0) is None
    assert await service._recall_user_fact("", _fact_context(), 0.0) is None


@pytest.mark.asyncio
async def test_recall_user_fact_falls_back_to_direct_query(monkeypatch):
    """Top-3 context hits may bury the fact under echoes; direct lookup rescues it."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(
        service,
        "_query_taught_facts",
        AsyncMock(
            return_value=[
                {
                    "role": "long_term_memory",
                    "content": "User taught Angela: 我的狗叫旺財",
                    "relevance": 0.6,
                }
            ]
        ),
    )
    result = await service._recall_user_fact("我的狗叫什麼名字？", {}, 0.0)
    assert result is not None
    assert "旺財" in result.text


@pytest.mark.asyncio
async def test_query_taught_facts_searches_wide_and_filters_prefix(monkeypatch):
    """Direct lookup uses top-50 (facts rank ~49 under echoes) and keeps prefix only."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    seen = {}

    async def fake_search(query, k):
        seen["k"] = k
        return {
            "documents": [["User: hi\nAngela: hi", "User taught Angela: 我的鳥叫啾啾"]],
            "distances": [[0.26, 0.48]],
        }

    store = AsyncMock()
    store.semantic_search = fake_search
    monkeypatch.setattr("ai.memory.vector_store.get_vector_store", lambda: store)
    results = await service._query_taught_facts("我的鳥叫什麼名字？")
    assert seen["k"] == 50
    assert [r["content"] for r in results] == ["User taught Angela: 我的鳥叫啾啾"]


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
