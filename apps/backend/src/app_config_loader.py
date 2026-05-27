import yaml
import os
from typing import Dict, Any, Optional

_config = None
_simulated_resources = None
_formula_configs = {}


def load_yaml(file_path: str) -> Dict[str, Any]:
    """Helper to load a YAML file relative to backend root."""
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(backend_root, file_path)
    if not os.path.exists(full_path):
        return {}
    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path="system/core"):
    """
    Redirects to TieredConfigLoader.
    """
    from core.system.config.tiered_loader import get_config
    return get_config(config_path)


def get_formula_config(name: str) -> Dict[str, Any]:
    """
    Redirects to tiered standard/science path.
    """
    from core.system.config.tiered_loader import get_config
    # Mapping old names to new tiered paths
    mapping = {
        "biological": "standard/science/biological",
        "spatial": "standard/science/spatial",
        "dynamic": "standard/behavior/dynamic",
        "behavior": "standard/behavior/behavior",
        "matrix": "standard/matrix/matrix",
        "prompts": "standard/narrative/prompts",
        "mods": "mods/active_mods"
    }
    return get_config(mapping.get(name, f"standard/science/{name}"))


def get_bootstrap_config() -> Dict[str, Any]:
    """Retrieves infrastructure bootstrap configuration from tiered system."""
    from core.system.config.tiered_loader import get_config
    return get_config("system/bootstrap")


# DORMANT FACTORY (not called externally)
def get_config():
    """
    Returns the loaded configuration.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config if _config is not None else {}


def load_simulated_resources(config_path="configs/simulated_resources.yaml"):
    """
    Loads the simulated resources configuration file.
    """
    global _simulated_resources
    if _simulated_resources is None:
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        full_config_path = os.path.join(backend_root, config_path)
        with open(full_config_path, "r", encoding="utf-8") as f:
            _simulated_resources = yaml.safe_load(f)
    return _simulated_resources if _simulated_resources is not None else {}


# DORMANT FACTORY (not called externally)
def get_simulated_resources():
    """
    Returns the loaded simulated resources.
    """
    if _simulated_resources is None:
        load_simulated_resources()
    return _simulated_resources if _simulated_resources is not None else {}


def is_demo_mode():
    """
    Checks if the application is running in demo mode.
    """
    config = get_config()
    ai_models_config = config.get("ai_models", {}) if config else {}
    return ai_models_config.get("use_simulated_resources", False)


def get_mock_placeholder_value(placeholder_type, placeholder_key):
    """
    Retrieves a mock value for a given placeholder type and key from the
    simulated resources configuration.
    """
    if not is_demo_mode():
        return None

    sim_resources = get_simulated_resources()
    placeholders = (
        sim_resources.get("simulated_resources", {}).get("placeholders", {})
        if sim_resources
        else {}
    )
    return placeholders.get(placeholder_type, {}).get(placeholder_key)
