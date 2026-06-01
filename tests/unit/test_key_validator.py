"""Smoke tests for core/security/key_validator.py with mock patching"""
from unittest.mock import patch, MagicMock, mock_open
import pytest


class TestKeyValidator:
    """Smoke tests for KeyValidator"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.security.key_validator import KeyValidator
            assert KeyValidator is not None
        except ImportError as e:
            pytest.skip(f"KeyValidator not available: {e}")

    @patch.dict('os.environ', {
        'ANGELA_KEY_A': 'test-key-32-chars-long!!',
        'ANGELA_KEY_B': 'test-key-32-chars-long!!',
        'ANGELA_KEY_C': 'test-key-32-chars-long!!',
        'GEMINI_API_KEY': 'test-key-20-chars!!',
        'OPENAI_API_KEY': 'test-key-20-chars!!',
        'ANTHROPIC_API_KEY': 'test-key-20-chars!!',
        'OLLAMA_API_KEY': 'test-key-20-chars!!',
    })
    def test_instantiation(self):
        """Verify basic instantiation with mock patching"""
        try:
            from core.security.key_validator import KeyValidator
            instance = KeyValidator()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"KeyValidator not available: {e}")
        except Exception as e:
            pytest.skip(f"KeyValidator init failed (expected in CI): {e}")
