import unittest
import yaml
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_different_patch_approaches():
    """測試不同的patch方法來確定哪種有效。"""
    
    test_config = {
        'dependencies': {
            'core': [
                {'name': 'normal_lib', 'fallbacks': ['normal_fallback'], 'essential': False},
            ]
        },
        'environments': {
            'development': {
                'allow_fallbacks': True,
                'warn_on_fallback': True,
            }
        }
    }
    
    mock_yaml_read = mock_open(read_data=yaml.dump(test_config))
    
    print("=== 測試1: patch builtins.open ===")
    with patch('builtins.open', mock_yaml_read) as mock_file:
        try:
            from src.core_ai.dependency_manager import DependencyManager
            manager = DependencyManager(config_path="test_config.yaml")
            print(f"Open調用次數: {mock_file.call_count}")
            print(f"調用參數: {mock_file.call_args_list}")
            print(f"已跟蹤的依賴項: {list(manager._dependencies.keys())}")
        except Exception as e:
            print(f"錯誤: {e}")
    
    print("\n=== 測試2: 檢查實際模組內的open引用 ===")
    import src.core_ai.dependency_manager as dm_module
    print(f"模組中的open函數: {dm_module.open}")
    print(f"open是否為內建: {dm_module.open is open}")
    
if __name__ == "__main__":
    test_different_patch_approaches()