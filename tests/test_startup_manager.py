import unittest
import os
import sys
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent # Go up to Unified-AI-Project
sys.path.insert(0, str(project_root))

# Mock the dependency_manager and dependency_checker imports
# This is crucial to prevent actual imports and side effects during testing
sys.modules['src.core_ai.dependency_manager'] = MagicMock()
sys.modules['src.tools.dependency_checker'] = MagicMock()

from startup_with_fallbacks import StartupManager, is_dependency_available

# Restore original modules after tests
def tearDownModule():
    del sys.modules['src.core_ai.dependency_manager']
    del sys.modules['src.tools.dependency_checker']

class TestStartupManager(unittest.TestCase):

    def setUp(self):
        self.temp_config_path = Path(__file__).parent.parent / "dependency_config.yaml"
        self.original_config_content = None
        if self.temp_config_path.exists():
            with open(self.temp_config_path, 'r') as f:
                self.original_config_content = f.read()

    def tearDown(self):
        if self.original_config_content is not None:
            with open(self.temp_config_path, 'w') as f:
                f.write(self.original_config_content)
        elif self.temp_config_path.exists():
            os.remove(self.temp_config_path)

    def _write_temp_config(self, config_data):
        with open(self.temp_config_path, 'w') as f:
            yaml.dump(config_data, f)

    @patch('startup_with_fallbacks.is_dependency_available')
    def test_load_startup_modes_from_config(self, mock_is_dependency_available):
        mock_is_dependency_available.return_value = True # Assume all dependencies are available for this test

        test_config = {
            'installation': {
                'test_minimal': {
                    'description': 'Test minimal installation',
                    'packages': ['dep_a', 'dep_b'],
                    'features': ['basic_web'] # Changed from 'feature_x'
                },
                'test_full': {
                    'description': 'Test full installation',
                    'packages': ['dep_a', 'dep_b', 'dep_c'],
                    'features': ['basic_web', 'core_ai'] # Changed from 'feature_x', 'feature_y'
                }
            }
        }
        self._write_temp_config(test_config)

        manager = StartupManager()
        self.assertIn('test_minimal', manager.startup_modes)
        self.assertEqual(manager.startup_modes['test_minimal']['description'], 'Test minimal installation')
        self.assertEqual(manager.startup_modes['test_minimal']['required_deps'], ['dep_a', 'dep_b'])
        self.assertEqual(manager.startup_modes['test_minimal']['features'], ['basic_web'])

        self.assertIn('test_full', manager.startup_modes)
        self.assertEqual(manager.startup_modes['test_full']['description'], 'Test full installation')
        self.assertEqual(manager.startup_modes['test_full']['required_deps'], ['dep_a', 'dep_b', 'dep_c'])
        self.assertEqual(manager.startup_modes['test_full']['features'], ['basic_web', 'core_ai'])

    @patch('startup_with_fallbacks.is_dependency_available')
    def test_check_mode_compatibility(self, mock_is_dependency_available):
        test_config = {
            'installation': {
                'test_mode': {
                    'description': 'Test mode',
                    'packages': ['dep_a', 'dep_b'],
                    'features': ['basic_web'] # Changed from 'feature_x'
                }
            }
        }
        self._write_temp_config(test_config)
        manager = StartupManager()

        # Case 1: All required dependencies and feature dependencies available
        mock_is_dependency_available.side_effect = lambda dep: dep in ['dep_a', 'dep_b', 'Flask'] # 'Flask' is a dependency for 'basic_web'
        compatibility = manager.check_mode_compatibility('test_mode')
        self.assertTrue(compatibility['compatible'])
        self.assertEqual(compatibility['missing_required'], [])
        self.assertEqual(compatibility['available_features'], ['basic_web'])
        self.assertEqual(compatibility['disabled_features'], [])

        # Case 2: Missing required dependency
        mock_is_dependency_available.side_effect = lambda dep: dep in ['dep_a', 'Flask']
        compatibility = manager.check_mode_compatibility('test_mode')
        self.assertFalse(compatibility['compatible'])
        self.assertEqual(compatibility['missing_required'], ['dep_b'])
        self.assertEqual(compatibility['available_features'], ['basic_web'])
        self.assertEqual(compatibility['disabled_features'], [])

        # Case 3: Feature not available (dependency for feature is missing)
        mock_is_dependency_available.side_effect = lambda dep: dep in ['dep_a', 'dep_b'] # Flask (dependency for basic_web) is missing
        compatibility = manager.check_mode_compatibility('test_mode')
        self.assertTrue(compatibility['compatible'])
        self.assertEqual(compatibility['missing_required'], [])
        self.assertEqual(compatibility['available_features'], [])
        self.assertEqual(compatibility['disabled_features'], ['basic_web'])

    @patch('startup_with_fallbacks.is_dependency_available')
    def test_suggest_best_mode(self, mock_is_dependency_available):
        test_config = {
            'installation': {
                'mode_a': {
                    'description': 'Mode A',
                    'packages': ['dep_1'],
                    'features': ['basic_web'] # Changed from 'feat_a'
                },
                'mode_b': {
                    'description': 'Mode B',
                    'packages': ['dep_1', 'dep_2'],
                    'features': ['basic_web', 'core_ai'] # Changed from 'feat_a', 'feat_b'
                },
                'mode_c': {
                    'description': 'Mode C',
                    'packages': ['dep_3'],
                    'features': ['hsp_communication'] # Changed from 'feat_c'
                }
            }
        }
        self._write_temp_config(test_config)
        manager = StartupManager()

        # Case 1: All dependencies for mode_b are available, others are not fully
        mock_is_dependency_available.side_effect = lambda dep: dep in ['dep_1', 'dep_2', 'Flask', 'numpy'] # Flask for basic_web, numpy for core_ai
        best_mode = manager.suggest_best_mode()
        self.assertEqual(best_mode, 'mode_b')

        # Case 2: Only mode_a dependencies available
        mock_is_dependency_available.side_effect = lambda dep: dep in ['dep_1', 'Flask']
        best_mode = manager.suggest_best_mode()
        self.assertEqual(best_mode, 'mode_a')

        # Case 3: No modes fully compatible, should fallback to minimal (if defined) or the first compatible
        test_config_with_minimal = {
            'installation': {
                'minimal': {
                    'description': 'Minimal',
                    'packages': ['core_dep'],
                    'features': ['core_ai'] # Changed from 'basic_feature'
                },
                'mode_a': {
                    'description': 'Mode A',
                    'packages': ['dep_1'],
                    'features': ['basic_web']
                }
            }
        }
        self._write_temp_config(test_config_with_minimal)
        manager = StartupManager()
        mock_is_dependency_available.side_effect = lambda dep: dep == 'core_dep' or dep == 'numpy' # numpy for core_ai
        best_mode = manager.suggest_best_mode()
        self.assertEqual(best_mode, 'minimal')

if __name__ == '__main__':
    unittest.main()
