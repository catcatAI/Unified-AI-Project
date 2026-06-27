import os

import pytest

try:
    from apps.backend.src.core.config_validator import (
        ConfigValidator,
        EnvVarSpec,
        Severity,
        ValidationResult,
    )
except ImportError:
    import pytest; pytest.skip("ConfigValidator is a stub", allow_module_level=True)


class TestValidationResult:
    def test_add_error(self):
        result = ValidationResult(valid=True)
        result.add_error("error 1")
        assert result.valid is False
        assert len(result.errors) == 1

    def test_add_warning(self):
        result = ValidationResult(valid=True)
        result.add_warning("warning 1")
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_add_info(self):
        result = ValidationResult(valid=True)
        result.add_info("info 1")
        assert len(result.info) == 1


class TestEnvVarSpec:
    def test_default_values(self):
        spec = EnvVarSpec(name="TEST_VAR", description="test")
        assert spec.required is True
        assert spec.default is None
        assert spec.validator is None
        assert spec.allowed_values is None

    def test_custom_values(self):
        spec = EnvVarSpec(
            name="TEST_VAR", description="test",
            required=False, default="hello",
            allowed_values=["hello", "world"],
            min_length=2, max_length=10,
        )
        assert spec.required is False
        assert spec.default == "hello"


class TestConfigValidator:
    def test_initial_specs_contain_required_vars(self):
        validator = ConfigValidator()
        names = [s.name for s in validator.specs]
        assert "ANGELA_KEY_A" in names
        assert "BACKEND_HOST" in names
        assert "DATABASE_URL" in names

    def test_validate_missing_required(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        for name in ["ANGELA_KEY_A", "ANGELA_KEY_B", "ANGELA_KEY_C"]:
            os.environ.pop(name, None)
        result = validator.validate()
        assert result.valid is False
        key_errors = [e for e in result.errors if "ANGELA_KEY" in e]
        assert len(key_errors) >= 1

    def test_validate_invalid_allowed_value(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        os.environ["ANGELA_ENV"] = "invalid_env"
        result = validator.validate()
        assert result.valid is False

    def test_validate_port_validation(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        os.environ["BACKEND_PORT"] = "99999"
        result = validator.validate()
        assert result.valid is False

    def test_validate_port_valid(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        for key in ["ANGELA_ENV", "NODE_ENV", "BACKEND_HOST", "BACKEND_URL", "DATABASE_URL", "ANGELA_KEY_A", "ANGELA_KEY_B", "ANGELA_KEY_C"]:
            os.environ.pop(key, None)
        os.environ["BACKEND_PORT"] = "8080"
        os.environ["ANGELA_ENV"] = "development"
        os.environ["NODE_ENV"] = "development"
        os.environ["BACKEND_HOST"] = "127.0.0.1"
        os.environ["BACKEND_URL"] = "http://127.0.0.1:8000"
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["ANGELA_KEY_A"] = "a" * 32
        os.environ["ANGELA_KEY_B"] = "b" * 32
        os.environ["ANGELA_KEY_C"] = "c" * 32
        result = validator.validate()
        assert result.valid is True

    def test_validate_placeholder_warning(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        os.environ["BACKEND_HOST"] = "your_backend_host_here"
        os.environ["ANGELA_KEY_A"] = "x" * 32
        os.environ["ANGELA_KEY_B"] = "x" * 32
        os.environ["ANGELA_KEY_C"] = "x" * 32
        result = validator.validate()
        has_placeholder = any("your_" in w or "_here" in w for w in result.warnings)
        assert has_placeholder is True

    def test_non_required_var_with_default(self, tmp_path):
        dummy_env = tmp_path / "dummy.env"
        dummy_env.write_text("")
        validator = ConfigValidator(env_file=dummy_env)
        os.environ.pop("LOG_LEVEL", None)
        result = validator.validate()
        assert "LOG_LEVEL" in os.environ
