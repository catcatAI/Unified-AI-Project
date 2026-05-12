"""Test Core Services - FastAPI server tests"""
import unittest
import sys
import os
from pathlib import Path

src_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestCoreServices(unittest.TestCase):
    def setUp(self):
        pass

    def test_config_loader_functions(self):
        """Test config_loader module functions"""
        from config_loader import load_config, get_config
        self.assertTrue(callable(load_config))
        self.assertTrue(callable(get_config))

    def test_path_config_import(self):
        """Test path_config module can be imported"""
        from path_config import PROJECT_ROOT, DATA_DIR, get_data_path
        self.assertTrue(PROJECT_ROOT is not None)
        self.assertTrue(DATA_DIR is not None)

    def test_core_modules_exist(self):
        """Test core module directory structure"""
        core_path = src_path / "core"
        self.assertTrue(core_path.exists())

    def test_services_modules_exist(self):
        """Test services module directory structure"""
        services_path = src_path / "services"
        self.assertTrue(services_path.exists())


if __name__ == "__main__":
    unittest.main()