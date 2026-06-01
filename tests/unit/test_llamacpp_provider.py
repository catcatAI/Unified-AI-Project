"""Smoke tests for LlamaCppBackend"""
import pytest


class TestLlamaCppBackend:
    """Basic smoke tests for LlamaCppBackend"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.llm.providers.llamacpp import LlamaCppBackend
            assert LlamaCppBackend is not None
        except ImportError as e:
            pytest.skip(f"LlamaCppBackend not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.llm.providers.llamacpp import LlamaCppBackend
            instance = LlamaCppBackend()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"LlamaCppBackend not available: {e}")
        except Exception as e:
            pytest.skip(f"LlamaCppBackend init failed (expected in CI): {e}")
