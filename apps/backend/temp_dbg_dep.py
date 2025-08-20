import yaml, os, sys
from unittest.mock import patch, mock_open
sys.path.insert(0, os.path.abspath('.'))
from src.core_ai.dependency_manager import DependencyManager

test_config = {
    'dependencies': {
        'core': [
            {'name': 'essential_lib', 'fallbacks': ['essential_fallback'], 'essential': True},
            {'name': 'normal_lib', 'fallbacks': ['normal_fallback'], 'essential': False},
            {'name': 'no_fallback_lib', 'fallbacks': [], 'essential': False},
            {'name': 'unavailable_lib', 'fallbacks': ['unavailable_fallback'], 'essential': False},
            {'name': 'paho-mqtt', 'fallbacks': ['asyncio-mqtt'], 'essential': True},
        ]
    },
    'environments': {
        'development': {
            'allow_fallbacks': True,
            'warn_on_fallback': True,
        },
        'production': {
            'allow_fallbacks': False,
        }
    }
}
mock_yaml_read = mock_open(read_data=yaml.dump(test_config))

with patch('builtins.open', mock_yaml_read):
    m = DependencyManager()
    print('config keys deps/core count:', len(m._config.get('dependencies',{}).get('core', [])))
    print('deps keys:', sorted(list(m._dependencies.keys())))
    print('env:', m._environment)