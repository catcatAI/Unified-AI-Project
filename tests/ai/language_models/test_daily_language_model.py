import pytest
from unittest.mock import AsyncMock
from ai.language_models.daily_language_model import DailyLanguageModel


def test_dlm_initialization():
    model = DailyLanguageModel()
    assert model.total_interactions == 0
    assert model.intent_accuracy == 0.0
    assert model.interaction_history == []
    assert model.llm_service is None


def test_dlm_get_stats():
    model = DailyLanguageModel()
    stats = model.get_stats()
    assert stats["total_interactions"] == 0
    assert stats["history_size"] == 0
    assert stats["dna_chains"] == 0


def test_dlm_recognize_intent_no_tools():
    import asyncio
    model = DailyLanguageModel()
    result = asyncio.run(model.recognize_intent("hello"))
    assert result == {"tool_name": None, "parameters": None, "confidence": 0.0}


def test_dlm_simple_intent_recognition_calculate():
    model = DailyLanguageModel()
    tools = {"calculate": "Perform math operations", "translate": "Translate text"}
    result = model._simple_intent_recognition("please calculate 2 + 2", tools)
    assert result["tool_name"] == "calculate"


def test_dlm_simple_intent_recognition_no_match():
    model = DailyLanguageModel()
    tools = {"calculate": "Perform math operations"}
    result = model._simple_intent_recognition("what is the weather", tools)
    assert result["tool_name"] is None
    assert result["confidence"] == 0.0


def test_dlm_simple_intent_recognition_translate():
    model = DailyLanguageModel()
    tools = {"calculate": "Math", "translate": "Translation"}
    result = model._simple_intent_recognition("translate hello to french", tools)
    assert result["tool_name"] == "translate"


def test_dlm_chat_no_llm():
    import asyncio
    model = DailyLanguageModel()
    result = asyncio.run(model.chat("hello"))
    assert result == "I'm listening, but I don't have a language model connected yet."


def test_dlm_stats_after_chat():
    import asyncio
    model = DailyLanguageModel()
    asyncio.run(model.chat("test"))
    stats = model.get_stats()
    assert stats["total_interactions"] == 1
    assert stats["history_size"] == 1