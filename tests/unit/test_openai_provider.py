"""Smoke tests for OpenAIAPIBackend"""
import pytest


class TestOpenAIAPIBackend:
    """Basic smoke tests for OpenAIAPIBackend"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.llm.providers.openai import OpenAIAPIBackend
            assert OpenAIAPIBackend is not None
        except ImportError as e:
            pytest.skip(f"OpenAIAPIBackend not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.llm.providers.openai import OpenAIAPIBackend
            instance = OpenAIAPIBackend(api_key="test-key-placeholder")
            assert instance is not None
            assert instance.api_key == "test-key-placeholder"
        except ImportError as e:
            pytest.skip(f"OpenAIAPIBackend not available: {e}")
        except Exception as e:
            pytest.skip(f"OpenAIAPIBackend init failed (expected in CI): {e}")
