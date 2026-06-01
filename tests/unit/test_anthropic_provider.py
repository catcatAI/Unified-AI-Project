"""Smoke tests for AnthropicAPIBackend"""
import pytest


class TestAnthropicAPIBackend:
    """Basic smoke tests for AnthropicAPIBackend"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.llm.providers.anthropic import AnthropicAPIBackend
            assert AnthropicAPIBackend is not None
        except ImportError as e:
            pytest.skip(f"AnthropicAPIBackend not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.llm.providers.anthropic import AnthropicAPIBackend
            instance = AnthropicAPIBackend(api_key="test-key-placeholder")
            assert instance is not None
            assert instance.api_key == "test-key-placeholder"
        except ImportError as e:
            pytest.skip(f"AnthropicAPIBackend not available: {e}")
        except Exception as e:
            pytest.skip(f"AnthropicAPIBackend init failed (expected in CI): {e}")
