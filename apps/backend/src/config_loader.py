import os
import yaml
from typing import Dict, Any

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Loads the application configuration from a YAML file.
    The default path is 'configs/config.yaml'.
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Handle the case where the config file doesn't exist
        print(f"Warning: Configuration file not found at {config_path}. Using default empty config.")
        return {}
    except yaml.YAMLError as e:
        # Handle errors during YAML parsing
        print(f"Error parsing YAML file at {config_path}: {e}")
        return {}
