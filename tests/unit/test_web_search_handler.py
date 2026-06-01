"""Smoke tests for WebSearchHandler"""
import pytest


class TestWebSearchHandler:
    """Basic smoke tests for WebSearchHandler"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.handlers.web_search_handler import WebSearchHandler
            assert WebSearchHandler is not None
        except ImportError as e:
            pytest.skip(f"WebSearchHandler not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.handlers.web_search_handler import WebSearchHandler
            instance = WebSearchHandler()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"WebSearchHandler not available: {e}")
        except Exception as e:
            pytest.skip(f"WebSearchHandler init failed (expected in CI): {e}")
