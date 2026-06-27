"""Tests for config_loader - Config dataclasses, loading, validation, and helpers."""

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest

try:
    from apps.backend.src.core.config_loader import (
        BackendConfig,
        Config,
        DatabaseConfig,
        Environment,
        FeatureFlags,
        Live2DConfig,
        LoggingConfig,
        PerformanceConfig,
        PerformanceMode,
        SecurityConfig,
        _get_bool,
        _get_int,
        _get_str,
        _load_env_file,
        get_config,
        init_config,
        reload_config,
    )
except ImportError:
    import pytest; pytest.skip("Environment not defined", allow_module_level=True)


class TestEnvironment:
    def test_values(self):
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"


class TestPerformanceMode:
    def test_values(self):
        assert PerformanceMode.AUTO.value == "auto"
        assert PerformanceMode.LOW.value == "low"
        assert PerformanceMode.MEDIUM.value == "medium"
        assert PerformanceMode.HIGH.value == "high"
        assert PerformanceMode.ULTRA.value == "ultra"


class TestBackendConfig:
    def test_defaults(self):
        cfg = BackendConfig()
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8000
        assert cfg.url == "http://127.0.0.1:8000"

    def test_get_base_url(self):
        cfg = BackendConfig(host="0.0.0.0", port=3000)
        assert cfg.get_base_url() == "http://0.0.0.0:3000"


class TestSecurityConfig:
    def test_defaults_empty_keys(self):
        cfg = SecurityConfig()
        assert cfg.validate() is False

    def test_valid_keys(self):
        cfg = SecurityConfig(key_a="a" * 32, key_b="b" * 32, key_c="c" * 32)
        assert cfg.validate() is True

    def test_partial_keys(self):
        cfg = SecurityConfig(key_a="a" * 32, key_b="", key_c="c" * 32)
        assert cfg.validate() is False


class TestDatabaseConfig:
    def test_defaults(self):
        cfg = DatabaseConfig()
        assert cfg.url == "sqlite:///./angela.db"
        assert cfg.pool_size == 10

    def test_get_engine_args(self):
        cfg = DatabaseConfig(pool_size=5, max_overflow=10)
        args = cfg.get_engine_args()
        assert args["pool_size"] == 5
        assert args["max_overflow"] == 10


class TestLive2DConfig:
    def test_defaults(self):
        cfg = Live2DConfig()
        assert cfg.model_path is None

    def test_get_model_path(self):
        cfg = Live2DConfig(model_path=".")
        path = cfg.get_model_path()
        assert path is not None
        assert path.is_absolute()

    def test_get_model_path_none(self):
        cfg = Live2DConfig()
        assert cfg.get_model_path() is None


class TestPerformanceConfig:
    def test_default_mode_auto(self):
        cfg = PerformanceConfig()
        assert cfg.mode == PerformanceMode.AUTO

    def test_get_fps_settings_low(self):
        cfg = PerformanceConfig(mode=PerformanceMode.LOW)
        settings = cfg.get_fps_settings()
        assert settings["target_fps"] == 30

    def test_get_fps_settings_ultra(self):
        cfg = PerformanceConfig(mode=PerformanceMode.ULTRA)
        settings = cfg.get_fps_settings()
        assert settings["target_fps"] == 120
        assert settings["effects"] == "all"


class TestLoggingConfig:
    def test_default_level_info(self):
        cfg = LoggingConfig()
        assert cfg.get_log_level() == 20

    def test_get_log_level_debug(self):
        cfg = LoggingConfig(level="debug")
        assert cfg.get_log_level() == 10

    def test_get_log_level_unknown_defaults_info(self):
        cfg = LoggingConfig(level="unknown")
        assert cfg.get_log_level() == 20


class TestFeatureFlags:
    def test_defaults_all_true(self):
        flags = FeatureFlags()
        assert all([flags.enable_voice_recognition, flags.enable_tts,
                    flags.enable_websocket, flags.enable_mobile_bridge])


class TestHelperFunctions:
    def test_get_str_default(self):
        assert _get_str("NONEXISTENT_KEY_X123", "fallback") == "fallback"

    def test_get_str_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_STR_KEY", "hello")
        assert _get_str("TEST_STR_KEY", "fallback") == "hello"

    def test_get_int_default(self):
        assert _get_int("NONEXISTENT_INT_KEY", 42) == 42

    def test_get_int_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_KEY", "99")
        assert _get_int("TEST_INT_KEY", 42) == 99

    def test_get_int_invalid(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_BAD", "not-a-number")
        assert _get_int("TEST_INT_BAD", 42) == 42

    def test_get_bool_true_values(self, monkeypatch):
        for val in ("true", "1", "yes", "on"):
            monkeypatch.setenv("TEST_BOOL", val)
            assert _get_bool("TEST_BOOL") is True

    def test_get_bool_false_values(self, monkeypatch):
        for val in ("false", "0", "no", "off"):
            monkeypatch.setenv("TEST_BOOL", val)
            assert _get_bool("TEST_BOOL") is False

    def test_get_bool_default(self):
        assert _get_bool("NONEXISTENT_BOOL", True) is True

    def test_get_bool_default_false(self):
        assert _get_bool("NONEXISTENT_BOOL") is False

    def test_load_env_file(self, monkeypatch, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_ENV_KEY=from_file\n# comment\nEMPTY=\nKEEP=value\n", encoding="utf-8")
        _load_env_file(env_file)
        assert os.environ.get("TEST_ENV_KEY") == "from_file"
        assert os.environ.get("KEEP") == "value"


class TestConfig:
    def test_default_development(self):
        config = Config()
        assert config.environment == Environment.DEVELOPMENT
        assert config.debug_mode is True

    def test_load_defaults(self, monkeypatch):
        monkeypatch.delenv("ANGELA_ENV", raising=False)
        monkeypatch.delenv("BACKEND_HOST", raising=False)
        config = Config.load()
        assert config.environment == Environment.DEVELOPMENT
        assert config.backend.host == "127.0.0.1"

    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("ANGELA_ENV", "production")
        monkeypatch.setenv("BACKEND_HOST", "0.0.0.0")
        config = Config.load()
        assert config.environment == Environment.PRODUCTION
        assert config.backend.host == "0.0.0.0"

    def test_validate_production_debug_error(self):
        config = Config(environment=Environment.PRODUCTION, debug_mode=True)
        valid, errors = config.validate()
        assert valid is False
        assert any("调试" in e for e in errors)

    def test_validate_short_keys_error(self):
        config = Config(security=SecurityConfig(key_a="short", key_b="short", key_c="short"))
        valid, errors = config.validate()
        assert valid is False

    def test_validate_empty_db_url(self):
        config = Config(database=DatabaseConfig(url=""))
        valid, errors = config.validate()
        assert valid is False
        assert any("URL" in e for e in errors)

    def test_validate_invalid_fps(self):
        config = Config(performance=PerformanceConfig(target_fps=200))
        valid, errors = config.validate()
        assert valid is False

    def test_validate_valid_config(self):
        config = Config(
            environment=Environment.DEVELOPMENT,
            security=SecurityConfig(key_a="a" * 32, key_b="b" * 32, key_c="c" * 32),
            performance=PerformanceConfig(target_fps=60),
        )
        valid, errors = config.validate()
        assert valid is True
        assert errors == []

    def test_to_dict_masks_keys(self):
        config = Config(
            security=SecurityConfig(key_a="secret123", key_b="secret456", key_c="secret789"),
        )
        d = config.to_dict()
        assert d["security"]["key_a"] == "***"
        assert d["security"]["key_b"] == "***"
        assert d["security"]["key_c"] == "***"
        assert "secret" not in json.dumps(d["security"])

    def test_to_dict_empty_keys(self):
        config = Config()
        d = config.to_dict()
        assert d["security"]["key_a"] is None


class TestModuleFunctions:
    def test_get_config_returns_singleton(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_reload_config_creates_new(self):
        c1 = get_config()
        c2 = reload_config()
        assert c1 is not c2

    def test_init_config_valid(self, monkeypatch):
        monkeypatch.setenv("ANGELA_KEY_A", "a" * 32)
        monkeypatch.setenv("ANGELA_KEY_B", "b" * 32)
        monkeypatch.setenv("ANGELA_KEY_C", "c" * 32)
        init_config()
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)
        assert config.security.key_a == "a" * 32

    def test_init_config_invalid_raises(self, monkeypatch):
        monkeypatch.setenv("ANGELA_KEY_A", "short")
        monkeypatch.setenv("ANGELA_KEY_B", "short")
        monkeypatch.setenv("ANGELA_KEY_C", "short")
        with pytest.raises(ValueError, match="配置验证失败"):
            init_config()
