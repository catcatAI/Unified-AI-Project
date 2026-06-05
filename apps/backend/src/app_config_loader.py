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
        }
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
