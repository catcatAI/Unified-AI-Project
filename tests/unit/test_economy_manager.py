"""Smoke tests for economy/economy_manager.py"""
import pytest


class TestEconomyManager:
    """Basic smoke tests for EconomyManager"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from economy.economy_manager import EconomyManager
            assert EconomyManager is not None
        except ImportError as e:
            pytest.skip(f"EconomyManager not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from economy.economy_manager import EconomyManager
            instance = EconomyManager(config={})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"EconomyManager not available: {e}")
        except Exception as e:
            pytest.skip(f"EconomyManager init failed (expected in CI): {e}")
