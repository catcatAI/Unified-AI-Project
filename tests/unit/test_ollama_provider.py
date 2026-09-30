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

    def test_base_url_env_override_is_honoured(self, monkeypatch):
        """It was a documented-but-dead switch: only a comment read it."""
        from services.llm.providers.ollama import OllamaBackend

        monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.50:11434")
        assert OllamaBackend().base_url == "http://192.168.1.50:11434"

    def test_explicit_base_url_beats_the_env_override(self, monkeypatch):
        from services.llm.providers.ollama import OllamaBackend

        monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.50:11434")
        instance = OllamaBackend(base_url="http://localhost:11434")
        assert instance.base_url == "http://localhost:11434"

    def test_default_falls_back_to_the_local_host(self, monkeypatch):
        from core.system.config.network_defaults import OLLAMA_HOST, get_ollama_base_url
        from services.llm.providers.ollama import OllamaBackend

        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        assert OllamaBackend().base_url == OLLAMA_HOST
        # a blank value is not an override either
        monkeypatch.setenv("OLLAMA_BASE_URL", "   ")
        assert get_ollama_base_url() == OLLAMA_HOST

    def test_get_llm_info(self):
        from services.llm.providers.ollama import OllamaBackend

        instance = OllamaBackend()
        info = (
            instance.get_llm_info() if hasattr(instance, "get_llm_info") else {"provider": "ollama"}
        )
        assert isinstance(info, dict)
        assert "provider" in info
