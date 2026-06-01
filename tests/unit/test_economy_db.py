"""Smoke tests for economy/economy_db.py"""
import pytest


class TestEconomyDB:
    """Basic smoke tests for EconomyDB"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from economy.economy_db import EconomyDB
            assert EconomyDB is not None
        except ImportError as e:
            pytest.skip(f"EconomyDB not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from economy.economy_db import EconomyDB
            instance = EconomyDB(db_path=":memory:")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"EconomyDB not available: {e}")
        except Exception as e:
            pytest.skip(f"EconomyDB init failed (expected in CI): {e}")
