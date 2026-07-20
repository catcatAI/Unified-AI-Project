# =============================================================================
# ANGELA-MATRIX: L0[基础层] [A] L1
# =============================================================================

"""Application-level configuration loader for Angela AI."""

from typing import Any, Dict, Optional

_CONFIG: Dict[str, Any] = {
    "bootstrap": {
        "hardware": {
            "performance_tier": "standard",
            "gpu_enabled": False,
        },
        "hardware_tiers": {
            "Extreme": {"score_threshold": 80, "max_fps": 60, "llm_model": "gemini-1.5-pro-latest", "precision": 1.0},
            "High": {"score_threshold": 60, "max_fps": 60, "llm_model": "gemini-pro", "precision": 0.8},
            "Medium": {"score_threshold": 40, "max_fps": 30, "llm_model": "gemini-pro", "precision": 0.5},
            "Low": {"score_threshold": 0, "max_fps": 24, "llm_model": "gemini-1.5-flash", "precision": 0.3},
        },
        "scoring_weights": {
            "cpu_core_multiplier": 2,
            "memory_gb_multiplier": 1.25,
            "gpu_rtx_bonus": 40,
            "gpu_standard_bonus": 30,
        },
    },
    "formula": {
        "spatial": {
            "screen": {"width": 1920, "height": 1080},
        },
        "biological": {
            "hormones": {
                "ADRENALINE": {"base_level": 10.0, "production_rate": 2.0, "half_life": 6.0},
                "CORTISOL": {"base_level": 15.0, "production_rate": 1.0, "half_life": 90.0},
                "DOPAMINE": {"base_level": 50.0, "production_rate": 1.5, "half_life": 30.0},
                "SEROTONIN": {"base_level": 60.0, "production_rate": 0.8, "half_life": 240.0},
                "OXYTOCIN": {"base_level": 40.0, "production_rate": 1.0, "half_life": 20.0},
                "MELATONIN": {"base_level": 10.0, "production_rate": 3.0, "half_life": 45.0},
                "ENDORPHIN": {"base_level": 30.0, "production_rate": 0.5, "half_life": 240.0},
                "NORADRENALINE": {"base_level": 10.0, "production_rate": 2.0, "half_life": 6.0},
                "TESTOSTERONE": {"base_level": 35.0, "production_rate": 0.3, "half_life": 120.0},
                "ESTROGEN": {"base_level": 30.0, "production_rate": 0.3, "half_life": 720.0},
            },
            "stress": {
                "half_life": 30.0,
            },
        },
    },
}


_bootstrap_merged = False


def _merge_bootstrap_overrides() -> None:
    """Merge the canonical tiered bootstrap config over the hardcoded defaults.

    The authoritative bootstrap config (hardware_tiers, scoring_weights, paths)
    lives in ``configs/system/bootstrap.{default,user,evolved}.yaml``.  The
    hardcoded ``_CONFIG`` only provides safe fallbacks.
    """
    global _bootstrap_merged
    if _bootstrap_merged:
        return
    try:
        from core.system.config.tiered_loader import get_config as _tiered_get

        bootstrap = _tiered_get("system/bootstrap")
        if isinstance(bootstrap, dict) and bootstrap:
            _CONFIG.setdefault("bootstrap", {}).update(bootstrap)
    except Exception:
        # Fall back to hardcoded defaults if the tiered loader is unavailable.
        pass
    finally:
        _bootstrap_merged = True


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the full application configuration."""
    _merge_bootstrap_overrides()
    return _CONFIG


def get_config(key: str, default: Any = None) -> Any:
    """Retrieve a specific config value by dotted key path."""
    _merge_bootstrap_overrides()
    keys = key.split(".")
    val: Any = _CONFIG
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
        if val is None:
            return default
    return val


def get_bootstrap_config() -> Dict[str, Any]:
    """Return the bootstrap sub-configuration."""
    _merge_bootstrap_overrides()
    return _CONFIG.get("bootstrap", {})


def get_formula_config(domain: str) -> Dict[str, Any]:
    """Return the formula sub-configuration for the given domain."""
    return _CONFIG.get("formula", {}).get(domain, {})
