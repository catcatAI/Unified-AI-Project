"""Tests for apps.backend.src.core.config_validator"""

import os

import pytest

from apps.backend.src.core.config_validator import (
    ConfigValidator,
    REQUIRED_VARS,
    OPTIONAL_VARS,
    REQUIRED_CONFIG_KEYS,
    validate_environment,
    validate_config,
)


class TestConfigValidator:
    def test_init_empty(self):
        v = ConfigValidator()
        assert v.config == {}

    def test_init_with_config(self):
        v = ConfigValidator({"version": "1.0", "name": "test"})
        assert v.config["version"] == "1.0"

    def test_validate_environment_missing_required(self):
        for k in REQUIRED_VARS:
            os.environ.pop(k, None)
        v = ConfigValidator()
        result = v.validate_environment()
        assert result is False
        errors = v.get_errors()
        assert len(errors) > 0
        assert any("ANGELA_HOME" in e for e in errors)

    def test_validate_environment_passes_with_env_set(self):
        os.environ["ANGELA_HOME"] = "C:\\test"
        v = ConfigValidator()
        result = v.validate_environment()
        assert result is True
        os.environ.pop("ANGELA_HOME", None)

    def test_validate_config_missing_keys(self):
        v = ConfigValidator({})
        result = v.validate_config()
        assert result is False
        errors = v.get_errors()
        assert len(errors) > 0

    def test_validate_config_passes(self):
        v = ConfigValidator({"version": "1.0", "name": "test"})
        result = v.validate_config()
        assert result is True

    def test_get_warnings_empty(self):
        v = ConfigValidator()
        assert v.get_warnings() == []

    def test_validate_environment_standalone(self):
        os.environ["ANGELA_HOME"] = "C:\\test"
        ok, errors = validate_environment()
        assert ok is True
        assert errors == []
        os.environ.pop("ANGELA_HOME", None)

    def test_validate_config_standalone(self):
        ok, errors = validate_config({"version": "1.0", "name": "test"})
        assert ok is True
        assert errors == []

    def test_validate_config_standalone_fails(self):
        ok, errors = validate_config({})
        assert ok is False
        assert len(errors) > 0


class TestConstants:
    def test_required_vars_defined(self):
        assert "ANGELA_HOME" in REQUIRED_VARS

    def test_optional_vars_defined(self):
        assert "ANGELA_LOG_LEVEL" in OPTIONAL_VARS

    def test_required_config_keys_defined(self):
        assert "version" in REQUIRED_CONFIG_KEYS
        assert "name" in REQUIRED_CONFIG_KEYS

    def test_validate_environment_twice_clears_errors(self):
        for k in REQUIRED_VARS:
            os.environ.pop(k, None)
        v = ConfigValidator()
        v.validate_environment()
        assert len(v.get_errors()) > 0
        os.environ["ANGELA_HOME"] = "C:\\test"
        v.validate_environment()
        assert v.get_errors() == []
        os.environ.pop("ANGELA_HOME", None)
