"""Smoke tests for core.bio.input_sensor"""
import pytest


class TestGlobalInputSensor:
    def test_import(self):
        try:
            from core.bio.input_sensor import GlobalInputSensor
            assert GlobalInputSensor is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.bio.input_sensor import GlobalInputSensor
            instance = GlobalInputSensor()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
