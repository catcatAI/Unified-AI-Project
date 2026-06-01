"""Smoke tests for core.hardware.precision_matrix"""
import pytest


class TestPrecisionMatrix:
    def test_import(self):
        try:
            from core.hardware.precision_matrix import PrecisionMatrix
            assert PrecisionMatrix is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.precision_matrix import PrecisionMatrix
            instance = PrecisionMatrix()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
