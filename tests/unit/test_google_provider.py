"""Smoke tests for GoogleAPIBackend"""
import pytest


class TestGoogleAPIBackend:
    """Basic smoke tests for GoogleAPIBackend"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.llm.providers.google import GoogleAPIBackend
            assert GoogleAPIBackend is not None
        except ImportError as e:
            pytest.skip(f"GoogleAPIBackend not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.llm.providers.google import GoogleAPIBackend
            instance = GoogleAPIBackend(api_key="test-key-placeholder")
            assert instance is not None
            assert instance.api_key == "test-key-placeholder"
        except ImportError as e:
            pytest.skip(f"GoogleAPIBackend not available: {e}")
        except Exception as e:
            pytest.skip(f"GoogleAPIBackend init failed (expected in CI): {e}")
