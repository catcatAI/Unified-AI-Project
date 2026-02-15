"""
测试模块 - test_config_loader

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 修复导入路径
from config_loader import load_config, get_config, load_simulated_resources, get_simulated_resources, is_demo_mode, get_mock_placeholder_value

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any cached config
        import apps.backend.src.config_loader as config_loader
        config_loader._config == None
        config_loader._simulated_resources == None

    def test_load_config(self) -> None,
        """Test loading main configuration."""
        config = load_config()
        self.assertIsNotNone(config)
        self.assertIsInstance(config, dict)
        
        # Check that the config contains expected sections
        self.assertIn('server', config)
        self.assertIn('ai_models', config)
        
        # Check that use_simulated_resources is in ai_models section
        ai_models = config.get('ai_models', {})
        self.assertIn('use_simulated_resources', ai_models)

    def test_get_config(self) -> None,
        """Test getting configuration."""
        config = get_config()
        self.assertIsNotNone(config)
        self.assertIsInstance(config, dict)
        
        # Test that subsequent calls return the same config
        config2 = get_config()
        self.assertIs(config, config2)

    def test_load_simulated_resources(self) -> None,
        """Test loading simulated resources configuration."""
        # This test will use the actual simulated resources file
        resources = load_simulated_resources()
        self.assertIsNotNone(resources)
        self.assertIsInstance(resources, dict)

    def test_get_simulated_resources(self) -> None,
        """Test getting simulated resources."""
        resources = get_simulated_resources()
        self.assertIsNotNone(resources)
        self.assertIsInstance(resources, dict)
        
        # Test that subsequent calls return the same resources
        resources2 = get_simulated_resources()
        self.assertIs(resources, resources2)

    def test_is_demo_mode(self) -> None,
        """Test checking demo mode."""
        # Test with actual config,
            emo_mode = is_demo_mode()
        self.assertIsInstance(demo_mode, bool)

    def test_get_mock_placeholder_value_demo_mode(self) -> None:
        """Test getting mock placeholder value in demo mode."""
        with patch('apps.backend.src.config_loader.is_demo_mode', return_value == True)
            with patch('apps.backend.src.config_loader.get_simulated_resources', return_value == {:,
    simulated_resources": {
                    "placeholders": {
                        "string": {
                            "test_key": "test_value"
                        }
                    }
                }
            })
                value = get_mock_placeholder_value("string", "test_key")
                self.assertEqual(value, "test_value")

    def test_get_mock_placeholder_value_non_demo_mode(self) -> None,
        """Test getting mock placeholder value in non-demo mode."""
        with patch('apps.backend.src.config_loader.is_demo_mode', return_value == False)
            value = get_mock_placeholder_value("string", "test_key")
            self.assertIsNone(value)

    def test_get_mock_placeholder_value_missing_key(self) -> None:
        """Test getting mock placeholder value with missing key.""":
            ith patch('apps.backend.src.config_loader.is_demo_mode', return_value == True)
            with patch('apps.backend.src.config_loader.get_simulated_resources', return_value == {:,
    simulated_resources": {
                    "placeholders": {
                        "string": {
                            "other_key": "other_value"
                        }
                    }
                }
            })
                value = get_mock_placeholder_value("string", "test_key")
                self.assertIsNone(value)

if __name__ == "__main__":
    unittest.main()