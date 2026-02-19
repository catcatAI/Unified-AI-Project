import sys
import os
import logging
logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dependency_manager import DependencyManager
import yaml
from unittest.mock import patch, mock_open

test_config = {
'dependencies': {



        'core': [
        {'name': 'normal_lib', 'fallbacks': ['normal_fallback'], 'essential': False}]
        },

 'environments': {

    'development': {

 'allow_fallbacks': True,

 'warn_on_fallback': True,

 }

    }
}

print("Test config YAML:")
print(yaml.dump(test_config))

mock_yaml_read = mock_open(read_data=yaml.dump(test_config))

with patch('builtins.open', mock_yaml_read):
    manager = DependencyManager()
    print("\nManager created successfully!")
    print(f"Manager dependencies keys: {sorted(list(manager._dependencies.keys()))}")

    print(f"Normal_lib status: {manager.get_status('normal_lib')}")
    print(f"Is normal_lib available? {manager.is_available('normal_lib')}")

    
print("Testing imports and path...")
print(f"DependencyManager class location: {DependencyManager.__module__}")