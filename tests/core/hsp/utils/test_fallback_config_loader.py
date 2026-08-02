"""core.hsp.utils.fallback_config_loader 配置載入器測試"""

from apps.backend.src.core.hsp.utils.fallback_config_loader import (
    FallbackConfigLoader,
    get_config_loader,
    load_fallback_config,
    load_hsp_config,
)


class TestFallbackConfigLoader:
    def test_default_config_has_sections(self):
        loader = FallbackConfigLoader()
        config = loader.load_config()
        assert "hsp_fallback" in config
        assert "hsp_primary" in config

    def test_get_fallback_config(self):
        loader = FallbackConfigLoader()
        fb = loader.get_fallback_config()
        assert "protocols" in fb
        assert "http" in fb["protocols"]
        assert "file" in fb["protocols"]
        assert "memory" in fb["protocols"]

    def test_get_hsp_config(self):
        loader = FallbackConfigLoader()
        hsp = loader.get_hsp_config()
        assert "mqtt" in hsp
        assert "broker_address" in hsp["mqtt"]

    def test_is_fallback_enabled_default(self):
        loader = FallbackConfigLoader()
        assert loader.is_fallback_enabled() is True

    def test_get_protocol_config(self):
        loader = FallbackConfigLoader()
        http_cfg = loader.get_protocol_config("http")
        assert http_cfg["priority"] == 3
        assert http_cfg["host"] == "127.0.0.1"

    def test_get_message_config(self):
        loader = FallbackConfigLoader()
        msg = loader.get_message_config()
        assert msg["default_max_retries"] == 3

    def test_get_logging_config(self):
        loader = FallbackConfigLoader()
        lc = loader.get_logging_config()
        assert lc["level"] == "INFO"

    def test_validate_config_valid(self):
        loader = FallbackConfigLoader()
        assert loader.validate_config() is True

    def test_merge_configs(self):
        loader = FallbackConfigLoader()
        merged = loader._merge_configs(
            {"a": {"b": 1, "c": 2}, "x": 1},
            {"a": {"c": 3}, "x": 2},
        )
        assert merged == {"a": {"b": 1, "c": 3}, "x": 2}

    def test_save_load_roundtrip(self, tmp_path):
        loader = FallbackConfigLoader(config_path=str(tmp_path / "cfg.yaml"))
        cfg = loader.load_config()
        loader.save_config(cfg, str(tmp_path / "cfg.yaml"))
        from pathlib import Path

        assert Path(tmp_path / "cfg.yaml").exists()
        loader2 = FallbackConfigLoader(config_path=str(tmp_path / "cfg.yaml"))
        loaded = loader2.load_config()
        assert loaded == cfg


class TestModuleLevelFunctions:
    def test_load_fallback_config(self):
        fb = load_fallback_config()
        assert "protocols" in fb

    def test_load_hsp_config(self):
        hsp = load_hsp_config()
        assert "mqtt" in hsp

    def test_get_config_loader_singleton(self):
        loader1 = get_config_loader()
        loader2 = get_config_loader()
        assert loader1 is loader2
