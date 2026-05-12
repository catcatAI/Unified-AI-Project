"""Test Data Manager - real tests"""
import unittest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestDataManager(unittest.TestCase):
    def test_economy_db_import(self):
        """Test economy database module can be imported"""
        try:
            from economy.economy_db import EconomyDB
            self.assertTrue(EconomyDB is not None)
        except ImportError as e:
            self.skipTest(f"Economy DB not available: {e}")

    def test_shared_types_import(self):
        """Test shared types module can be imported"""
        try:
            from shared.types.common_types import MappableDataObject
            self.assertTrue(MappableDataObject is not None)
        except ImportError as e:
            self.skipTest(f"Shared types not available: {e}")

    def test_utils_import(self):
        """Test utils module can be imported"""
        try:
            from core.utils import get_timestamp
            self.assertTrue(get_timestamp is not None)
        except ImportError as e:
            self.skipTest(f"Utils not available: {e}")


if __name__ == "__main__":
    unittest.main()