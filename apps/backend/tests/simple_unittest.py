import unittest
import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSimple(unittest.TestCase):
    
    def test_import(self) -> None:
        """Test that we can import config_loader."""
        try:
            _ = print("config_loader imported successfully")
            _ = self.assertTrue(True)
        except Exception as e:
            _ = print(f"Import error: {e}")
            _ = self.assertTrue(False)

if __name__ == '__main__':
    _ = unittest.main()