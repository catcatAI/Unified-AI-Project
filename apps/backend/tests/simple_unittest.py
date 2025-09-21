import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSimple(unittest.TestCase):
    
    def test_import(self):
        """Test that we can import config_loader."""
        try:
            from config_loader import load_config
            print("config_loader imported successfully")
            self.assertTrue(True)
        except Exception as e:
            print(f"Import error: {e}")
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()