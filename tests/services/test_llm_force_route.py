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


def _null_matcher():
    """Truthy matcher so _try_template_match runs past its early guard.

    With template_matcher=None the method returns before the social/keyword/
    emotion layers, so a test that only asserts `is None` verifies nothing
    about those layers (two older tests passed for exactly that reason).
    """
    from types import SimpleNamespace

    return SimpleNamespace(match=lambda *a, **k: SimpleNamespace(score=0.0, template_content=""))


def _template_service(monkeypatch, matcher=None):
    """A router instance with the template layers actually reachable."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    service.stats = {
        "total_requests": 1,
        "total_response_time": 0.0,
        "memory_hits": 0,
        "composed_responses": 0,
    }
    service.model_bus = None
    service.template_matcher = matcher if matcher is not None else _null_matcher()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(service, "_recall_user_fact", AsyncMock(return_value=None))
    return service


class _FakeTemplate:
    def __init__(self, category, keywords, content):
        self.category = category
        self.keywords = keywords
        self.content = content


def _fake_library(monkeypatch, templates):
    """Deterministic template library (keyword scan + category lookup)."""
    import ai.memory.template_library as template_library

    class FakeLibrary:
        def get_all_templates(self):
            return list(templates)

        def get_by_category(self, category):
            return [t for t in templates if t.category == category]

    monkeypatch.setattr(template_library, "get_template_library", lambda: FakeLibrary())


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
async def test_recall_prefers_higher_overlap_over_relevance(monkeypatch):
    """Near-duplicate facts: 狐狸(4 chunks) beats 貓(1 chunk) despite lower relevance."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User taught Angela: 我的貓叫咪咪",
                "relevance": 0.95,
            },
            {
                "role": "long_term_memory",
                "content": "User taught Angela: 我的狐狸叫小白",
                "relevance": 0.50,
            },
        ]
    }
    result = await service._recall_user_fact("我的狐狸叫什麼名字？", context, 0.0)
    assert result is not None
    assert "小白" in result.text


@pytest.mark.asyncio
async def test_recall_yields_to_handler_backed_intent(monkeypatch):
    """Imperatives with handler verbs reach handlers, not recall (chip compose case)."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User taught Angela: chip目錄有54個cell",
                "relevance": 0.99,
            }
        ]
    }
    assert await service._recall_user_fact("組裝一個chip查看代理", context, 0.0) is None
    # Plain question on the same fact still recalls.
    result = await service._recall_user_fact("chip目錄有幾個cell", context, 0.0)
    assert result is not None and "54" in result.text


@pytest.mark.asyncio
async def test_recall_yields_to_deterministic_math(monkeypatch):
    """Math-shaped queries compute even when a fact shares a bigram (一百/一百度)."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User taught Angela: 水的沸點是一百度",
                "relevance": 0.99,
            }
        ]
    }
    assert await service._recall_user_fact("一百加二十是多少", context, 0.0) is None


@pytest.mark.asyncio
async def test_store_template_skips_fallback_and_unverified():
    """Fallbacks and unverified generations must never fossilize (template poison)."""
    from unittest.mock import AsyncMock

    from core.interfaces.protocols import LLMResponse

    service = _recall_service()
    service.memory_manager = AsyncMock()
    fallback = LLMResponse(
        text="User，目前還沒有足夠的知識", backend="local-fallback", model="honest"
    )
    await service._store_response_as_template("問題", fallback, {})
    gen = LLMResponse(text="光合作用是植物的過程。", backend="llama.cpp", model="qwen")
    gen.confidence = 0.9
    await service._store_response_as_template("什麼是光合作用", gen, {})
    service.memory_manager.store_template.assert_not_called()


@pytest.mark.asyncio
async def test_clock_response_answers_time_and_date():
    """Deterministic clock: 幾點/今天幾號 never reach fuzzy composers."""
    import time as _time

    service = _recall_service()
    service.stats = {"total_requests": 1, "total_response_time": 0.0, "memory_hits": 0}
    start = _time.time()
    time_resp = await service._clock_response("現在幾點", {}, start)
    assert time_resp is not None
    assert "點" in time_resp.text and "分" in time_resp.text
    assert time_resp.backend == "deterministic-clock"
    date_resp = await service._clock_response("今天幾號", {}, start)
    assert date_resp is not None and "月" in date_resp.text and "日" in date_resp.text
    assert await service._clock_response("你好", {}, start) is None
    assert await service._clock_response("時間管理怎麼做", {}, start) is None


def test_manifest_contains_clock_connector():
    """Routing-engine path must include the clock step (not legacy-only)."""
    from services.llm.routing.manifest import DEFAULT_PLAN

    names = [s.name for s in DEFAULT_PLAN]
    assert "clock" in names
    assert names.index("clock") < names.index("template_match")
    assert DEFAULT_PLAN[-1].kind == "terminal"


@pytest.mark.asyncio
async def test_recall_ignores_storage_prefix_chunks(monkeypatch):
    """English queries share 'us/ta/al' with the storage prefix — must not recall."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User taught Angela: AsyncIO 的基本用法",
                "relevance": 0.9,
            }
        ]
    }
    assert (
        await service._recall_user_fact("Status: shell is already available", context, 0.0) is None
    )


@pytest.mark.asyncio
async def test_recall_english_query_still_matches(monkeypatch):
    """Legit English recall works via 4-grams (CJK bigrams don't apply)."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    context = {
        "retrieved_context": [
            {
                "role": "long_term_memory",
                "content": "User taught Angela: my dog is called Bobby",
                "relevance": 0.7,
            }
        ]
    }
    result = await service._recall_user_fact("what is my dog called", context, 0.0)
    assert result is not None
    assert "Bobby" in result.text


@pytest.mark.asyncio
async def test_emotion_template_yields_to_factual_query(monkeypatch):
    """Factual queries skip emotion templates (physics got random curiosity)."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    service.stats = {
        "total_requests": 1,
        "total_response_time": 0.0,
        "memory_hits": 0,
        "composed_responses": 0,
    }
    service.model_bus = None
    # Truthy matcher: with None the method returns at its own guard, which is
    # what this test used to measure instead of the factual guard.
    service.template_matcher = _null_matcher()
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(service, "_recall_user_fact", AsyncMock(return_value=None))
    result = await service._try_template_match("解釋為什麼天空是藍色的，兩句話", {}, 0.0)
    assert result is None


@pytest.mark.asyncio
async def test_template_layers_yield_to_code_write(monkeypatch):
    """Code-write skips social/keyword/emotion/matcher (修好的→好的affirmation)."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    service = _recall_service()
    # composed_responses must exist: a missing key made the template layer raise
    # KeyError into a bare `except: pass`, so the assertion held for the wrong
    # reason instead of because the code-write gate fired.
    service.stats = {
        "total_requests": 1,
        "total_response_time": 0.0,
        "memory_hits": 0,
        "composed_responses": 0,
    }
    service.model_bus = None
    service.template_matcher = SimpleNamespace(
        match=lambda *a, **k: SimpleNamespace(score=0.99, template_content="好的！没问题~")
    )
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(service, "_recall_user_fact", AsyncMock(return_value=None))
    result = await service._try_template_match("只輸出修好的for循環段", {}, 0.0)
    assert result is None


@pytest.mark.asyncio
async def test_ignorance_template_never_blocks_llm(monkeypatch):
    """不好意思-templates must fall through instead of blocking generation."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from services.llm.router import _KNOWN_FALLBACK_RESPONSES

    assert "不好意思，这个我不太确定..." in _KNOWN_FALLBACK_RESPONSES
    service = _recall_service()
    service.stats = {"total_requests": 1, "total_response_time": 0.0, "memory_hits": 0}
    service.model_bus = None
    service.template_matcher = SimpleNamespace(
        match=lambda *a, **k: SimpleNamespace(
            score=0.95, template_content="不好意思，这个我不太确定..."
        )
    )
    monkeypatch.setattr(service, "_query_taught_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(service, "_recall_user_fact", AsyncMock(return_value=None))
    result = await service._try_template_match("xyzzy_frobnicator_123", {}, 0.0)
    assert result is None


@pytest.mark.asyncio
async def test_fallback_task_gets_honest_cannot_do():
    """Task-shaped fallback: honest inability, never small-talk (Unity case)."""
    service = _recall_service()
    service.model_bus = None
    result = await service._fallback_response(
        "寫Unity Editor腳本只輸出代碼", {"_classify_result_type": "code"}
    )
    assert result.model == "honest-cannot-do"
    assert "做不到" in result.text


@pytest.mark.asyncio
async def test_fallback_chitchat_keeps_smalltalk():
    """Greetings still get templates, not honest-cannot-do."""
    service = _recall_service()
    service.model_bus = None
    result = await service._fallback_response("你好", {"_classify_result_type": "greeting"})
    assert result.model != "honest-cannot-do"


@pytest.mark.asyncio
async def test_query_taught_facts_searches_facts_only_and_filters_prefix(monkeypatch):
    """Direct lookup restricts ranking to taught facts store-side (echo-proof)."""
    from unittest.mock import AsyncMock

    service = _recall_service()
    seen = {}

    async def fake_search(query, k, where_document=None):
        seen["k"] = k
        seen["where"] = where_document
        return {
            "documents": [["User: hi\nAngela: hi", "User taught Angela: 我的鳥叫啾啾"]],
            "distances": [[0.26, 0.48]],
        }

    store = AsyncMock()
    store.semantic_search = fake_search
    monkeypatch.setattr("ai.memory.vector_store.get_vector_store", lambda: store)
    results = await service._query_taught_facts("我的鳥叫什麼名字？")
    assert seen["where"] == {"$contains": "User taught Angela:"}
    assert [r["content"] for r in results] == ["User taught Angela: 我的鳥叫啾啾"]


@pytest.mark.asyncio
async def test_maybe_revive_backends_readds_healthy():
    """A backend pruned at boot (LLM started later) revives on the live path."""
    from unittest.mock import AsyncMock

    class _FakeBackendType:
        value = "late-llm"

    service = _recall_service()
    fake = _FakeBackendType()
    fake.check_health = AsyncMock(return_value=True)
    service._pruned_backends = {fake: fake}
    service._last_revive_check = 0.0
    service.backends = {}

    async def fake_submit(coro, **kwargs):
        return await coro

    service._submit_waiting = fake_submit
    service._pick_best_backend = lambda available: setattr(service, "active_backend_type", fake)
    service._init_model_bus = AsyncMock()

    assert await service._maybe_revive_backends() is True
    assert service.backends == {fake: fake}
    assert service._pruned_backends == {}
    assert service.is_available is True


@pytest.mark.asyncio
async def test_maybe_revive_backends_throttled_and_empty():
    from unittest.mock import AsyncMock

    service = _recall_service()
    service._pruned_backends = {}
    service._last_revive_check = 0.0
    assert await service._maybe_revive_backends() is False

    service._pruned_backends = {"x": AsyncMock()}
    service._last_revive_check = 9999999999.0
    service.backends = {}
    service._submit_waiting = AsyncMock()
    assert await service._maybe_revive_backends() is False
    service._submit_waiting.assert_not_called()


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


@pytest.mark.asyncio
async def test_keyword_category_beats_vague_emotion_category(monkeypatch):
    """回歸鎖定：關鍵詞命中（特定類別）必須勝過 EmotionAnalyzer 的粗略類別。
    舊行為把「我好想你」交給 small_talk 隨機模板（實測吃到「好好吃！我也想尝尝呢~」）。"""
    from ai.memory.memory_template import ResponseCategory

    intimacy = _FakeTemplate(ResponseCategory.INTIMACY, ["想你"], "我也想你！")
    decoy = _FakeTemplate(ResponseCategory.SMALL_TALK, [], "好好吃！我也想尝尝呢~")
    _fake_library(monkeypatch, [intimacy, decoy])
    service = _template_service(monkeypatch)

    result = await service._try_template_match("我好想你", {}, 0.0)

    assert result is not None
    assert result.hit_source == "keyword-category"
    assert result.text == "我也想你！"


@pytest.mark.asyncio
async def test_traditional_input_hits_simplified_keywords(monkeypatch):
    """回歸鎖定：模板庫關鍵詞全為簡體，繁體輸入（我好難過）過去一個都命中不了，
    落到 EmotionAnalyzer 粗略類別後從同類別裡隨機抽一張（實測吃到「工作辛苦了」）。"""
    from ai.memory.memory_template import ResponseCategory

    comfort = _FakeTemplate(ResponseCategory.EMOTIONAL, ["难过"], "摸摸头~别难过")
    decoy = _FakeTemplate(ResponseCategory.HELP, ["工作"], "工作辛苦了！你真的很棒！")
    _fake_library(monkeypatch, [comfort, decoy])
    service = _template_service(monkeypatch)

    result = await service._try_template_match("我好難過", {}, 0.0)

    assert result is not None
    assert result.hit_source == "keyword-category"
    assert result.text == "摸摸头~别难过"


@pytest.mark.asyncio
async def test_serves_the_template_whose_keyword_matched(monkeypatch):
    """回歸鎖定：命中關鍵詞後必須回比對到的那張模板，而不是同類別裡隨機一張。
    「好累」是 study_break 的關鍵詞，過去會被 help 類別的隨機一張蓋掉
    （實測吃到「当然！需要我帮你做什么？」）。"""
    from ai.memory.memory_template import ResponseCategory

    matched = _FakeTemplate(ResponseCategory.HELP, ["好累"], "学了这么久，休息一下吧！")
    sibling = _FakeTemplate(ResponseCategory.HELP, ["帮忙"], "当然！需要我帮你做什么？")
    _fake_library(monkeypatch, [matched, sibling])
    service = _template_service(monkeypatch)

    for _ in range(5):
        result = await service._try_template_match("我好累", {}, 0.0)
        assert result is not None
        assert result.text == "学了这么久，休息一下吧！"


@pytest.mark.asyncio
async def test_negated_keyword_does_not_match(monkeypatch):
    """回歸鎖定：子字串比對下，「不开心」的「开心」和「我不太想你」的「想你」
    都曾經命中，回出與語意相反的答案。"""
    from ai.memory.memory_template import ResponseCategory

    joy = _FakeTemplate(ResponseCategory.EMOTIONAL, ["开心"], "看到你开心，我也跟着开心起来了呢！")
    denial = _FakeTemplate(ResponseCategory.EMOTIONAL, ["不开心"], "摸摸头~别难过")
    missing = _FakeTemplate(ResponseCategory.INTIMACY, ["想你"], "我也想你！")
    _fake_library(monkeypatch, [joy, denial, missing])
    service = _template_service(monkeypatch)

    # 明确的否定短语：由自己的關鍵詞比中
    result = await service._try_template_match("我不开心", {}, 0.0)
    assert result is not None and result.text == "摸摸头~别难过"

    # 否定詞 + 程度副詞：不算命中，不得回出相反的開心模板
    for text in ("我不太开心", "我不太想你"):
        result = await service._try_template_match(text, {}, 0.0)
        assert result is None or result.text != "看到你开心，我也跟着开心起来了呢！"
        assert result is None or result.text != "我也想你！"


@pytest.mark.asyncio
async def test_known_fallback_template_is_never_served(monkeypatch):
    """回歸鎖定：罐頭層不得回「我不太確定」這類已知無知模板——它會擋掉
    真的能回答的 LLM（live 2026-10-10 Unity 請求）。關鍵詞路徑有守門，
    情緒路徑沒有（傷心→support 只有這張模板時就把它回出去了）。

    這裡刻意讓訊息命中不了任何關鍵詞，確保走到的是情緒路徑。"""
    from ai.memory.memory_template import ResponseCategory

    bad = _FakeTemplate(ResponseCategory.SUPPORT, ["相信"], "不好意思，这个我不太确定...")
    _fake_library(monkeypatch, [bad])
    service = _template_service(monkeypatch)

    result = await service._try_template_match("我好伤心啊", {}, 0.0)

    assert result is None


@pytest.mark.asyncio
async def test_keyword_category_yields_to_factual_query(monkeypatch):
    """知識型問題不得被關鍵詞模板搶答，即使模板關鍵詞剛好出現在問題裡。"""
    from ai.memory.memory_template import ResponseCategory

    template = _FakeTemplate(ResponseCategory.CURIOSITY, ["天空"], "天空是藍色的喔~")
    _fake_library(monkeypatch, [template])
    service = _template_service(monkeypatch)

    result = await service._try_template_match("解釋為什麼天空是藍色的，兩句話", {}, 0.0)

    assert result is None


@pytest.mark.asyncio
async def test_code_write_request_skips_keyword_templates(monkeypatch):
    """回歸鎖定（live 2026-10-11 Unity 修復重演）：程式碼請求即使命中模板
    關鍵詞，也必須略過所有罐頭模板層，交由 LLM 生成。"""
    from ai.memory.memory_template import ResponseCategory

    template = _FakeTemplate(ResponseCategory.AFFIRMATION, ["修好"], "好的！没问题~")
    _fake_library(monkeypatch, [template])
    service = _template_service(monkeypatch)

    result = await service._try_template_match("只輸出修好的for循環段", {}, 0.0)

    assert result is None
