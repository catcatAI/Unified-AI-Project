"""core.config 配置模块测试"""

from unittest.mock import patch

from apps.backend.src.core.config.level5_config import (
    Level5PerformanceMetrics,
    Level5SystemMonitor,
    get_static_level5_capabilities,
)
from apps.backend.src.core.config.system_config import (
    get_ai_ops_config,
    get_hsp_config,
    get_memory_config,
    get_system_config,
    get_training_config,
)


class TestGetSystemConfig:
    def test_returns_all_sections(self):
        config = get_system_config()
        for section in ("environment", "debug", "host", "port", "ai_ops", "hsp", "memory", "training"):
            assert section in config

    @patch.dict("os.environ", {"LOG_LEVEL": "INFO"}, clear=True)
    def test_has_defaults(self):
        config = get_system_config()
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 8000
        assert config["log_level"] == "INFO"


class TestGetSubConfigs:
    def test_get_ai_ops_config(self):
        cfg = get_ai_ops_config()
        assert "enabled" in cfg
        assert "redis_host" in cfg

    def test_get_hsp_config(self):
        cfg = get_hsp_config()
        assert "mqtt_broker" in cfg
        assert "mqtt_port" in cfg

    def test_get_memory_config(self):
        cfg = get_memory_config()
        assert "chroma_host" in cfg
        assert "vector_dimension" in cfg

    def test_get_training_config(self):
        cfg = get_training_config()
        assert "auto_training" in cfg
        assert "batch_size" in cfg


class TestGetStaticLevel5Capabilities:
    def test_returns_capability_set(self):
        caps = get_static_level5_capabilities()
        assert caps["system_level"] == "Level 5 AGI"
        assert "global_intelligence" in caps["capabilities"]
        assert "metacognitive_capabilities" in caps["capabilities"]
        assert "specifications" in caps


class TestLevel5Classes:
    def test_metrics_initializable(self):
        metrics = Level5PerformanceMetrics()
        assert hasattr(metrics, "calculate_real_time_metrics")
        assert hasattr(metrics, "knowledge_processing_rate")

    def test_monitor_initializable(self):
        monitor = Level5SystemMonitor()
        assert hasattr(monitor, "get_current_status")
        assert hasattr(monitor, "start_monitoring")
