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
        }
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


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the full application configuration."""
    return _CONFIG


def get_config(key: str, default: Any = None) -> Any:
    """Retrieve a specific config value by dotted key path."""
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
    return _CONFIG.get("bootstrap", {})


def get_formula_config(domain: str) -> Dict[str, Any]:
    """Return the formula sub-configuration for the given domain."""
    return _CONFIG.get("formula", {}).get(domain, {})
