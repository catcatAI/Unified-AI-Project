# ANGELA-MATRIX: L0[基础层] [A] L1

"""Environment utilities - 统一的环境变量与配置管理"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_env(key: str, default: Any = None) -> Any:
    """获取环境变量值"""
    return os.environ.get(key, default)


def get_int_env(key: str, default: int = 0) -> int:
    """获取整数类型的环境变量"""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        logger.warning(f"[EnvUtils] Invalid int env '{key}': {val}")
        return default


def get_float_env(key: str, default: float = 0.0) -> float:
    """获取浮点数类型的环境变量"""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        result = float(val)
        if result != result:  # NaN check (NaN != NaN)
            logger.warning(f"[EnvUtils] Invalid float env '{key}': {val}")
            return default
        return result
    except (ValueError, TypeError):
        logger.warning(f"[EnvUtils] Invalid float env '{key}': {val}")
        return default


def get_bool_env(key: str, default: bool = False) -> bool:
    """获取布尔类型的环境变量"""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def load_env_file(filepath: str) -> Dict[str, str]:
    """加载 .env 格式的文件"""
    result: Dict[str, str] = {}
    if not os.path.isfile(filepath):
        logger.warning(f"[EnvUtils] Env file not found: {filepath}")
        return result
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("\"'")
            result[key] = val
            os.environ[key] = val
    logger.info(f"[EnvUtils] Loaded {len(result)} vars from {filepath}")
    return result
