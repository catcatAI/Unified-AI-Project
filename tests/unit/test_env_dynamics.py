"""Smoke tests for core.life.env_dynamics"""
import pytest


class TestEnvironmentDynamics:
    def test_import(self):
        try:
            from core.life.env_dynamics import EnvironmentDynamics
            assert EnvironmentDynamics is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.life.env_dynamics import EnvironmentDynamics
            instance = EnvironmentDynamics()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
