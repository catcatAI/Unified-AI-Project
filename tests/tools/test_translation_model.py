import unittest
import pytest
import os
import json
import sys
import shutil

from src.tools import translation_tool
from src.tools.translation_tool import (
    translate,
    _detect_language,
    _load_dictionary,
    request_model_upgrade,
)
from src.tools.tool_dispatcher import ToolDispatcher

# Define a consistent test output directory for this test suite
TEST_DATA_DIR = "tests/test_output_data/translation_model_data"
# Path for the dummy dictionary for testing
DUMMY_DICTIONARY_PATH = os.path.join(TEST_DATA_DIR, "test_translation_dictionary.json")


class TestTranslationModelComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_DATA_DIR, exist_ok=True)

        # Create a dummy dictionary for testing purposes
        cls.dummy_dict_content = {
            "zh_to_en": {"你好": "Hello", "世界": "World", "猫": "Cat"},
            "en_to_zh": {"Hello": "你好", "World": "世界", "Dog": "狗"}
        }
        with open(DUMMY_DICTIONARY_PATH, 'w', encoding='utf-8') as f:
            json.dump(cls.dummy_dict_content, f, indent=2)

        # Override the original dictionary path for testing
        cls.original_dictionary_path = translation_tool.DICTIONARY_PATH
        translation_tool.DICTIONARY_PATH = DUMMY_DICTIONARY_PATH

        # Reset the global dictionary in the module to force reload with dummy
        translation_tool._translation_dictionary = None


    @classmethod
    def tearDownClass(cls):
        # Restore original dictionary path
        translation_tool.DICTIONARY_PATH = cls.original_dictionary_path
        translation_tool._translation_dictionary = None # Clear loaded dict

        # Clean up test directory and files
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

    def setUp(self):
        # Ensure dictionary is reloaded for each test with the dummy one
        translation_tool._translation_dictionary = None
        _load_dictionary() # This will now load DUMMY_DICTIONARY_PATH

    @pytest.mark.timeout(5)
    def test_01_load_dictionary(self):
        print("\nRunning test_01_load_dictionary...")
        dictionary = _load_dictionary() # Should use the dummy dictionary
        self.assertIsNotNone(dictionary)
        self.assertIn("zh_to_en", dictionary)
        self.assertIn("你好", dictionary["zh_to_en"])
        self.assertEqual(dictionary["zh_to_en"]["你好"], "Hello")
        print("test_01_load_dictionary PASSED")

    @pytest.mark.timeout(5)
    def test_02_detect_language(self):
        print("\nRunning test_02_detect_language...")
        self.assertEqual(_detect_language("你好世界"), "zh")
        self.assertEqual(_detect_language("Hello World"), "en")
        self.assertEqual(_detect_language("你好 World"), "zh") # Contains Chinese chars
        self.assertEqual(_detect_language("123 !@#"), None) # No clear language
        self.assertEqual(_detect_language(""), None)
        print("test_02_detect_language PASSED")

    @pytest.mark.timeout(5)
    def test_03_translate_function(self):
        print("\nRunning test_03_translate_function...")
        # Test with dummy dictionary
        self.assertEqual(translate("你好", "en"), "Hello")
        self.assertEqual(translate("Hello", "zh"), "你好")
        self.assertEqual(translate("猫", "en", source_language="zh"), "Cat")
        self.assertEqual(translate("Dog", "zh", source_language="en"), "狗")

        # Case insensitivity for English source
        self.assertEqual(translate("hello", "zh"), "你好")

        # Unknown word
        self.assertIn("not available", translate("未知", "en"))
        self.assertIn("not available", translate("Unknown", "zh"))

        # Unsupported language
        self.assertIn("not supported", translate("你好", "es"))

        # Same source/target
        self.assertEqual(translate("你好", "zh"), "你好")
        print("test_03_translate_function PASSED")

    @pytest.mark.timeout(5)
    def test_04_request_model_upgrade_hook(self):
        print("\nRunning test_04_request_model_upgrade_hook...")
        # This test just ensures the function can be called without error
        try:
            request_model_upgrade("Test details for upgrade request.")
            # If we want to check print output, we'd need to redirect stdout
            print("test_04_request_model_upgrade_hook PASSED (callability check)")
        except Exception as e:
            self.fail(f"request_model_upgrade raised an exception: {e}")

    @pytest.mark.timeout(5)
    def test_05_tool_dispatcher_translation_routing(self):
        print("\nRunning test_05_tool_dispatcher_translation_routing...")
        dispatcher = ToolDispatcher()

        # Mock the DLM's intent recognition for these tests
        def mock_recognize_intent(query, **kwargs):
            if "你好" in query and "English" in query:
                return {"tool_name": "translate_text", "parameters": {"text_to_translate": "你好", "target_language": "English"}}
            if "Hello" in query and "Chinese" in query:
                return {"tool_name": "translate_text", "parameters": {"text_to_translate": "Hello", "target_language": "Chinese"}}
            if "'Dog' in Chinese" in query:
                 return {"tool_name": "translate_text", "parameters": {"text_to_translate": "Dog", "target_language": "Chinese"}}
            if "未知词" in query:
                 return {"tool_name": "translate_text", "parameters": {"text_to_translate": "未知词", "target_language": "English"}}
            if "Spanish" in query:
                 return {"tool_name": "translate_text", "parameters": {"text_to_translate": "你好", "target_language": "Spanish"}}
            return {"tool_name": "NO_TOOL", "parameters": {}}
        dispatcher.dlm.recognize_intent = mock_recognize_intent

        # Test inference scenarios
        response1 = dispatcher.dispatch("translate '你好' to English")
        self.assertEqual(response1['payload'], "Hello")
        response2 = dispatcher.dispatch("translate 'Hello' to Chinese")
        self.assertEqual(response2['payload'], "你好")
        response3 = dispatcher.dispatch("'Dog' in Chinese")
        self.assertEqual(response3['payload'], "狗")
        response4 = dispatcher.dispatch("translate '未知词' to English")
        self.assertEqual(response4['status'], 'failure_tool_error')
        self.assertIn("not available", response4['error_message'])
        response5 = dispatcher.dispatch("translate '你好' to Spanish")
        self.assertEqual(response5['status'], 'failure_tool_error')
        self.assertIn("not supported", response5['error_message'])

        # Test explicit call (bypassing DLM)
        response_explicit = dispatcher.dispatch("猫", explicit_tool_name="translate_text", target_language="en")
        self.assertEqual(response_explicit['payload'], "Cat")

        print("test_05_tool_dispatcher_translation_routing PASSED")

    @pytest.mark.timeout(5)
    def test_06_dictionary_load_failure(self):
        print("\nRunning test_06_dictionary_load_failure...")
        original_path = translation_tool.DICTIONARY_PATH
        translation_tool.DICTIONARY_PATH = "non_existent_dictionary.json"
        translation_tool._translation_dictionary = None # Force reload

        dictionary = _load_dictionary()
        self.assertIsNotNone(dictionary) # Should return empty dicts on failure
        self.assertEqual(dictionary["zh_to_en"], {})
        self.assertEqual(dictionary["en_to_zh"], {})

        # Test translate function with empty dictionary
        self.assertIn("not available", translate("你好", "en"))

        translation_tool.DICTIONARY_PATH = original_path # Restore
        translation_tool._translation_dictionary = None # Force reload of original for other tests if any
        print("test_06_dictionary_load_failure PASSED")


if __name__ == '__main__':
    # This setup is primarily if running this test file directly.
    # unittest.main() will use the setUpClass/tearDownClass for managing paths.
    print(f"Translation Model Test: Current working directory: {os.getcwd()}")
    print(f"Translation Model Test: Sys.path: {sys.path}")
    print(f"Translation Model Test: Test data output directory: {TEST_DATA_DIR}")

    unittest.main(verbosity=2)
