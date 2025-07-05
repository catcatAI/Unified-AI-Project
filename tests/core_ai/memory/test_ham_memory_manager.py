import unittest
import os
import json
from datetime import datetime, timedelta
import sys

# Add src directory to sys.path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

from core_ai.memory.ham_memory_manager import HAMMemoryManager
from cryptography.fernet import Fernet, InvalidToken # For testing invalid token
import hashlib # For testing checksums
from unittest.mock import patch # For mocking

# Define a consistent test output directory (relative to project root)
# Assuming tests might be run from project root or tests/
PROJECT_ROOT_FOR_TEST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEST_STORAGE_DIR = os.path.join(PROJECT_ROOT_FOR_TEST, "tests", "test_output_data", "ham_memory")


class TestHAMMemoryManager(unittest.TestCase):

    def setUp(self):
        # Ensure a clean test environment for each test
        self.test_filename = "test_ham_core_memory.json"
        # Ensure the HAMMemoryManager uses this specific dir for its file.
        # This requires HAMMemoryManager to be flexible or this path to match its internal logic.
        # For now, we assume HAMMemoryManager's default storage_dir is used, and we clean that.
        # A better way would be to pass storage_dir to HAMMemoryManager or use a dedicated test path.

        # Let's make HAMMemoryManager create its file in our TEST_STORAGE_DIR
        # We can achieve this by ensuring HAMMemoryManager's path logic resolves correctly
        # or by temporarily overriding where it looks for its project root.
        # For this test, we'll ensure HAMMemoryManager's default path inside 'data/processed_data' is cleaned.

        self.ham_manager = HAMMemoryManager(core_storage_filename=self.test_filename)
        # Clean up any existing test file before each test
        if os.path.exists(self.ham_manager.core_storage_filepath):
            os.remove(self.ham_manager.core_storage_filepath)
        # Re-initialize to start fresh after potential deletion
        self.ham_manager = HAMMemoryManager(core_storage_filename=self.test_filename)


    def tearDown(self):
        # Clean up the test file after each test
        if os.path.exists(self.ham_manager.core_storage_filepath):
            os.remove(self.ham_manager.core_storage_filepath)
        # Clean up the directory if it's empty
        try:
            if os.path.exists(TEST_STORAGE_DIR) and not os.listdir(TEST_STORAGE_DIR):
                os.rmdir(TEST_STORAGE_DIR)
        except OSError:
            pass # If other files are present (e.g. from other tests), leave it.

    def test_01_initialization_and_empty_store(self):
        print("\nRunning test_01_initialization_and_empty_store...")
        self.assertIsNotNone(self.ham_manager)
        self.assertEqual(len(self.ham_manager.core_memory_store), 0)
        self.assertEqual(self.ham_manager.next_memory_id, 1)
        # File should be created (even if empty) upon initialization if it didn't exist
        self.assertTrue(os.path.exists(self.ham_manager.core_storage_filepath))
        print("test_01_initialization_and_empty_store PASSED")

    def test_02_store_and_recall_text_experience(self):
        print("\nRunning test_02_store_and_recall_text_experience...")
        raw_text = "Miko had a productive day coding the HAM model."
        metadata = {"project": "MikoAI", "task": "HAM_implementation"}

        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata)
        self.assertIsNotNone(memory_id)
        self.assertEqual(memory_id, "mem_000001")
        self.assertEqual(len(self.ham_manager.core_memory_store), 1)

        recalled_data = self.ham_manager.recall_gist(memory_id)
        self.assertIsNotNone(recalled_data)
        self.assertIsInstance(recalled_data, dict)
        self.assertEqual(recalled_data["id"], memory_id)
        self.assertEqual(recalled_data["data_type"], "dialogue_text")
        self.assertEqual(recalled_data["metadata"], metadata)

        # Check abstraction (summary and keywords)
        # Summary is first sentence: "Miko had a productive day coding the HAM model."
        # Keywords (example, depends on stopword list and simple freq count): "miko", "productive", "day", "coding", "ham" (or similar)
        self.assertIn("Summary: Miko had a productive day coding the HAM model.", recalled_data["rehydrated_gist"])
        self.assertIn("Keywords:", recalled_data["rehydrated_gist"])
        # A more robust check for keywords:
        gist_keywords = recalled_data["rehydrated_gist"].split("Keywords: ")[1].split(", ")
        self.assertIn("miko", gist_keywords)
        self.assertIn("coding", gist_keywords)
        print("test_02_store_and_recall_text_experience PASSED")

    def test_03_store_and_recall_generic_data(self):
        print("\nRunning test_03_store_and_recall_generic_data...")
        raw_data = {"temperature": 25, "unit": "Celsius"}
        metadata = {"sensor_id": "temp001"}

        memory_id = self.ham_manager.store_experience(raw_data, "sensor_reading", metadata)
        self.assertIsNotNone(memory_id)

        recalled_data = self.ham_manager.recall_gist(memory_id)
        self.assertIsNotNone(recalled_data)
        self.assertEqual(recalled_data["data_type"], "sensor_reading")
        # For generic data, rehydrated_gist is currently the string representation
        self.assertEqual(recalled_data["rehydrated_gist"], str(raw_data))
        print("test_03_store_and_recall_generic_data PASSED")

    def test_04_persistence(self):
        print("\nRunning test_04_persistence...")

        # Generate a key for this test session to ensure both instances use the same one
        test_session_key = Fernet.generate_key()

        with patch.dict(os.environ, {"MIKO_HAM_KEY": test_session_key.decode()}):
            # Initial manager instance
            ham_manager_initial = HAMMemoryManager(core_storage_filename=self.test_filename)
            # Clean up any existing file from previous setUp if it used a different temp key
            if os.path.exists(ham_manager_initial.core_storage_filepath):
                os.remove(ham_manager_initial.core_storage_filepath)
            ham_manager_initial = HAMMemoryManager(core_storage_filename=self.test_filename) # Re-init with the env key

            raw_text = "Testing persistence of HAM."
            exp_id = ham_manager_initial.store_experience(raw_text, "log_entry")
            self.assertIsNotNone(exp_id)

            # Create a new instance, which should load from file using the same key
            ham_reloaded = HAMMemoryManager(core_storage_filename=self.test_filename)
            self.assertEqual(len(ham_reloaded.core_memory_store), 1)
            # next_memory_id should be preserved through save/load
            self.assertEqual(ham_reloaded.next_memory_id, ham_manager_initial.next_memory_id)

            recalled_data = ham_reloaded.recall_gist(exp_id)
            self.assertIsNotNone(recalled_data)
            self.assertIsInstance(recalled_data, dict) # recall_gist returns dict for non-dialogue_text too
            self.assertEqual(recalled_data.get("rehydrated_gist"), str(raw_text))

        print("test_04_persistence PASSED")

    def test_05_recall_non_existent_memory(self):
        print("\nRunning test_05_recall_non_existent_memory...")
        recalled_data = self.ham_manager.recall_gist("mem_nonexistent")
        self.assertIsNone(recalled_data) # Current implementation prints error and returns None
        print("test_05_recall_non_existent_memory PASSED")

    def test_06_query_memory_keywords(self):
        print("\nRunning test_06_query_memory_keywords...")
        self.ham_manager.store_experience("User query about weather.", "dialogue_text", {"user": "Alice", "topic": "weather"})
        self.ham_manager.store_experience("User query about news.", "dialogue_text", {"user": "Bob", "topic": "news"})
        self.ham_manager.store_experience("Another weather update.", "log_entry", {"source": "system", "topic": "weather"})

        results = self.ham_manager.query_core_memory(keywords=["weather", "alice"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["user"], "Alice")

        results_topic = self.ham_manager.query_core_memory(keywords=["topic:weather"]) # Assuming simple string search in metadata
        # This won't work as expected as it searches the whole metadata string.
        # A more structured metadata search would be needed for "topic:weather".
        # For now, we test simple keyword presence.
        results_topic_simple = self.ham_manager.query_core_memory(keywords=["weather"])
        self.assertEqual(len(results_topic_simple), 2) # Finds two items with "weather" in metadata or gist
        print("test_06_query_memory_keywords PASSED")

    def test_07_query_memory_data_type(self):
        print("\nRunning test_07_query_memory_data_type...")
        self.ham_manager.store_experience("Dialogue 1", "dialogue_text")
        self.ham_manager.store_experience("Log 1", "log_entry")
        self.ham_manager.store_experience("Dialogue 2", "dialogue_text")

        results = self.ham_manager.query_core_memory(data_type_filter="dialogue_text", limit=10)
        self.assertEqual(len(results), 2)
        for item in results:
            self.assertEqual(item["data_type"], "dialogue_text")
        print("test_07_query_memory_data_type PASSED")

    def test_08_query_memory_date_range(self):
        print("\nRunning test_08_query_memory_date_range...")
        # Note: Timestamps are generated by datetime.now().isoformat()
        # For precise date range tests, we might need to mock datetime or store with fixed timestamps.
        # This test is a basic check.
        id1 = self.ham_manager.store_experience("Event A", "event", {"time": "past"})

        # Simulate time passing for next entry
        # This is not ideal for unit tests but demonstrates concept
        # A better way: allow passing timestamp to store_experience

        # For a simple test, let's assume all are stored close in time
        # and filter for a range that includes today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        results = self.ham_manager.query_core_memory(date_range=(today_start, today_end))
        self.assertGreaterEqual(len(results), 1) # At least Event A should be found

        # Test a range that should yield no results (far future)
        future_start = datetime.now() + timedelta(days=10)
        future_end = future_start + timedelta(days=1)
        results_future = self.ham_manager.query_core_memory(date_range=(future_start, future_end))
        self.assertEqual(len(results_future), 0)
        print("test_08_query_memory_date_range PASSED (basic check)")

    def test_09_empty_text_abstraction(self):
        print("\nRunning test_09_empty_text_abstraction...")
        raw_text = " " # Empty or only stopwords
        metadata = {"test_case": "empty_text"}
        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata)
        recalled_data = self.ham_manager.recall_gist(memory_id)
        self.assertIn("Summary: .", recalled_data["rehydrated_gist"]) # Corrected: single space after colon
        self.assertIn("Keywords: ", recalled_data["rehydrated_gist"]) # Keywords list should be empty
        actual_keywords = recalled_data["rehydrated_gist"].split("Keywords: ")[1]
        self.assertEqual(actual_keywords.strip(), "")
        print("test_09_empty_text_abstraction PASSED")

    def test_10_encryption_decryption(self):
        print("\nRunning test_10_encryption_decryption...")
        # This test assumes MIKO_HAM_KEY is set for actual encryption,
        # or it tests the fallback (data not truly encrypted).

        original_data_bytes = b"secret data to encrypt"

        # Test _encrypt
        encrypted_bytes = self.ham_manager._encrypt(original_data_bytes)
        if self.ham_manager.fernet:
            self.assertNotEqual(encrypted_bytes, original_data_bytes, "Data should be encrypted if Fernet is active.")
        else:
            self.assertEqual(encrypted_bytes, original_data_bytes, "Data should not be encrypted if Fernet is inactive.")

        # Test _decrypt
        decrypted_bytes = self.ham_manager._decrypt(encrypted_bytes)
        self.assertEqual(decrypted_bytes, original_data_bytes)

        # Test _decrypt with invalid token (if Fernet is active)
        if self.ham_manager.fernet:
            invalid_token_bytes = b"gAAAAABw..." # Not a real token, just an example of invalid format
            with patch('builtins.print') as mock_print: # Suppress error print for this specific test
                decrypted_invalid = self.ham_manager._decrypt(invalid_token_bytes)
            self.assertEqual(decrypted_invalid, b'', "Decryption of invalid token should return empty bytes.")
            # Check if error was logged (printed)
            self.assertTrue(any("Invalid token" in call_args[0][0] for call_args in mock_print.call_args_list if call_args[0]))
        print("test_10_encryption_decryption PASSED")

    def test_11_checksum_verification(self):
        print("\nRunning test_11_checksum_verification...")
        raw_text = "Data for checksum test."
        metadata_in = {"source": "checksum_test"}

        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata_in)
        self.assertIsNotNone(memory_id)

        # Verify checksum was added to metadata in the in-memory store
        stored_package = self.ham_manager.core_memory_store.get(memory_id)
        self.assertIsNotNone(stored_package)
        self.assertIn("metadata", stored_package)
        self.assertIn("sha256_checksum", stored_package["metadata"])

        # Recall and check (it should log no error if checksum matches)
        with patch('builtins.print') as mock_print:
            recalled_data = self.ham_manager.recall_gist(memory_id)
            self.assertIsNotNone(recalled_data)
            self.assertNotIn("CRITICAL WARNING: Checksum mismatch", "\n".join(str(c[0][0]) for c in mock_print.call_args_list if c[0]))

        # Test checksum mismatch scenario (by manually corrupting the package before recall)
        if memory_id and self.ham_manager.fernet: # Only if data was actually encrypted
            corrupted_package_encrypted = self.ham_manager.core_memory_store[memory_id]["encrypted_package"][:-5] + b"xxxxx" # Corrupt it

            # Temporarily replace the package in store for testing recall with corruption
            original_package = self.ham_manager.core_memory_store[memory_id].copy()
            self.ham_manager.core_memory_store[memory_id]["encrypted_package"] = corrupted_package_encrypted

            with patch('builtins.print') as mock_print_corrupt:
                recalled_corrupted = self.ham_manager.recall_gist(memory_id)
                # Recall might fail decryption/decompression first due to corruption
                if isinstance(recalled_corrupted, str) and "Error:" in recalled_corrupted:
                     print(f"Recall failed as expected due to corruption: {recalled_corrupted}")
                     # Check if the error was due to decryption or decompression before checksum
                     self.assertTrue(any("decryption" in call_args[0][0].lower() or "decompression" in call_args[0][0].lower() for call_args in mock_print_corrupt.call_args_list if call_args[0]))
                else: # If it somehow passed decryption/decompression but checksum failed
                    self.assertTrue(any("CRITICAL WARNING: Checksum mismatch" in call_args[0][0] for call_args in mock_print_corrupt.call_args_list if call_args[0]))

            self.ham_manager.core_memory_store[memory_id] = original_package # Restore original package
        print("test_11_checksum_verification PASSED (mismatch test depends on encryption state)")

    def test_12_advanced_text_abstraction_placeholders(self):
        print("\nRunning test_12_advanced_text_abstraction_placeholders...")
        # Test English-like text
        eng_text = "Hello world, this is a test."
        eng_mem_id = self.ham_manager.store_experience(eng_text, "user_dialogue_text")
        recalled_eng = self.ham_manager.recall_gist(eng_mem_id)
        self.assertIn("POS Tags (Placeholder):", recalled_eng["rehydrated_gist"])
        self.assertNotIn("Radicals (Placeholder):", recalled_eng["rehydrated_gist"])

        # Test Chinese-like text
        # Need to clear memory or use different HAM instance for clean abstraction check
        self.ham_manager.core_memory_store = {} # Clear for this part
        self.ham_manager.next_memory_id = 1
        if os.path.exists(self.ham_manager.core_storage_filepath):
            os.remove(self.ham_manager.core_storage_filepath)
        self.ham_manager._load_core_memory_from_file()


        chn_text = "你好世界，这是一个测试。"
        chn_mem_id = self.ham_manager.store_experience(chn_text, "user_dialogue_text")
        recalled_chn = self.ham_manager.recall_gist(chn_mem_id)
        self.assertIn("Radicals (Placeholder):", recalled_chn["rehydrated_gist"])
        self.assertNotIn("POS Tags (Placeholder):", recalled_chn["rehydrated_gist"])
        print("test_12_advanced_text_abstraction_placeholders PASSED")


if __name__ == '__main__':
    # Ensure the test output directory exists
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)

    print(f"HAM Test: Current working directory: {os.getcwd()}")
    print(f"HAM Test: Sys.path: {sys.path}")
    print(f"HAM Test: Test storage directory: {TEST_STORAGE_DIR}")

    unittest.main(verbosity=2)
