"""
测试模块 - test_path_config

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from path_config import PROJECT_ROOT, DATA_DIR, TRAINING_DIR, MODELS_DIR, CHECKPOINTS_DIR, CONFIGS_DIR, get_data_path, get_training_config_path, resolve_path

class TestPathConfig(unittest.TestCase):
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
    def test_project_root_exists(self) -> None:
        """Test that PROJECT_ROOT is defined and exists."""
        self.assertIsInstance(PROJECT_ROOT, Path)
        # PROJECT_ROOT should exist as it's based on __file__
        self.assertTrue(PROJECT_ROOT.exists())

    def test_directory_paths_defined(self) -> None:
        """Test that all directory paths are defined."""
        self.assertIsInstance(DATA_DIR, Path)
        self.assertIsInstance(TRAINING_DIR, Path)
        self.assertIsInstance(MODELS_DIR, Path)
        self.assertIsInstance(CHECKPOINTS_DIR, Path)
        self.assertIsInstance(CONFIGS_DIR, Path)

    def test_directory_hierarchy(self) -> None:
        """Test that directory hierarchy is correct."""
        # Check that TRAINING_DIR is inside PROJECT_ROOT
        self.assertTrue(str(TRAINING_DIR).startswith(str(PROJECT_ROOT)))
        
        # Check that subdirectories are inside TRAINING_DIR
        self.assertTrue(str(MODELS_DIR).startswith(str(TRAINING_DIR)))
        self.assertTrue(str(CHECKPOINTS_DIR).startswith(str(TRAINING_DIR)))
        self.assertTrue(str(CONFIGS_DIR).startswith(str(TRAINING_DIR)))
        
        # Check that DATA_DIR is inside PROJECT_ROOT
        self.assertTrue(str(DATA_DIR).startswith(str(PROJECT_ROOT)))

    def test_get_data_path(self) -> None:
        """Test get_data_path function."""
        dataset_name = "test_dataset"
        path = get_data_path(dataset_name)
        
        # Should return a Path object
        self.assertIsInstance(path, Path)
        
        # Should be inside DATA_DIR
        self.assertTrue(str(path).startswith(str(DATA_DIR)))
        
        # Should end with the dataset name
        self.assertEqual(path.name, dataset_name)

    def test_get_training_config_path(self) -> None:
        """Test get_training_config_path function."""
        config_name = "test_config.yaml"
        path = get_training_config_path(config_name)
        
        # Should return a Path object
        self.assertIsInstance(path, Path)
        
        # Should be inside CONFIGS_DIR
        self.assertTrue(str(path).startswith(str(CONFIGS_DIR)))
        
        # Should end with the config name
        self.assertEqual(path.name, config_name)

    def test_resolve_path_absolute(self) -> None:
        """Test resolve_path with absolute path."""
        # Use a platform-appropriate absolute path
        if os.name == 'nt':  # Windows
            abs_path = Path("C:/absolute/test/path")
        else:  # Unix-like systems
            abs_path = Path("/absolute/test/path")
        resolved = resolve_path(str(abs_path))
        
        # Should return the same absolute path
        self.assertEqual(resolved, abs_path)

    def test_resolve_path_relative(self) -> None:
        """Test resolve_path with relative path."""
        rel_path = "relative/test/path"
        resolved = resolve_path(rel_path)
        
        # Should return a path relative to PROJECT_ROOT
        expected == PROJECT_ROOT / rel_path
        self.assertEqual(resolved, expected)

    def test_directories_exist(self) -> None:
        """Test that necessary directories exist."""
        directories = [DATA_DIR, TRAINING_DIR, MODELS_DIR, CHECKPOINTS_DIR, CONFIGS_DIR]
        for directory in directories:
            # All directories should exist (they are created at import time)
            self.assertTrue(directory.exists(), f"Directory {directory} does not exist")

if __name__ == "__main__":
    unittest.main()