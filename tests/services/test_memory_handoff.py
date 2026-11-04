"""記憶是證據，不是回覆——有可生成後端時必須交棒。

使用者的規則：模板、記憶等表層不得直接走對話輸出，該交給能生成答案的層
再處理。這條規則以前只在「教學確認」上成立；回憶、使用者事實、以及 HAM 的
記憶模板仍然會先回答。這裡守住三件事：

1. 判定「有沒有可生成後端」只有一份實作，且 llama.cpp 的三個 slot 名字
   （llamacpp / llamacpp-qwen / llamacpp-gemma）都在名單裡——舊名單寫的是
   ``llama_cpp``，所以 llama.cpp 後端對記憶層是隱形的。
2. 有生成後端時，回憶層把使用者說過的原句放進 ``memory_evidence`` 並回
   None；沒有生成後端（native）時才由回憶層自己回答。
3. HAM 的「記憶模板」是罐頭句：有生成後端時不得直接送出。
"""

import asyncio

import pytest
from services.llm.generation_gate import (
    GENERATIVE_BACKENDS,
    generation_available,
    has_generative_backend,
)
from services.llm.memory_evidence import collect, remember
from services.llm.memory_integration import MemoryIntegration


class _Service:
    def __init__(self, backend_names, manager=None):
        self.backends = {name: object() for name in backend_names}
        self.memory_manager = manager


# --------------------------------------------------------------------------- #
# One definition of "a generator is available"
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", ["openai", "deepseek", "anthropic", "google", "ollama"])
def test_cloud_and_ollama_backends_count_as_generative(name):
    assert has_generative_backend({name: object()}) is True


@pytest.mark.parametrize("name", ["llamacpp", "llamacpp-qwen", "llamacpp-gemma"])
def test_every_llamacpp_slot_is_generative(name):
    """The enum says llamacpp; the old memory allowlist said llama_cpp."""
    assert name in GENERATIVE_BACKENDS
    assert has_generative_backend({name: object()}) is True


def test_the_offline_unified_engine_is_not_a_generator():
    """unified 是專案自己的統計核心，不是能被餵提示改寫的語言模型。"""
    assert has_generative_backend({"unified": object()}) is False
    assert has_generative_backend({}) is False
    assert has_generative_backend(None) is False


def test_generation_available_reads_the_service_without_initializing():
    assert generation_available(_Service(["unified", "openai"])) is True
    assert generation_available(_Service(["unified"])) is False


def test_a_service_registered_before_the_module_global_is_still_seen(monkeypatch):
    """Chat Step 1c asks before it fetches the service.

    The gate must not answer "no model" just because ``get_llm_service()`` has
    not assigned the module global yet — the registry entry is written after
    initialize(), which is exactly when the answer becomes knowable.
    """
    from core.interfaces.service_registry import get_registry
    from services.llm import router as router_module

    registry = get_registry()
    previous = registry.get("angela_llm_service")
    monkeypatch.setattr(router_module, "_llm_service", None)
    registry.register("angela_llm_service", _Service(["openai"]))
    try:
        assert generation_available() is True
    finally:
        if previous is None:
            registry.unregister("angela_llm_service")
        else:
            registry.register("angela_llm_service", previous)


def test_the_provider_enum_names_are_the_ones_checked():
    from services.llm.providers.registry import LLMBackend

    assert has_generative_backend({LLMBackend.LLAMA_CPP: object()}) is True
    assert has_generative_backend({LLMBackend.UNIFIED: object()}) is False


# --------------------------------------------------------------------------- #
# Conversation recall: hand over, do not speak
# --------------------------------------------------------------------------- #
def _recall(service, question, context):
    return asyncio.run(  # type: ignore[arg-type]
        MemoryIntegration(service).try_conversation_recall(question, context)
    )


@pytest.fixture
def statements(monkeypatch):
    async def _candidates(self, question, manager):
        return ["我住在新竹", "我今天用紅色背包"]

    monkeypatch.setattr(MemoryIntegration, "_recall_candidates", _candidates)


def test_recall_is_published_as_evidence_when_a_generator_exists(statements):
    context = {}
    response = _recall(
        _Service(["unified", "openai"], manager=object()),
        "我剛才說我住哪裡？",
        context,
    )
    assert response is None, "the memory layer must not speak for the model"
    assert collect(context) == [{"text": "我住在新竹", "source": "conversation"}]


def test_the_native_path_still_answers_the_recall_question(statements):
    """No generator: the extractive answer is the honest degraded mode."""
    response = _recall(_Service(["unified"], manager=object()), "我剛才說我住哪裡？", {})
    assert response is not None
    assert "新竹" in response.text
    assert response.backend == "memory-recall"


def test_the_recall_scan_runs_once_per_turn(statements, monkeypatch):
    """Both the template and memory connectors ask; the second must not repeat."""
    calls = []

    async def _counting_candidates(self, question, manager):
        calls.append(question)
        return ["我住在新竹"]

    monkeypatch.setattr(MemoryIntegration, "_recall_candidates", _counting_candidates)
    service = _Service(["unified"], manager=object())
    context = {}
    first = _recall(service, "我剛才說我住哪裡？", context)
    second = _recall(service, "我剛才說我住哪裡？", context)
    assert first is not None
    assert second is None
    assert len(calls) == 1


# --------------------------------------------------------------------------- #
# HAM memory templates are canned lines
# --------------------------------------------------------------------------- #
class _TemplateManager:
    async def retrieve_response_templates(self, query, limit, min_score):
        return [({"id": "tpl-1", "content": "雨天有雨天的趣味"}, 0.9)]


def _memory_retrieval(service, message="今天天氣如何？"):
    return asyncio.run(MemoryIntegration(service).try_memory_retrieval(message, {}))


def test_a_memory_template_does_not_pre_empt_a_generator(monkeypatch):
    async def _no_candidates(self, question, manager):
        return []

    monkeypatch.setattr(MemoryIntegration, "_recall_candidates", _no_candidates)
    # The poison guard is not what this test is about; the hit itself is.
    monkeypatch.setattr(
        MemoryIntegration, "_validated_template_content", lambda self, tpl: tpl["content"]
    )
    assert _memory_retrieval(_Service(["unified", "openai"], _TemplateManager())) is None


def test_the_native_path_still_serves_the_memory_template(monkeypatch):
    async def _no_candidates(self, question, manager):
        return []

    monkeypatch.setattr(MemoryIntegration, "_recall_candidates", _no_candidates)
    monkeypatch.setattr(
        MemoryIntegration, "_validated_template_content", lambda self, tpl: tpl["content"]
    )
    response = _memory_retrieval(_Service(["unified"], _TemplateManager()))
    assert response is not None
    assert response.backend == "memory-template"


# --------------------------------------------------------------------------- #
# Evidence is rendered for the model, and deduplicated
# --------------------------------------------------------------------------- #
def test_evidence_is_deduplicated_and_copied():
    context = {}
    remember(context, "我住在新竹", "conversation")
    remember(context, "我住在新竹", "conversation")
    assert collect(context) == [{"text": "我住在新竹", "source": "conversation"}]
    copy = collect(context)
    copy[0]["text"] = "changed"
    assert collect(context)[0]["text"] == "我住在新竹"


def test_evidence_reaches_the_prompt():
    from services.llm.prompt_builder import _append_memory_evidence

    context = {}
    remember(context, "我住在新竹", "conversation")
    messages = []
    _append_memory_evidence(messages, context)
    assert len(messages) == 1
    assert "我住在新竹" in messages[0]["content"]
    # It must be named as memory, not as verified knowledge.
    assert "記憶" in messages[0]["content"] or "Memory" in messages[0]["content"]


def test_empty_evidence_adds_nothing():
    from services.llm.prompt_builder import _append_memory_evidence

    messages = []
    _append_memory_evidence(messages, {})
    assert messages == []


# --------------------------------------------------------------------------- #
# The pipeline's taught-fact turn: one of (reply, evidence), never both
# --------------------------------------------------------------------------- #
@pytest.fixture
def taught_fact(tmp_path, monkeypatch):
    from ai.memory.taught_facts import get_taught_facts, reset_taught_facts

    monkeypatch.setenv("ANGELA_TAUGHT_FACTS", str(tmp_path / "taught.json"))
    reset_taught_facts()
    get_taught_facts().learn_from_turn("Zorblax 的首都是 Quuxville。")
    yield "Zorblax 的首都是哪裡？"
    reset_taught_facts()


def test_a_taught_fact_is_evidence_when_a_generator_exists(taught_fact, monkeypatch):
    from api.routes.chat_routes import _taught_fact_turn
    from services.llm import generation_gate

    monkeypatch.setattr(generation_gate, "generation_available", lambda *a: True)
    reply, evidence = _taught_fact_turn(taught_fact, "sess")
    assert reply is None, "the memory layer must not answer for the model"
    assert evidence is not None
    assert "Quuxville" in evidence["text"]
    assert evidence["source"] == "taught_facts"


def test_a_taught_fact_is_answered_when_no_generator_exists(taught_fact, monkeypatch):
    from api.routes.chat_routes import _taught_fact_turn
    from services.llm import generation_gate

    monkeypatch.setattr(generation_gate, "generation_available", lambda *a: False)
    reply, evidence = _taught_fact_turn(taught_fact, "sess")
    assert evidence is None
    assert reply is not None
    assert reply["source"] == "memory"
    assert "你教過我" in reply["response_text"]
    assert "Quuxville" in reply["response_text"]


# --------------------------------------------------------------------------- #
# The teaching acknowledgment must yield to every generative slot
# --------------------------------------------------------------------------- #
def _ack(service, message):
    return asyncio.run(MemoryIntegration(service).try_teaching_ack(message))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "backend",
    ["openai", "deepseek", "anthropic", "google", "ollama", "llamacpp", "llamacpp-qwen"],
)
def test_the_teaching_frame_never_pre_empts_a_generator(backend):
    """The old allowlist said llama_cpp; llama.cpp was invisible to it."""
    assert _ack(_Service([backend]), "我今年三十五歲") is None


def test_the_native_path_still_acknowledges(monkeypatch):
    response = _ack(_Service(["unified"]), "我今年三十五歲")
    assert response is not None
    assert response.backend == "memory-teaching"


# --------------------------------------------------------------------------- #
# A taught pair the encoder recalls is still memory, not generation
# --------------------------------------------------------------------------- #
class _TaughtEngine:
    """Only the attributes ``_try_neural_retrieval`` reads."""

    core = object()
    _taught_pairs = [("水的沸點是多少？", "100 度")]


class _EngineBackend:
    _engine = _TaughtEngine()


def _router(backend_names):
    from services.llm.router import AngelaLLMService

    service = object.__new__(AngelaLLMService)
    service.backends = {
        name: (_EngineBackend() if name == "unified" else object()) for name in backend_names
    }
    return service


def test_a_recalled_taught_pair_is_evidence_when_a_generator_exists():
    """Similarity is neural; the replayed answer is still a memory of an exchange.

    Serving it verbatim (labelled ``hit_source="neural"``) pre-empts the model
    and makes retrieval look like generation.
    """
    context = {}
    result = _router(["unified", "openai"])._try_neural_retrieval("水的沸點是多少？", context)
    assert result is None
    assert [item["text"] for item in collect(context)] == ["100 度"]


def test_the_native_path_still_answers_from_the_taught_pair():
    result = _router(["unified"])._try_neural_retrieval("水的沸點是多少？", {})
    assert result is not None
    assert result.text == "100 度"
