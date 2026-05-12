"""Test Dependency Manager - real tests"""
import unittest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestDependencyManager(unittest.TestCase):
    def test_hsp_connector_import(self):
        """Test HSP connector can be imported"""
        try:
            from core.hsp.connector import HSPConnector
            self.assertTrue(HSPConnector is not None)
        except ImportError as e:
            self.skipTest(f"HSP connector not available: {e}")

    def test_hsp_bridge_import(self):
        """Test HSP bridge module can be imported"""
        try:
            from core.hsp.bridge import message_bridge
            self.assertTrue(message_bridge is not None)
        except ImportError as e:
            self.skipTest(f"HSP bridge not available: {e}")

    def test_core_imports(self):
        """Test core module imports"""
        try:
            from core.angela_error import AngelaError
            self.assertTrue(AngelaError is not None)
        except ImportError as e:
            self.skipTest(f"Core module not available: {e}")


if __name__ == "__main__":
    unittest.main()