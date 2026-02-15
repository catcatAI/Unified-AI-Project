import pytest
import asyncio
import os
import json
import shutil
from unittest.mock import MagicMock, AsyncMock, patch

from tools import translation_tool
from tools.translation_tool import (
    translate,
    _detect_language,
    _load_dictionary,
    request_model_upgrade)
from tools.tool_dispatcher import ToolDispatcher

# Define a consistent test output directory for this test suite
TEST_DATA_DIR = "tests/test_output_data/translation_model_data"
DUMMY_DICTIONARY_PATH = os.path.join(TEST_DATA_DIR, "test_translation_dictionary.json")

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_class():
    """Set up and tear down test environment for the module."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)

    dummy_dict_content = {
        "zh_to_en": {"你好": "Hello", "世界": "World", "猫": "Cat"},
        "en_to_zh": {"Hello": "你好", "World": "世界", "Dog": "狗"}
    }
    with open(DUMMY_DICTIONARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(dummy_dict_content, f, indent=2)

    # Store original path and override for testing
    original_dictionary_path = translation_tool.DICTIONARY_PATH
    translation_tool.DICTIONARY_PATH = DUMMY_DICTIONARY_PATH
    translation_tool._translation_dictionary = None # Force reload with dummy

    yield # Run tests

    # Teardown
    translation_tool.DICTIONARY_PATH = original_dictionary_path # Restore
    translation_tool._translation_dictionary = None # Clear loaded dict
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)

@pytest.fixture(autouse=True)
def setup_each_test():
    """Ensure dictionary is reloaded for each test with the dummy one."""
    translation_tool._translation_dictionary = None
    _load_dictionary() # This will now load DUMMY_DICTIONARY_PATH

@pytest.mark.timeout(5)
def test_01_load_dictionary():
    print("\nRunning test_01_load_dictionary...")
    dictionary = _load_dictionary() # Should use the dummy dictionary
    assert dictionary is not None
    assert "zh_to_en" in dictionary
    assert "你好" in dictionary["zh_to_en"]
    assert dictionary["zh_to_en"]["你好"] == "Hello"
    print("test_01_load_dictionary PASSED")

@pytest.mark.timeout(5)
def test_02_detect_language():
    print("\nRunning test_02_detect_language...")
    assert _detect_language("你好世界") == "zh"
    assert _detect_language("Hello World") == "en"
    assert _detect_language("你好 World") == "zh" # Contains Chinese chars
    assert _detect_language("123 !@#") is None # No clear language
    assert _detect_language("") is None
    print("test_02_detect_language PASSED")

@pytest.mark.timeout(5)
def test_03_translate_function():
    print("\nRunning test_03_translate_function...")
    # Test with dummy dictionary
    assert translate("你好", "en") == "Hello"
    assert translate("Hello", "zh") == "你好"
    assert translate("猫", "en", source_language="zh") == "Cat"
    assert translate("Dog", "zh", source_language="en") == "狗"

    # Case insensitivity for English source
    assert translate("hello", "zh") == "你好"

    # Unknown word
    assert "not available" in translate("未知", "en")
    assert "not available" in translate("Unknown", "zh")

    # Unsupported language
    assert "not supported" in translate("你好", "es")

    # Same source/target
    assert translate("你好", "zh") == "你好"
    print("test_03_translate_function PASSED")

@pytest.mark.timeout(5)
def test_04_request_model_upgrade_hook():
    print("\nRunning test_04_request_model_upgrade_hook...")
    # This test just ensures the function can be called without error
    try:
        request_model_upgrade("Test details for upgrade request.")
        # If we want to check print output, we'd need to redirect stdout
        print("test_04_request_model_upgrade_hook PASSED (callability check)")
    except Exception as e:
        pytest.fail(f"request_model_upgrade raised an exception: {e}")

@pytest.mark.asyncio
@pytest.mark.timeout(5)
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_05_tool_dispatcher_translation_routing():
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
    dispatcher.dlm = MagicMock()
    dispatcher.dlm.recognize_intent = mock_recognize_intent

    # Test inference scenarios
    response1 = await dispatcher.dispatch("translate '你好' to English")
    assert response1.payload == "Hello"
    response2 = await dispatcher.dispatch("translate 'Hello' to Chinese")
    assert response2.payload == "你好"
    response3 = await dispatcher.dispatch("'Dog' in Chinese")
    assert response3.payload == "狗"
    response4 = await dispatcher.dispatch("translate '未知词' to English")
    assert response4.status == 'failure_tool_error'
    assert "not available" in response4.error_message
    response5 = await dispatcher.dispatch("translate '你好' to Spanish")
    assert response5.status == 'failure_tool_error'
    assert "not supported" in response5.error_message

    # Test explicit call (bypassing DLM)
    response_explicit = await dispatcher.dispatch("猫", explicit_tool_name="translate_text", target_language="en")
    assert response_explicit.payload == "Cat"

    print("test_05_tool_dispatcher_translation_routing PASSED")

@pytest.mark.timeout(5)
def test_06_dictionary_load_failure():
    print("\nRunning test_06_dictionary_load_failure...")
    original_path = translation_tool.DICTIONARY_PATH
    translation_tool.DICTIONARY_PATH = "non_existent_dictionary.json"
    translation_tool._translation_dictionary = None # Force reload

    dictionary = _load_dictionary()
    assert dictionary is not None # Should return empty dicts on failure
    assert dictionary["zh_to_en"] == {}
    assert dictionary["en_to_zh"] == {}

    # Test translate function with empty dictionary
    assert "not available" in translate("你好", "en")

    translation_tool.DICTIONARY_PATH = original_path # Restore
    translation_tool._translation_dictionary = None # Force reload of original for other tests if any
    print("test_06_dictionary_load_failure PASSED")