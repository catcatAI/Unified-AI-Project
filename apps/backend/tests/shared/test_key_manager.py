import unittest
import os
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

# Adjust the path to import from the src directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from apps.backend.src.shared.key_manager import UnifiedKeyManager

class TestUnifiedKeyManager(unittest.TestCase):

    def test_get_key_from_environment(self):
        """Test fetching a key that exists in the environment."""
        with patch.dict(os.environ, {"MY_API_KEY": "env_key_123"}):
            # We pass a non-existent config path to ensure it falls back to env vars
            km = UnifiedKeyManager(config_path="non_existent_config.yaml")
            self.assertEqual(km.get_key("MY_API_KEY"), "env_key_123")

    def test_get_key_not_in_environment(self):
        """Test fetching a key that does not exist."""
        # Ensure the key is not in the environment
        if "NON_EXISTENT_KEY" in os.environ:
            del os.environ["NON_EXISTENT_KEY"]

        km = UnifiedKeyManager(config_path="non_existent_config.yaml")
        self.assertIsNone(km.get_key("NON_EXISTENT_KEY"))

    def test_demo_mode_detection_from_env(self):
        """Test that demo mode is detected from environment variables."""
        mock_config = {
            "demo_mode": {
                "auto_detect": True,
                "detection_patterns": ["^DEMO_"],
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch.dict(os.environ, {"DEMO_API_KEY": "some_demo_key"}):
                km = UnifiedKeyManager()
                self.assertTrue(km.demo_mode)

    def test_get_key_in_demo_mode(self):
        """Test that fixed demo keys are returned in demo mode."""
        mock_config = {
            "demo_mode": {
                "auto_detect": True,
                "detection_patterns": ["^DEMO_"],
                "fixed_keys": {
                    "MIKO_HAM_KEY": "fixed_ham_key_for_demo",
                    "OPENAI_API_KEY": "fixed_openai_key_for_demo"
                }
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch.dict(os.environ, {"DEMO_FLAG": "true", "OPENAI_API_KEY": "real_key_should_be_ignored"}):
                km = UnifiedKeyManager()
                self.assertTrue(km.demo_mode)
                self.assertEqual(km.get_key("MIKO_HAM_KEY"), "fixed_ham_key_for_demo")
                self.assertEqual(km.get_key("OPENAI_API_KEY"), "fixed_openai_key_for_demo")
                # Test that it doesn't fall back to env var for a key not in fixed_keys
                self.assertIsNone(km.get_key("SOME_OTHER_KEY"))

    def test_not_in_demo_mode(self):
        """Test behavior when not in demo mode."""
        mock_config = {
            "demo_mode": {
                "auto_detect": True,
                "detection_patterns": ["^DEMO_"],
            }
        }

        # Ensure no demo-related env vars are set
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("DEMO")}

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch.dict(os.environ, clean_env, clear=True):
                with patch.dict(os.environ, {"OPENAI_API_KEY": "real_production_key"}):
                    km = UnifiedKeyManager()
                    self.assertFalse(km.demo_mode)
                    # It should return the key from the environment
                    self.assertEqual(km.get_key("OPENAI_API_KEY"), "real_production_key")

    def test_generate_ham_key_not_in_demo_mode(self):
        """Test that a new HAM key is generated when not in demo mode."""
        km = UnifiedKeyManager(config_path="non_existent_config.yaml")
        self.assertFalse(km.demo_mode)

        key1 = km.generate_ham_key()
        key2 = km.generate_ham_key()

        self.assertIsInstance(key1, str)
        self.assertNotEqual(key1, key2)
        # A basic check for base64 encoding used by Fernet keys
        self.assertTrue(len(key1) > 40)

    def test_generate_ham_key_in_demo_mode(self):
        """Test that the fixed HAM key is returned in demo mode."""
        mock_config = {
            "demo_mode": {
                "auto_detect": True,
                "detection_patterns": ["^DEMO_"],
                "fixed_keys": {
                    "MIKO_HAM_KEY": "fixed_ham_key_for_demo"
                }
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch.dict(os.environ, {"DEMO_FLAG": "true"}):
                km = UnifiedKeyManager()
                self.assertTrue(km.demo_mode)
                self.assertEqual(km.generate_ham_key(), "fixed_ham_key_for_demo")

if __name__ == '__main__':
    unittest.main()
