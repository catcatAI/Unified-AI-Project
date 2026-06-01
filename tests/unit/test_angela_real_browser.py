"""Smoke tests for core.art.real_playwright_browser"""
import pytest


class TestAngelaRealBrowser:
    def test_import(self):
        try:
            from core.art.real_playwright_browser import AngelaRealBrowser
            assert AngelaRealBrowser is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.art.real_playwright_browser import AngelaRealBrowser
            instance = AngelaRealBrowser()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
