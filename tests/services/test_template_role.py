"""
ANGELA-MATRIX: [L3] [β] [B] [L2-L6]
The role of a response template in an AI project.

A canned template used to be served verbatim as the user's answer: the model
never saw it, and the user got the same sentence every time ("摸摸頭~別難過，
我一直在你身邊呢"). For an AI project a template is worth exactly two
things:

  1. an *example* that goes into the model's context (a tone/wording
     reference the model rephrases in its own words), and
  2. a degraded-mode answer when no model can answer at all.

Serving it as the answer in normal operation is the rigid-template failure
mode. These tests pin the corrected split.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


class _Backend:
    """A backend key that is not the offline 'unified' engine."""

    value = "ollama"


def _service(monkeypatch, with_llm: bool):
    """A router whose template layers are reachable."""
    from services.llm.router import AngelaLLMService

    service = object.__new__(AngelaLLMService)
    service.stats = {
        "total_requests": 1,
        "total_response_time": 0.0,
        "memory_hits": 0,
        "composed_responses": 0,
    }
    service.model_bus = None
    service.template_matcher = SimpleNamespace(
        match=lambda *a, **k: SimpleNamespace(score=0.0, template_content="", template_id=None)
    )
    service.backends = {_Backend(): object()} if with_llm else {}
    return service


class _FakeTemplate:
    def __init__(self, template_id, category, keywords, content):
        self.id = template_id
        self.category = category
        self.keywords = keywords
        self.content = content


def _install_library(monkeypatch):
    import ai.memory.template_library as template_library

    templates = [
        _FakeTemplate("comfort_sad", "emotional", ["难过"], "摸摸頭~別難過，我一直在你身邊呢"),
        _FakeTemplate("greeting_general", "greeting", ["你好"], "你好呀！見到你真開心~"),
    ]

    class FakeLibrary:
        def get_all_templates(self):
            return list(templates)

        def get_by_category(self, category):
            return [t for t in templates if t.category == category]

    monkeypatch.setattr(template_library, "get_template_library", lambda: FakeLibrary())


@pytest.mark.asyncio
async def test_with_a_model_the_template_becomes_context_not_the_answer(monkeypatch):
    """The model must get the template as an example, not the user."""
    from services.llm.router import AngelaLLMService

    _install_library(monkeypatch)
    service = _service(monkeypatch, with_llm=True)
    context = {}
    result = await service._try_template_match("我很難過", context, 0.0)

    # No canned answer: the request continues to the model.
    assert result is None
    example = context.get("template_example")
    assert example is not None
    assert example["content"] == "摸摸頭~別難過，我一直在你身邊呢"
    assert example["hit_source"] == "keyword-category"


@pytest.mark.asyncio
async def test_without_a_model_the_template_is_the_degraded_answer(monkeypatch):
    """Offline, the fixed string is the only thing that can answer."""
    from services.llm.router import AngelaLLMService

    _install_library(monkeypatch)
    service = _service(monkeypatch, with_llm=False)
    context = {}
    result = await service._try_template_match("我很難過", context, 0.0)

    assert result is not None
    assert result.text == "摸摸頭~別難過，我一直在你身邊呢"
    assert "template_example" not in context


def test_the_example_reaches_the_prompt_as_a_tone_reference():
    """The model is told it is an example, so it does not echo it verbatim."""
    from services.llm.prompt_builder import construct_angela_prompt

    messages = construct_angela_prompt(
        "我很難過",
        {"template_example": {"content": "摸摸頭~別難過，我一直在你身邊呢"}},
    )
    joined = "\n".join(m["content"] for m in messages)
    assert "摸摸頭~別難過，我一直在你身邊呢" in joined
    assert "語氣示例" in joined or "Tone Example" in joined
    assert "不是答案" in joined or "not the answer" in joined


def test_no_template_example_means_no_extra_prompt_block():
    from services.llm.prompt_builder import construct_angela_prompt

    messages = construct_angela_prompt("你好", {})
    joined = "\n".join(m["content"] for m in messages)
    assert "語氣示例" not in joined
    assert "Tone Example" not in joined
