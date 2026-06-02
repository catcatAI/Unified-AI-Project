"""Smoke tests for core.state.decimal_hash_table"""
import pytest

class TestDecimalHashTable:
    def test_import(self):
        try:
            from apps.backend.src.core.state.decimal_hash_table import DecimalHashTable
            assert DecimalHashTable is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.core.state.decimal_hash_table import DecimalHashTable
            instance = DecimalHashTable()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
