import unittest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.src.ai.dependency_manager import DependencyManager, DependencyStatus


class TestDependencyManager(unittest.TestCase):

    def setUp(self):
        """Set up a mock config for all tests."""
        self.test_config = {
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
        # Use mock_open to simulate reading the YAML config file when needed
        self.mock_yaml_read = mock_open(read_data=yaml.dump(self.test_config))

    @patch('importlib.import_module')
    def test_primary_dependency_available(self, mock_import_module):
        """Test that a primary dependency is loaded correctly."""
        mock_import_module.return_value = MagicMock()
        # Avoid file IO: create manager then inject config
        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._config = self.test_config
        manager._setup_dependency_statuses()

        self.assertTrue(manager.is_available('normal_lib'))
        status = manager.get_status('normal_lib')
        self.assertTrue(status.is_available)
        self.assertFalse(status.fallback_available)
        self.assertIsNotNone(manager.get_dependency('normal_lib'))
        # Ensure import was called with the correct name
        mock_import_module.assert_any_call('normal_lib')

    @patch('importlib.import_module')
    def test_fallback_dependency_used(self, mock_import_module):
        """Test that a fallback is used when the primary dependency is unavailable."""
        # Simulate ImportError for the primary, but success for the fallback
        mock_import_module.side_effect = [ImportError("No module named normal_lib"), MagicMock()]

        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._config = self.test_config
        manager._setup_dependency_statuses()

        self.assertTrue(manager.is_available('normal_lib'))
        status = manager.get_status('normal_lib')
        self.assertFalse(status.is_available)
        self.assertTrue(status.fallback_available)
        self.assertEqual(status.fallback_name, 'normal_fallback')
        self.assertIsNotNone(manager.get_dependency('normal_lib'))
        # Check that both primary and fallback were attempted
        mock_import_module.assert_any_call('normal_lib')
        mock_import_module.assert_any_call('normal_fallback')

    @patch('importlib.import_module', side_effect=ImportError("Module not found"))
    def test_all_dependencies_unavailable(self, mock_import_module):
        """Test behavior when a dependency and its fallbacks are all unavailable."""
        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._config = self.test_config
        manager._setup_dependency_statuses()

        self.assertFalse(manager.is_available('unavailable_lib'))
        status = manager.get_status('unavailable_lib')
        self.assertFalse(status.is_available)
        self.assertFalse(status.fallback_available)
        self.assertIsNone(manager.get_dependency('unavailable_lib'))

    @patch('importlib.import_module')
    def test_import_name_mapping(self, mock_import_module):
        """Test that package names with hyphens are correctly mapped to import names."""
        mock_import_module.return_value = MagicMock()
        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._config = self.test_config
        manager._setup_dependency_statuses()

        self.assertTrue(manager.is_available('paho-mqtt'))
        # The manager should have tried to import 'paho.mqtt.client' based on its internal map.
        mock_import_module.assert_any_call('paho.mqtt.client')

    @patch.dict('os.environ', {'UNIFIED_AI_ENV': 'production'})
    @patch('importlib.import_module', side_effect=ImportError("Module not found"))
    def test_fallbacks_disabled_in_production(self, mock_import_module):
        """Test that fallbacks are not used when disabled by the environment config."""
        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._config = self.test_config
        manager._setup_dependency_statuses()

        self.assertFalse(manager.is_available('normal_lib'))
        status = manager.get_status('normal_lib')
        self.assertFalse(status.is_available)
        self.assertFalse(status.fallback_available)
        # Ensure only the primary dependency was attempted
        mock_import_module.assert_called_once_with('normal_lib')

    def test_dependency_report_generation(self):
        """Test the human-readable report generation."""
        # Mock the internal state for a predictable report
        manager = DependencyManager(config_path="non_existent_path.yaml")
        manager._dependencies = {
            'lib_ok': DependencyStatus('lib_ok', is_available=True),
            'lib_fallback': DependencyStatus('lib_fallback', fallback_available=True, fallback_name='fb_1'),
            'lib_fail': DependencyStatus('lib_fail', error='Not found')
        }

        report = manager.get_dependency_report()
        self.assertIn("✓ Available (1):", report)
        self.assertIn("- lib_ok", report)
        self.assertIn("⚠ Using Fallbacks (1):", report)
        self.assertIn("- lib_fallback (using fb_1)", report)
        self.assertIn("✗ Unavailable (1):", report)
        self.assertIn("- lib_fail - Not found", report)

    def test_config_file_not_found(self):
        """Test that the manager uses a default config when the file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError) as mock_open_fn:
            with patch('importlib.import_module', side_effect=ImportError("Module not found")):
                manager = DependencyManager(config_path="non_existent_path.yaml")

        # Check that it tried to open the specified file
        mock_open_fn.assert_called_with("non_existent_path.yaml", 'r', encoding='utf-8')
        # Check that it fell back to the default config by checking for a default dependency
        self.assertIn('tensorflow', manager.get_all_status())
        self.assertTrue(manager.get_status('tensorflow').error is not None)


if __name__ == '__main__':
    unittest.main()