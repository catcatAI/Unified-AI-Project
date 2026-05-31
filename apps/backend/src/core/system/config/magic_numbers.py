"""
ANGELA-MATRIX: [L2-L3] [β] [C] [L1]
P6-3: Centralized access to previously-hardcoded magic numbers.
All values loaded from TieredConfigLoader with inline fallback defaults.
"""

from typing import Any, Dict, Optional


def _get_tiered_config(path: str) -> Dict[str, Any]:
    try:
        from core.system.config.tiered_loader import get_config
        return get_config(path)
    except Exception:
        return {}


def _nested_get(cfg: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    """Traverse a nested dict using dotted keys like 'loop.sleep_short'."""
    parts = dotted_key.split(".")
    current = cfg
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return default
    return current if current is not None else default


# ── Behavioral thresholds ──────────────────────────────────────────────

def behavior_threshold(key: str, default: Any = None) -> Any:
    """Get a behavioral threshold value from configs/standard/behavior/thresholds.*.yaml."""
    cfg = _get_tiered_config("standard/behavior/thresholds")
    return _nested_get(cfg, f"behavior.triggers.{key}", default)


def behavior_feedback(key: str, default: Any = None) -> Any:
    """Get a feedback-related threshold from thresholds config (behavior.feedback.*)."""
    cfg = _get_tiered_config("standard/behavior/thresholds")
    return _nested_get(cfg, f"feedback.{key}", default)


# ── Timing / sleep durations ──────────────────────────────────────────

def timing_value(dotted_key: str, default: Any = None) -> Any:
    """Get a timing value from configs/system/timing.*.yaml (e.g. 'loop.sleep_short')."""
    cfg = _get_tiered_config("system/timing")
    return _nested_get(cfg, f"timing.{dotted_key}", default)


def loop_sleep(key: str, default: float = 0.1) -> float:
    """Get a loop sleep duration (e.g. 'loop.sleep_short')."""
    return timing_value(key, default)


def timeout_value(key: str, default: float = 5.0) -> float:
    """Get a timeout value (e.g. 'timeout.short')."""
    return timing_value(key, default)


# ── LLM parameters ────────────────────────────────────────────────────

def llm_param(key: str, default: Any = None) -> Any:
    """Get an LLM parameter (e.g. 'llm.default_temperature')."""
    return timing_value(key, default)


# ── Heartbeat parameters ──────────────────────────────────────────────

def heartbeat_value(key: str, default: Any = None) -> Any:
    """Get a heartbeat parameter from timing config (e.g. 'heartbeat.max_interval')."""
    return timing_value(key, default)


# ── Executor parameters ─────────────────────────────────────────────────

def behavior_executor(key: str, default: Any = None) -> Any:
    """Get an executor parameter from thresholds config (behavior.executor.*)."""
    cfg = _get_tiered_config("standard/behavior/thresholds")
    return _nested_get(cfg, f"executor.{key}", default)
