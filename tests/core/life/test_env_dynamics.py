"""Tests for EnvironmentDynamics."""
import pytest
from core.life.env_dynamics import EnvironmentDynamics


class TestEnvironmentDynamics:
    def test_init_default(self):
        env = EnvironmentDynamics()
        assert env.config == {}

    def test_init_with_config(self):
        env = EnvironmentDynamics(config={"threshold": 0.7})
        assert env.config["threshold"] == 0.7

    def test_get_dynamic_threshold_found(self):
        env = EnvironmentDynamics(config={"temp": 0.8})
        assert env.get_dynamic_threshold("temp") == 0.8

    def test_get_dynamic_threshold_not_found_default(self):
        env = EnvironmentDynamics(config={"temp": 0.8})
        assert env.get_dynamic_threshold("humidity", 0.5) == 0.5

    def test_get_dynamic_threshold_not_found_no_default(self):
        env = EnvironmentDynamics()
        assert env.get_dynamic_threshold("nonexistent") == 0.0

    def test_get_dynamic_threshold_float_string_key(self):
        env = EnvironmentDynamics(config={"key": 0.5})
        assert isinstance(env.get_dynamic_threshold("key"), float)
