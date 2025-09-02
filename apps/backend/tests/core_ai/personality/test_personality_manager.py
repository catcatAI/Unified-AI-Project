import unittest
import sys
import os
import json
from pathlib import Path
import pytest

# Add the src directory to the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs") # For accessing personality profiles

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from apps.backend.src.core_ai.personality.personality_manager import PersonalityManager

class TestPersonalityManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_profiles_dir = Path(TEST_OUTPUT_DIR) / "personality_profiles" # Use a test-specific dir
        os.makedirs(cls.test_profiles_dir, exist_ok=True)

        cls.miko_base_profile_path = Path(CONFIGS_DIR) / "personality_profiles" / "miko_base.json"

        # Create a dummy profile for testing loading different profiles
        cls.dummy_profile_data = {
            "profile_name": "dummy_test_profile",
            "display_name": "Dummy Profile",
            "initial_prompt": "Dummy says hi!",
            "communication_style": {"default_tone": "robotic"},
        }
        with open(cls.test_profiles_dir / "dummy_test_profile.json", 'w') as f:
            json.dump(cls.dummy_profile_data, f)

    @classmethod
    def tearDownClass(cls):
        # Clean up the dummy profile and directory
        if cls.test_profiles_dir.exists():
            for item in cls.test_profiles_dir.iterdir():
                item.unlink() # remove file
            cls.test_profiles_dir.rmdir()


    def setUp(self):
        # Most tests will use the default miko_base.json from configs/
        # For tests specifically needing the dummy profile, we'll pass the test_profiles_dir
        self.pm_default = PersonalityManager() # Uses default path
        self.pm_test_dir = PersonalityManager(personality_profiles_dir=str(self.test_profiles_dir))


    @pytest.mark.timeout(5)
    def test_01_initialization_default_path(self):
        self.assertIsNotNone(self.pm_default)
        self.assertTrue(any(p["name"] == "miko_base" for p in self.pm_default.list_available_profiles()))
        self.assertIsNotNone(self.pm_default.current_personality)
        self.assertEqual(self.pm_default.current_personality["profile_name"], "miko_base")
        print("TestPersonalityManager.test_01_initialization_default_path PASSED")

    @pytest.mark.timeout(5)
    def test_02_initialization_custom_path(self):
        self.assertIsNotNone(self.pm_test_dir)
        available_test_profiles = self.pm_test_dir.list_available_profiles()
        self.assertTrue(any(p["name"] == "dummy_test_profile" for p in available_test_profiles))
        # It should load the default_profile_name ("miko_base") if available, but it won't be in test_profiles_dir
        # So it should try to load "dummy_test_profile" if "miko_base" (default) isn't found there,
        # or load nothing if dummy_test_profile was not default and miko_base wasn't there.
        # Let's check its behavior when default isn't in custom path.
        # The PersonalityManager defaults to "miko_base". If not found in custom path, current_personality might be None
        # or it might pick the first one it finds if default is not there.
        # Current logic: if default ('miko_base') not found, it tries to load it anyway (and fails silently or logs).
        # Then current_personality would be None.
        # Let's ensure it loads the dummy if we explicitly tell it to.

        pm_specific_dummy = PersonalityManager(
            personality_profiles_dir=str(self.test_profiles_dir),
            default_profile_name="dummy_test_profile"
        )
        self.assertIsNotNone(pm_specific_dummy.current_personality)
        self.assertEqual(pm_specific_dummy.current_personality["profile_name"], "dummy_test_profile")
        print("TestPersonalityManager.test_02_initialization_custom_path PASSED")


    @pytest.mark.timeout(5)
    def test_03_load_personality(self):
        loaded = self.pm_test_dir.load_personality("dummy_test_profile")
        self.assertTrue(loaded)
        self.assertIsNotNone(self.pm_test_dir.current_personality)
        self.assertEqual(self.pm_test_dir.current_personality["profile_name"], "dummy_test_profile")
        self.assertEqual(self.pm_test_dir.get_initial_prompt(), "Dummy says hi!")
        print("TestPersonalityManager.test_03_load_personality PASSED")

    @pytest.mark.timeout(5)
    def test_04_load_non_existent_profile(self):
        # pm_default uses the actual configs/ dir. "non_existent" shouldn't be there.
        # It will try to load "miko_base" if "non_existent" fails.
        loaded = self.pm_default.load_personality("non_existent_profile_qwert")
        self.assertTrue(loaded) # Because it falls back to default miko_base
        self.assertEqual(self.pm_default.current_personality["profile_name"], "miko_base")
        print("TestPersonalityManager.test_04_load_non_existent_profile PASSED")

    @pytest.mark.timeout(5)
    def test_05_get_trait(self):
        # Uses pm_default which has miko_base loaded
        prompt = self.pm_default.get_current_personality_trait("initial_prompt")
        self.assertEqual(prompt, "你好，我是 Miko，一個樂於助人的 AI 助理。")

        nested_trait = self.pm_default.get_current_personality_trait("communication_style.default_style")
        self.assertEqual(nested_trait, "親切、富有啟發性")

        non_existent = self.pm_default.get_current_personality_trait("non.existent.trait", "default_val")
        self.assertEqual(non_existent, "default_val")
        print("TestPersonalityManager.test_05_get_trait PASSED")

# This setup is needed because test_math_model also defines TEST_OUTPUT_DIR
# We need a unique path for this test module to avoid conflicts if tests are run together.
# However, for pytest discovery, this __main__ block might not be the best place.
# Let's ensure TEST_OUTPUT_DIR is defined before setUpClass.
TEST_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tests", "test_output_data", "personality_manager_files")

if __name__ == '__main__':
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    unittest.main(verbosity=2)
