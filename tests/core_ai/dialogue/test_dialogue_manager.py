import unittest
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core_ai.dialogue.dialogue_manager import DialogueManager
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.personality.personality_manager import PersonalityManager
from core_ai.time_system import TimeSystem # For mocking specific time system if needed
from datetime import datetime # For creating specific datetime objects for mocking
from unittest.mock import patch # For mocking datetime.now
import json # For reading memory file

# Define a consistent test output directory (relative to project root)
TEST_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tests", "test_output_data", "dialogue_manager_tests")


class TestDialogueManager(unittest.TestCase):

    def setUp(self):
        self.test_memory_filename = "test_dialogue_memory.json"
        self.test_memory_filepath = os.path.join(TEST_OUTPUT_DIR, self.test_memory_filename)

        # Ensure the directory for test memory exists
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

        # Clean up any existing test memory file before each test
        if os.path.exists(self.test_memory_filepath):
            os.remove(self.test_memory_filepath)

        # Initialize managers with test-specific configurations if needed
        # For HAMMemoryManager, ensure it writes to our test directory
        # We need to ensure its internal `storage_dir` points to `TEST_OUTPUT_DIR`
        # One way: HAMMemoryManager could take storage_dir as an __init__ arg.
        # For now, HAMMemoryManager calculates storage_dir based on its own file location.
        # Let's mock its storage_dir or pass a pre-configured instance.

        # Create a HAMMemoryManager that uses the test-specific file path
        # This requires HAMMemoryManager's constructor or file path logic to be adaptable.
        # Assuming HAMMemoryManager's core_storage_filepath can be influenced by core_storage_filename
        # and its default self.storage_dir is `data/processed_data` relative to project root.
        # For isolated testing, it's better to pass a fully configured memory manager.

        # Let's make HAMMemoryManager use a specific path for testing
        # We'll create a specific instance of HAMMemoryManager for the test
        # and pass it to DialogueManager.
        # This requires HAMMemoryManager to be flexible enough or DialogueManager to accept it.
        # The HAMMemoryManager's __init__ computes storage_dir as:
        # project_root / "data" / "processed_data"
        # And core_storage_filepath is os.path.join(self.storage_dir, core_storage_filename)

        # To make HAMMemoryManager write to TEST_OUTPUT_DIR, we can patch its self.storage_dir
        # or modify HAMMemoryManager to accept a full path or separate base_dir.
        # For simplicity, let's ensure the test HAMMemoryManager instance uses our desired path.
        # This is a bit of a hack for now if HAMMemoryManager is not designed for path override.

        # A cleaner way: DialogueManager's memory_manager param.
        test_pm = PersonalityManager() # Uses default miko_base

        # Create a HAMMemoryManager instance that will save its file inside TEST_OUTPUT_DIR
        # We achieve this by giving a filename that implies the path
        # No, HAMMemoryManager prepends its own self.storage_dir.
        # The easiest is to have DialogueManager pass the filename.
        # DialogueManager now initializes HAMMemoryManager(core_storage_filename="dialogue_context_memory.json")
        # We need to make DialogueManager use a *test specific* HAMMemoryManager.

        self.mock_ham_storage_dir = TEST_OUTPUT_DIR

        # Patch HAMMemoryManager's storage_dir for tests
        # This is not ideal, dependency injection is better.
        # For now, let's assume DialogueManager can be given a memory_manager instance.
        self.test_ham_manager = HAMMemoryManager(core_storage_filename=self.test_memory_filename)
        # Override its calculated storage_dir to our test directory.
        self.test_ham_manager.storage_dir = self.mock_ham_storage_dir
        self.test_ham_manager.core_storage_filepath = os.path.join(self.mock_ham_storage_dir, self.test_memory_filename)
        # Ensure it loads/creates the file in the new path
        if os.path.exists(self.test_ham_manager.core_storage_filepath): # clean if exists from other runs
            os.remove(self.test_ham_manager.core_storage_filepath)
        self.test_ham_manager._load_core_memory_from_file() # This will now use the test path

        # EmotionSystem is now also part of DialogueManager init
        # For predictable emotion testing, we can pass a specific EmotionSystem instance or rely on its default.
        # DialogueManager will pass its own personality_manager.current_personality to EmotionSystem if not provided.
        self.dialogue_mgr = DialogueManager(
            personality_manager=test_pm,
            memory_manager=self.test_ham_manager
            # emotion_system will be created by default inside DialogueManager
        )


    def tearDown(self):
        # Clean up the test memory file after each test
        if os.path.exists(self.test_memory_filepath):
            os.remove(self.test_memory_filepath)
        # Clean up the directory if it's empty and was created by this test
        if os.path.exists(TEST_OUTPUT_DIR) and not os.listdir(TEST_OUTPUT_DIR):
            try:
                os.rmdir(TEST_OUTPUT_DIR)
            except OSError: # Might fail if other tests created files there in parallel
                pass


    def test_01_initialization(self):
        self.assertIsNotNone(self.dialogue_mgr)
        self.assertIsNotNone(self.dialogue_mgr.memory_manager)
        # Check if the memory manager is using the test file path
        self.assertEqual(self.dialogue_mgr.memory_manager.core_storage_filepath, self.test_memory_filepath)
        print("TestDialogueManager.test_01_initialization PASSED")

    def test_02_get_simple_response(self):
        user_input = "Hello there"
        ai_name = self.dialogue_mgr.personality_manager.get_current_personality_trait("display_name", "AI")

        # The LLMInterface placeholder returns: f"Placeholder response from {model_name} for: {prompt}"
        # Assuming default model name "generic-llm-placeholder" from LLMInterface placeholder
        llm_placeholder_model_name = "generic-llm-placeholder" # As per LLMInterface placeholder
        expected_llm_part = f"Placeholder response from {llm_placeholder_model_name} for: {user_input}"
        base_expected_response = f"{ai_name}: {expected_llm_part}"

        # Test with neutral input first (should have no suffix or default personality suffix)
        # The default personality "miko_base" has "neutral" as default_tone.
        # EmotionSystem's default map for "neutral" has "" text_ending.
        actual_response_neutral = self.dialogue_mgr.get_simple_response(user_input)
        self.assertEqual(actual_response_neutral, base_expected_response) # No suffix for neutral

        # Test with input that should trigger "empathetic"
        sad_input = "I am very sad."
        expected_llm_part_sad = f"Placeholder response from {llm_placeholder_model_name} for: {sad_input}"
        base_expected_response_sad = f"{ai_name}: {expected_llm_part_sad}"
        expected_response_empathetic = f"{base_expected_response_sad}{self.dialogue_mgr.emotion_system.emotion_expressions['empathetic']['text_ending']}"
        actual_response_empathetic = self.dialogue_mgr.get_simple_response(sad_input)
        self.assertEqual(actual_response_empathetic, expected_response_empathetic)
        self.assertEqual(self.dialogue_mgr.emotion_system.current_emotion, "empathetic")


        # Test with input that should trigger "playful"
        happy_input = "I am so happy today!"
        expected_llm_part_happy = f"Placeholder response from {llm_placeholder_model_name} for: {happy_input}"
        base_expected_response_happy = f"{ai_name}: {expected_llm_part_happy}"
        expected_response_playful = f"{base_expected_response_happy}{self.dialogue_mgr.emotion_system.emotion_expressions['playful']['text_ending']}"
        actual_response_playful = self.dialogue_mgr.get_simple_response(happy_input)
        self.assertEqual(actual_response_playful, expected_response_playful)
        self.assertEqual(self.dialogue_mgr.emotion_system.current_emotion, "playful")

        # Verify memory storage (checking for the last interaction - playful one)
        # The memory will have 2 (neutral) + 2 (empathetic) + 2 (playful) = 6 entries by now
        self.assertTrue(os.path.exists(self.test_memory_filepath))
        with open(self.test_memory_filepath, 'r') as f:
            memory_data = json.load(f)

        self.assertIn("store", memory_data)
        stored_items = memory_data["store"]
        self.assertEqual(len(stored_items), 6) # 2 for neutral, 2 for empathetic, 2 for playful

        # Check content for the last (playful) interaction's AI response
        # This is a bit more involved as we need to find the correct entry.
        # We'll assume the last AI response stored matches expected_response_playful.

        found_playful_ai_response = False
        for mem_id, item_pkg_b64 in stored_items.items():
            if item_pkg_b64["data_type"] == "ai_dialogue_text":
                decrypted_bytes = self.test_ham_manager._decrypt(item_pkg_b64["encrypted_package_b64"].encode('latin-1'))
                decompressed_bytes = self.test_ham_manager._decompress(decrypted_bytes)
                gist_json_str = decompressed_bytes.decode('utf-8')
                gist_data = json.loads(gist_json_str)
                # Check original_length of the AI's response part
                if gist_data.get("original_length") == len(expected_response_playful):
                    found_playful_ai_response = True
                    # Optionally, also check associated user input if user_input_ref was reliably set and testable
                    # For now, just confirming the AI response text length seems sufficient for this test.
                    break

        self.assertTrue(found_playful_ai_response, "Playful AI response memory entry not found or content mismatch.")
        print("TestDialogueManager.test_02_get_simple_response PASSED (including memory check for emotional responses)")

    def test_03_start_session(self):
        # PersonalityManager by default loads "miko_base"
        base_prompt = self.dialogue_mgr.personality_manager.get_initial_prompt()

        test_cases = [
            (datetime(2023, 1, 1, 9, 0, 0), f"Good morning! {base_prompt}"),  # Morning
            (datetime(2023, 1, 1, 14, 0, 0), f"Good afternoon! {base_prompt}"),# Afternoon
            (datetime(2023, 1, 1, 20, 0, 0), f"Good evening! {base_prompt}"), # Evening
            (datetime(2023, 1, 1, 23, 0, 0), f"Hello, {base_prompt}")      # Night
        ]

        for mock_now, expected_greeting in test_cases:
            with patch('core_ai.time_system.datetime') as mock_datetime_module:
                mock_datetime_module.datetime.now.return_value = mock_now
                # Re-initialize DialogueManager or its TimeSystem to pick up mocked time
                # Easiest: Pass a new TimeSystem instance that will use the mocked now()
                test_pm = PersonalityManager() # Fresh PM for consistent base_prompt
                # Create a new TimeSystem that will pick up the patched datetime.now
                # when its get_current_time() is called.
                # DialogueManager will create its own TimeSystem if not provided.
                # So we need to ensure the TimeSystem *inside* DialogueManager uses the mock.
                # This is done by patching where TimeSystem looks for datetime.

                # Create a fresh DialogueManager for each time segment to ensure TimeSystem is new
                # or that its get_time_of_day_segment is influenced by the mock.
                dialogue_mgr_for_test = DialogueManager(
                    personality_manager=test_pm,
                    memory_manager=self.test_ham_manager
                    # It will create its own TimeSystem, which will use the patched datetime
                )
                actual_greeting = dialogue_mgr_for_test.start_session("test_user_id")
                self.assertEqual(actual_greeting, expected_greeting, f"Failed for time {mock_now.hour}h")

        print("TestDialogueManager.test_03_start_session PASSED (Time-Aware)")

    def test_04_crisis_response(self):
        user_input_crisis = "This is an emergency, I need help!"
        ai_name = self.dialogue_mgr.personality_manager.get_current_personality_trait("display_name", "AI")

        # Default crisis response from DialogueManager if not in config
        expected_crisis_response = f"{ai_name}: I sense this is a sensitive situation. If you need help, please reach out to appropriate support channels."

        # Check specific crisis response if DialogueManager config provides one
        if self.dialogue_mgr.config.get("crisis_response_text"):
            expected_crisis_response = self.dialogue_mgr.config.get("crisis_response_text")
            # The DM prepends ai_name if the config text doesn't already include it.
            # For this test, we assume the placeholder DM config won't have this, so default is used.
            # If it did, we'd need to be more precise:
            # custom_crisis_text = self.dialogue_mgr.config.get("crisis_response_text")
            # if not custom_crisis_text.startswith(ai_name): # crude check
            #    expected_crisis_response = f"{ai_name}: {custom_crisis_text}"
            # else:
            #    expected_crisis_response = custom_crisis_text


        actual_response = self.dialogue_mgr.get_simple_response(user_input_crisis)
        self.assertEqual(actual_response, expected_crisis_response)
        self.assertGreater(self.dialogue_mgr.crisis_system.get_current_crisis_level(), 0)

        # Verify memory storage for crisis interaction
        self.assertTrue(os.path.exists(self.test_memory_filepath))
        with open(self.test_memory_filepath, 'r') as f:
            memory_data = json.load(f)

        stored_items = memory_data.get("store", {})
        # This test runs after others, so count previous items + 2 for this crisis interaction
        # setUp cleans the file, so this test method's interactions are the only ones.
        # If other tests in this class run before and add to the same file, this count needs adjustment
        # For now, assuming setUp makes this test's memory writes isolated for this check.
        # Let's reset memory for this specific test for cleaner assertion.

        # Re-setup for isolated memory for this test case
        if os.path.exists(self.test_memory_filepath):
            os.remove(self.test_memory_filepath)
        self.test_ham_manager._load_core_memory_from_file() # Re-init to empty and save empty file
        self.dialogue_mgr.memory_manager.core_memory_store = {} # Also clear in-memory part
        self.dialogue_mgr.memory_manager.next_memory_id = 1


        actual_response_after_reset = self.dialogue_mgr.get_simple_response(user_input_crisis)
        self.assertEqual(actual_response_after_reset, expected_crisis_response)

        with open(self.test_memory_filepath, 'r') as f:
            memory_data_crisis = json.load(f)
        stored_crisis_items = memory_data_crisis.get("store", {})
        self.assertEqual(len(stored_crisis_items), 2) # User input + AI crisis response

        user_entry_found = False
        ai_crisis_response_entry_found = False
        for mem_id, item_pkg_b64 in stored_crisis_items.items():
            decrypted_bytes = self.test_ham_manager._decrypt(item_pkg_b64["encrypted_package_b64"].encode('latin-1'))
            decompressed_bytes = self.test_ham_manager._decompress(decrypted_bytes)
            gist_json_str = decompressed_bytes.decode('utf-8')
            gist_data = json.loads(gist_json_str)

            if item_pkg_b64["data_type"] == "user_dialogue_text" and gist_data.get("original_length") == len(user_input_crisis):
                user_entry_found = True
            elif item_pkg_b64["data_type"] == "ai_dialogue_text" and gist_data.get("original_length") == len(expected_crisis_response):
                ai_crisis_response_entry_found = True

        self.assertTrue(user_entry_found, "Crisis user input memory entry not found.")
        self.assertTrue(ai_crisis_response_entry_found, "AI crisis response memory entry not found.")

        # Resolve crisis for cleanup
        self.dialogue_mgr.crisis_system.resolve_crisis("Test cleanup")
        print("TestDialogueManager.test_04_crisis_response PASSED")


if __name__ == '__main__':
    unittest.main(verbosity=2)
