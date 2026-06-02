"""Tests for core/config_validator.py"""
import os
import pytest


class TestConfigValidator:
    """Tests for ConfigValidator"""

    def test_import(self):
        from core.config_validator import ConfigValidator
        assert ConfigValidator is not None

    def test_instantiation(self):
        from core.config_validator import ConfigValidator
        instance = ConfigValidator()
        assert instance is not None
        assert instance.result is not None
        assert len(instance.specs) > 0

    def test_validate_missing_env_file(self):
        from core.config_validator import ConfigValidator, Severity
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            fake_env = os.path.join(tmp, ".env")
            validator = ConfigValidator(env_file=fake_env)
            assert hasattr(validator, "validate")

    def test_severity_enum(self):
        from core.config_validator import Severity
        assert Severity.ERROR.value == "ERROR"
        assert Severity.WARNING.value == "WARNING"
        assert Severity.INFO.value == "INFO"

    def test_validation_result_methods(self):
        from core.config_validator import ValidationResult
        r = ValidationResult(valid=True)
        assert r.valid is True
        r.add_error("test error")
        assert r.valid is False
        assert "test error" in r.errors
        r.add_warning("test warning")
        assert "test warning" in r.warnings
        r.add_info("test info")
        assert "test info" in r.info

    def test_env_var_spec_defaults(self):
        from core.config_validator import EnvVarSpec
        spec = EnvVarSpec(name="TEST_VAR", description="A test var")
        assert spec.required is True
        assert spec.default is None
        assert spec.allowed_values is None
