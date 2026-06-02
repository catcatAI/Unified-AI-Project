"""Tests for OllamaBackend"""
import pytest


class TestOllamaBackend:
    """Tests for OllamaBackend"""

    def test_import(self):
        from services.llm.providers.ollama import OllamaBackend
        assert OllamaBackend is not None

    def test_instantiation_defaults(self):
        from services.llm.providers.ollama import OllamaBackend
        instance = OllamaBackend()
        assert instance is not None
        assert instance.model is not None
        assert instance.base_url is not None

    def test_instantiation_custom(self):
        from services.llm.providers.ollama import OllamaBackend
        instance = OllamaBackend(base_url="http://localhost:11434", model="llama3", api_key="test")
        assert instance.base_url == "http://localhost:11434"
        assert instance.model == "llama3"
        assert instance.api_key == "test"
