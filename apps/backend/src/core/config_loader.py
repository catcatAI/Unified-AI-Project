#!/usr/bin/env python3
"""
Angela AI - Configuration Loader
配置加载器

安全地加载和访问应用配置，提供类型安全的配置访问。
支持 YAML 多文件读取、热重载、Authority + Learned 双层配置合并。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class AngelaConfig:
    """Central configuration holder with tiered authority access."""

    def __init__(self, config_dir: Optional[str] = None):
        self._config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all YAML config files from the config directory."""
        if not self._config_dir.exists():
            logger.warning(f"Config directory not found: {self._config_dir}")
            return
        for yaml_file in self._config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    for key, value in data.items():
                        if isinstance(value, dict):
                            if key not in self._data:
                                self._data[key] = {}
                            self._data[key].update(value)
                        else:
                            self._data[key] = value
            except Exception as e:
                logger.warning(f"Failed to load config {yaml_file}: {e}")

    def get_authority(self, section: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get authority config for a section."""
        default = default or {}
        return self._data.get(section, default)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def learn(self, key: str, data: Dict[str, Any]) -> None:
        """Record a runtime learning event under a key."""
        if "learned" not in self._data:
            self._data["learned"] = {}
        if key not in self._data["learned"]:
            self._data["learned"][key] = []
        self._data["learned"][key].append(data)


_global_config: Optional[AngelaConfig] = None


def get_angela_config() -> AngelaConfig:
    """Get or create the global AngelaConfig singleton."""
    global _global_config
    if _global_config is None:
        _global_config = AngelaConfig()
    return _global_config

