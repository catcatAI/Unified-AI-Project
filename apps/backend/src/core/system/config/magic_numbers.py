"""
ANGELA-MATRIX: [L2-L3] [β] [C] [L1]
P6-3: Centralized access to previously-hardcoded magic numbers.
All values loaded from TieredConfigLoader with inline fallback defaults.
"""

import logging
from typing import Any, Dict, Optional

_MAGIC_CACHE: Dict[str, Any] = {}


def _load_config() -> Optional[Dict[str, Any]]:
    """Try to load config via tiered_loader; return None if unavailable."""
    global _MAGIC_CACHE
    if _MAGIC_CACHE:
        return _MAGIC_CACHE
    try:
        from core.system.config.tiered_loader import get_config as _tiered_get
        from pathlib import Path as _Path

        configs: Dict[str, Any] = {}
        # Discover all tiered config files under the configs root
        from core.system.config.tiered_loader import _CONFIGS_ROOT
        if _CONFIGS_ROOT and _CONFIGS_ROOT.is_dir():
            for default_file in sorted(_CONFIGS_ROOT.rglob("*.default.yaml")):
                rel = default_file.relative_to(_CONFIGS_ROOT)
                # e.g. system/llm.default.yaml → dotted path "system/llm"
                dotted_path = "/".join(rel.parts[:-1] + (rel.stem.replace(".default", ""),))

                layer_config = _tiered_get(dotted_path)
                if layer_config and isinstance(layer_config, dict):
                    # Nest under path segments so dotted key lookups work
                    node: Any = configs
                    for seg in dotted_path.split("/"):
                        node = node.setdefault(seg, {})
                    node.update(layer_config)

        _MAGIC_CACHE = configs
    except Exception as e:
        # broad except intentional: config loading must never crash; silent fallback to defaults
        logger = logging.getLogger(__name__)
        logger.debug(f"Tiered config loading failed, using defaults: {e}")
        _MAGIC_CACHE = {}
    return _MAGIC_CACHE


def _get(key: str, default: Any = None) -> Any:
    """Look up a key from the config, falling back to default."""
    config = _load_config()
    if config is None:
        return default
    keys = key.split(".")
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, {})
        else:
            return default
    if isinstance(val, dict) and not val:
        return default
    return val if val is not None else default


def loop_sleep(key: str, default: float = 1.0) -> float:
    """Return a sleep interval (seconds) for the given loop key."""
    return float(_get(key, default))


def timeout_value(key: str, default: float = 30.0) -> float:
    """Return a timeout value (seconds) for the given key."""
    return float(_get(key, default))


def cache_value(key: str, default: int = 100) -> int:
    """Return a cache configuration value for the given key."""
    return int(_get(key, default))


def batch_value(key: str, default: int = 10) -> int:
    """Return a batch size for the given key."""
    return int(_get(key, default))


def llm_param(key: str, default: float = 0.7) -> float:
    """Return an LLM parameter value for the given key."""
    return float(_get(key, default))


def retry_value(key: str, default: int = 3) -> int:
    """Return a retry count for the given key."""
    return int(_get(key, default))


def threshold_value(key: str, default: float = 0.8) -> float:
    """Return a threshold value for the given key."""
    return float(_get(key, default))


def behavior_threshold(key: str, default: float = 0.5) -> float:
    """Return a behavior threshold for the given key."""
    return float(_get(key, default))


def behavior_executor(key: str, default: float = 0.5) -> float:
    """Return a behavior executor configuration value for the given key."""
    return float(_get(key, default))


def heartbeat_value(key: str, default: float = 1.0) -> float:
    """Return a heartbeat interval (seconds) for the given key."""
    return float(_get(key, default))


def timing_value(key: str, default: float = 0.1) -> float:
    """Return a timing value (seconds) for the given key."""
    return float(_get(key, default))


def confidence_value(key: str, default: float = 0.7) -> float:
    """Return a confidence threshold for the given key."""
    return float(_get(key, default))


def learning_rate(key: str, default: float = 0.05) -> float:
    """Return a learning rate for the given key."""
    return float(_get(key, default))


def latency_value(key: str, default: float = 10.0) -> float:
    """Return a latency value (ms) for the given key."""
    return float(_get(key, default))


def limit_value(key: str, default: int = 100) -> int:
    """Return a maximum limit/cap for the given key."""
    return int(_get(key, default))

