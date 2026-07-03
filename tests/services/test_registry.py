"""Tests for LLMBackend enum registry."""
import pytest
from services.llm.providers.registry import LLMBackend


class TestLLMBackend:
    def test_has_llamacpp(self):
        assert LLMBackend.LLAMA_CPP.value == "llamacpp"

    def test_has_ollama(self):
        assert LLMBackend.OLLAMA.value == "ollama"

    def test_has_openai(self):
        assert LLMBackend.OPENAI.value == "openai"

    def test_has_anthropic(self):
        assert LLMBackend.ANTHROPIC.value == "anthropic"

    def test_has_google(self):
        assert LLMBackend.GOOGLE.value == "google"

    def test_has_ed3n(self):
        assert LLMBackend.ED3N.value == "ed3n"

    def test_has_garden(self):
        assert LLMBackend.GARDEN.value == "garden"

    def test_has_local(self):
        assert LLMBackend.LOCAL.value == "local"

    def test_has_none(self):
        assert LLMBackend.NONE.value == "none"

    def test_members_count(self):
        assert len(LLMBackend) == 9

    def test_from_value_valid(self):
        assert LLMBackend("ollama") == LLMBackend.OLLAMA

    def test_from_value_invalid_raises(self):
        with pytest.raises(ValueError):
            LLMBackend("nonexistent")

    def test_unique_values(self):
        values = [m.value for m in LLMBackend]
        assert len(values) == len(set(values))
