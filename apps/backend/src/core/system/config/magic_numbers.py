"""
ANGELA-MATRIX: [L2-L3] [β] [C] [L1]
P6-3: Centralized access to previously-hardcoded magic numbers.
All values loaded from TieredConfigLoader with inline fallback defaults.
"""

import logging
from typing import Any, Dict, Optional, Union

_MAGIC_CACHE: Dict[str, Any] = {}
_HARDWARE_PROFILE: Optional[Any] = None  # lazy-loaded HardwareProfile singleton


def _get_hardware_profile() -> Optional[Any]:
    """Lazy-load and cache HardwareProfile singleton.

    Returns None if import fails (graceful degradation).
    """
    global _HARDWARE_PROFILE
    if _HARDWARE_PROFILE is None:
        try:
            from core.system.config.hardware_profile import HardwareProfile

            _HARDWARE_PROFILE = HardwareProfile()
            logger = logging.getLogger(__name__)
            logger.info(
                "HardwareProfile activated: %s (multiplier=%.1f)",
                _HARDWARE_PROFILE.scenario.value,
                _HARDWARE_PROFILE.profile.base_multiplier,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.debug("HardwareProfile unavailable, using defaults: %s", e)
            _HARDWARE_PROFILE = False  # sentinel: don't retry
    return _HARDWARE_PROFILE if _HARDWARE_PROFILE is not False else None


def _load_config() -> Optional[Dict[str, Any]]:
    """Try to load config via tiered_loader; return None if unavailable."""
    global _MAGIC_CACHE
    if _MAGIC_CACHE:
        return _MAGIC_CACHE
    try:
        from pathlib import Path as _Path

        from core.system.config.tiered_loader import get_config as _tiered_get

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


def _safe_float(value: Any, default: Any = None) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default if default is not None else value


def _safe_int(value: Any, default: Any = None) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default if default is not None else value


def loop_sleep(key: str, default: float = 1.0) -> float:
    """Get loop sleep interval with hardware-aware frequency scaling.

    Returns the configured interval from tiered config, scaled by the
    HardwareProfile's base_multiplier so that loops run faster on
    high-performance hardware and slower on power-constrained devices.
    """
    base = _safe_float(_get(key, default), default)
    profile = _get_hardware_profile()
    if profile is not None:
        return profile.apply_multiplier(base)
    return base


def timeout_value(key: str, default: float = 30.0) -> float:
    return _safe_float(_get(key, default), default)


def cache_value(key: str, default: int = 100) -> int:
    return _safe_int(_get(key, default), default)


def batch_value(key: str, default: int = 10) -> int:
    return _safe_int(_get(key, default), default)


def llm_param(key: str, default: float = 0.7) -> float:
    return _safe_float(_get(key, default), default)


def retry_value(key: str, default: int = 3) -> int:
    return _safe_int(_get(key, default), default)


def threshold_value(key: str, default: float = 0.8) -> float:
    return _safe_float(_get(key, default), default)


def behavior_threshold(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def behavior_feedback(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def behavior_executor(key: str, default: float = 0.5) -> float:
    return _safe_float(_get(key, default), default)


def _apply_hw_multiplier(value: float) -> float:
    if not isinstance(value, (int, float)):
        return value
    profile = _get_hardware_profile()
    if profile is not None:
        return profile.apply_multiplier(value)
    return value


def heartbeat_value(key: str, default: float = 1.0) -> float:
    return _apply_hw_multiplier(_safe_float(_get(key, default), default))


def timing_value(key: str, default: float = 0.1) -> float:
    return _apply_hw_multiplier(_safe_float(_get(key, default), default))


def confidence_value(key: str, default: float = 0.7) -> float:
    return _safe_float(_get(key, default), default)


def learning_rate(key: str, default: float = 0.05) -> float:
    return _safe_float(_get(key, default), default)


def latency_value(key: str, default: float = 10.0) -> float:
    return _safe_float(_get(key, default), default)


def limit_value(key: str, default: int = 100) -> int:
    return _safe_int(_get(key, default), default)


def lifecycle_value(key: str, default: float = 0.5) -> float:
    """Lifecycle feedback threshold (e.g. success_rate_low, success_rate_high, adjustment)."""
    return _safe_float(_get(key, default), default)
