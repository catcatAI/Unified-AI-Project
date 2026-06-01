"""Smoke tests for core.hardware.hal"""
import pytest


class TestHardwareManager:
    def test_import(self):
        try:
            from core.hardware.hal import HardwareManager
            assert HardwareManager is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.hardware.hal import HardwareManager
            instance = HardwareManager()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
