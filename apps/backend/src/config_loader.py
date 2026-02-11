# from diagnose_base_agent import
# TODO: Fix import - module 'yaml' not found
# from typing import Dict, Any
# import os

_config = None
_simulated_resources = None

def load_config(config_path="configs/config.yaml"):
    """
    Loads the main configuration file.
    """
    global _config
    if _config is None:
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        full_config_path = os.path.join(backend_root, config_path)
        with open(full_config_path, 'r') as f:
            _config = yaml.safe_load(f)
    return _config if _config is not None else {}

def get_config():
    """
    Returns the loaded configuration.
    """
    if _config is None:
        load_config()
    return _config if _config is not None else {}

def load_simulated_resources(config_path="configs/simulated_resources.yaml"):
    """
    Loads the simulated resources configuration file.
    """
    global _simulated_resources
    if _simulated_resources is None:
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        full_config_path = os.path.join(backend_root, config_path)
        with open(full_config_path, 'r') as f:
            _simulated_resources = yaml.safe_load(f)
    return _simulated_resources if _simulated_resources is not None else {}

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
    placeholders = sim_resources.get("simulated_resources", {}).get("placeholders", {}) if sim_resources else {}
    return placeholders.get(placeholder_type, {}).get(placeholder_key)
