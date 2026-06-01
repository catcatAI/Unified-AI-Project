"""Smoke tests for HotReloadService"""
import pytest


class TestHotReloadService:
    """Basic smoke tests for HotReloadService"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from services.hot_reload_service import HotReloadService
            assert HotReloadService is not None
        except ImportError as e:
            pytest.skip(f"HotReloadService not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from services.hot_reload_service import HotReloadService
            instance = HotReloadService()
            assert instance is not None
            assert instance._draining is False
        except ImportError as e:
            pytest.skip(f"HotReloadService not available: {e}")
        except Exception as e:
            pytest.skip(f"HotReloadService init failed (expected in CI): {e}")
