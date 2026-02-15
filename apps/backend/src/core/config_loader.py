#!/usr/bin/env python3
"""
Angela AI - Configuration Loader
配置加载器

安全地加载和访问应用配置，提供类型安全的配置访问。
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
logger = logging.getLogger(__name__)


T = TypeVar('T')


class Environment(Enum):
    """运行环境"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class PerformanceMode(Enum):
    """性能模式"""
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class BackendConfig:
    """后端配置"""
    host: str = "127.0.0.1"
    port: int = 8000
    url: str = "http://127.0.0.1:8000"
    
    def get_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class SecurityConfig:
    """安全配置"""
    key_a: str = ""
    key_b: str = ""
    key_c: str = ""
    
    def validate(self) -> bool:
        """验证密钥配置"""
        return all(len(key) >= 32 for key in [self.key_a, self.key_b, self.key_c])


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///./angela.db"
    pool_size: int = 10
    max_overflow: int = 20
    
    def get_engine_args(self) -> Dict[str, Any]:
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
        }


@dataclass
class Live2DConfig:
    """Live2D 配置"""
    model_path: Optional[str] = None
    sdk_cdn: str = "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"
    
    def get_model_path(self) -> Optional[Path]:
        if self.model_path:
            return Path(self.model_path).resolve()
        return None


@dataclass
class PerformanceConfig:
    """性能配置"""
    mode: PerformanceMode = PerformanceMode.AUTO
    target_fps: int = 60
    enable_hardware_acceleration: bool = True
    
    def get_fps_settings(self) -> Dict[str, Any]:
        mode_settings = {
            PerformanceMode.LOW: {"target_fps": 30, "effects": "basic"},
            PerformanceMode.MEDIUM: {"target_fps": 45, "effects": "standard"},
            PerformanceMode.HIGH: {"target_fps": 60, "effects": "enhanced"},
            PerformanceMode.ULTRA: {"target_fps": 120, "effects": "all"},
        }
        return mode_settings.get(self.mode, {"target_fps": self.target_fps, "effects": "auto"})


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "info"
    file_path: str = "./logs/angela.log"
    max_size: str = "10MB"
    backup_count: int = 5
    
    def get_log_level(self) -> int:
        levels = {"debug": 10, "info": 20, "warning": 30, "error": 40, "critical": 50}
        return levels.get(self.level.lower(), 20)


@dataclass
class FeatureFlags:
    """功能开关"""
    enable_voice_recognition: bool = True
    enable_tts: bool = True
    enable_websocket: bool = True
    enable_mobile_bridge: bool = True
    
    @classmethod
    def from_env(cls) -> "FeatureFlags":
        return cls(
            enable_voice_recognition=_get_bool("ENABLE_VOICE_RECOGNITION", True),
            enable_tts=_get_bool("ENABLE_TTS", True),
            enable_websocket=_get_bool("ENABLE_WEBSOCKET", True),
            enable_mobile_bridge=_get_bool("ENABLE_MOBILE_BRIDGE", True),
        )


@dataclass
class Config:
    """主配置类"""
    environment: Environment = Environment.DEVELOPMENT
    backend: BackendConfig = field(default_factory=BackendConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    live2d: Live2DConfig = field(default_factory=Live2DConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # 调试和开发设置
    debug_mode: bool = True
    hot_reload: bool = True
    enable_cors: bool = True
    
    # 测试配置
    test_mode: bool = False
    mock_external_apis: bool = False
    
    @classmethod
    def load(cls, env_file: Optional[Path] = None) -> "Config":
        """加载配置"""
        # 加载 .env 文件
        if env_file:
            _load_env_file(env_file)
        
        # 创建配置对象
        return cls(
            environment=Environment(_get_str("ANGELA_ENV", "development")),
            backend=BackendConfig(
                host=_get_str("BACKEND_HOST", "127.0.0.1"),
                port=_get_int("BACKEND_PORT", 8000),
                url=_get_str("BACKEND_URL", "http://127.0.0.1:8000"),
            ),
            security=SecurityConfig(
                key_a=_get_str("ANGELA_KEY_A", ""),
                key_b=_get_str("ANGELA_KEY_B", ""),
                key_c=_get_str("ANGELA_KEY_C", ""),
            ),
            database=DatabaseConfig(
                url=_get_str("DATABASE_URL", "sqlite:///./angela.db"),
                pool_size=_get_int("DATABASE_POOL_SIZE", 10),
                max_overflow=_get_int("DATABASE_MAX_OVERFLOW", 20),
            ),
            live2d=Live2DConfig(
                model_path=_get_str("LIVE2D_MODEL_PATH"),
                sdk_cdn=_get_str("LIVE2D_SDK_CDN", "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"),
            ),
            performance=PerformanceConfig(
                mode=PerformanceMode(_get_str("PERFORMANCE_MODE", "auto")),
                target_fps=_get_int("TARGET_FPS", 60),
                enable_hardware_acceleration=_get_bool("ENABLE_HARDWARE_ACCELERATION", True),
            ),
            logging=LoggingConfig(
                level=_get_str("LOG_LEVEL", "info"),
                file_path=_get_str("LOG_FILE", "./logs/angela.log"),
                max_size=_get_str("LOG_MAX_SIZE", "10MB"),
                backup_count=_get_int("LOG_BACKUP_COUNT", 5),
            ),
            features=FeatureFlags.from_env(),
            debug_mode=_get_bool("DEBUG_MODE", True),
            hot_reload=_get_bool("HOT_RELOAD", True),
            enable_cors=_get_bool("ENABLE_CORS", True),
            test_mode=_get_bool("TEST_MODE", False),
            mock_external_apis=_get_bool("MOCK_EXTERNAL_APIS", False),
        )
    
    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        errors = []
        
        # 验证环境
        if self.environment == Environment.PRODUCTION and self.debug_mode:
            errors.append("生产环境不应启用调试模式")
        
        # 验证安全配置
        if not self.security.validate():
            errors.append("安全密钥配置无效，密钥长度至少需要 32 字符")
        
        # 验证数据库
        if not self.database.url:
            errors.append("数据库 URL 不能为空")
        
        # 验证性能配置
        if self.performance.target_fps < 30 or self.performance.target_fps > 144:
            errors.append(f"目标帧率无效: {self.performance.target_fps}")
        
        return (len(errors) == 0, errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment.value,
            "backend": {
                "host": self.backend.host,
                "port": self.backend.port,
                "url": self.backend.url,
            },
            "security": {
                "key_a": "***" if self.security.key_a else None,
                "key_b": "***" if self.security.key_b else None,
                "key_c": "***" if self.security.key_c else None,
            },
            "database": {
                "url": self.database.url,
                "pool_size": self.database.pool_size,
            },
            "performance": {
                "mode": self.performance.mode.value,
                "target_fps": self.performance.target_fps,
            },
            "logging": {
                "level": self.logging.level,
                "file_path": self.logging.file_path,
            },
            "features": {
                "enable_voice_recognition": self.features.enable_voice_recognition,
                "enable_tts": self.features.enable_tts,
                "enable_websocket": self.features.enable_websocket,
            },
        }


# 辅助函数
def _load_env_file(env_file: Path) -> None:
    """加载 .env 文件"""
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def _get_str(key: str, default: Optional[str] = None) -> str:
    """获取字符串配置"""
    return os.environ.get(key, default or "")


def _get_int(key: str, default: int = 0) -> int:
    """获取整数配置"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_bool(key: str, default: bool = False) -> bool:
    """获取布尔配置"""
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config(env_file: Optional[Path] = None) -> Config:
    """重新加载配置"""
    global _config
    _config = Config.load(env_file)
    return _config


def init_config(env_file: Optional[Path] = None) -> None:
    """初始化配置"""
    global _config
    _config = Config.load(env_file)
    
    # 验证配置
    valid, errors = _config.validate()
    if not valid:
        error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)


if __name__ == "__main__":
    # 测试配置加载
    config = Config.load()
    logger.info(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))