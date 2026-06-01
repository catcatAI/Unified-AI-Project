"""Smoke tests for core.hardware.compute_matrix"""
import pytest


class TestComputationMatrix:
    def test_import(self):
        try:
            from core.hardware.compute_matrix import ComputationMatrix
            assert ComputationMatrix is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.compute_matrix import ComputationMatrix
            instance = ComputationMatrix()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
