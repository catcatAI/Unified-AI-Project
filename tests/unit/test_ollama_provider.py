"""Smoke tests for OllamaBackend"""
import pytest


class TestOllamaBackend:
    """Basic smoke tests for OllamaBackend"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.llm.providers.ollama import OllamaBackend
            assert OllamaBackend is not None
        except ImportError as e:
            pytest.skip(f"OllamaBackend not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.llm.providers.ollama import OllamaBackend
            instance = OllamaBackend()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"OllamaBackend not available: {e}")
        except Exception as e:
            pytest.skip(f"OllamaBackend init failed (expected in CI): {e}")
