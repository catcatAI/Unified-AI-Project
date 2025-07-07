import unittest
import os
import json
from datetime import datetime, timedelta, timezone # Added timezone
from typing import Optional, Dict, Any, List # Keep List for general list operations

import sys

# Add src directory to sys.path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

from core_ai.memory.ham_memory_manager import HAMMemoryManager
from shared.types.common_types import (
    DialogueMemoryEntryMetadata, HAMRecallResult,
    SimulatedDiskConfig, SimulatedHardwareProfile, SimulatedCPUConfig, SimulatedRAMConfig
)
from services.resource_awareness_service import ResourceAwarenessService # New import
from cryptography.fernet import Fernet, InvalidToken # For testing invalid token
import hashlib # For testing checksums
from unittest.mock import patch, MagicMock # For mocking
import time # For testing lag

# Define a consistent test output directory (relative to project root)
PROJECT_ROOT_FOR_TEST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEST_STORAGE_DIR = os.path.join(PROJECT_ROOT_FOR_TEST, "tests", "test_output_data", "ham_memory")


class TestHAMMemoryManager(unittest.TestCase):

    def setUp(self):
        self.test_filename = "test_ham_core_memory.json"
        # Ensure the TEST_STORAGE_DIR exists for HAM to place its file.
        os.makedirs(TEST_STORAGE_DIR, exist_ok=True)

        # Standard HAM manager without resource awareness for most tests
        self.ham_manager_no_res = HAMMemoryManager(core_storage_filename=self.test_filename)
        if os.path.exists(self.ham_manager_no_res.core_storage_filepath):
            os.remove(self.ham_manager_no_res.core_storage_filepath)
        # Re-initialize to ensure it creates a new file if it was removed
        self.ham_manager_no_res = HAMMemoryManager(core_storage_filename=self.test_filename)

        # For resource awareness tests, we'll set up a specific HAM manager with a mock service
        self.mock_resource_service = MagicMock(spec=ResourceAwarenessService)
        self.ham_manager_with_res = HAMMemoryManager(
            core_storage_filename="test_ham_res_aware_memory.json",
            resource_awareness_service=self.mock_resource_service
        )
        if os.path.exists(self.ham_manager_with_res.core_storage_filepath):
            os.remove(self.ham_manager_with_res.core_storage_filepath)
        # Re-initialize this one too
        self.ham_manager_with_res = HAMMemoryManager(
            core_storage_filename="test_ham_res_aware_memory.json",
            resource_awareness_service=self.mock_resource_service
        )

        # Use self.ham_manager for existing tests to avoid breaking them immediately.
        # Tests for resource awareness will use self.ham_manager_with_res.
        self.ham_manager = self.ham_manager_no_res


    def tearDown(self):
        if os.path.exists(self.ham_manager.core_storage_filepath):
            os.remove(self.ham_manager.core_storage_filepath)
        try:
            if os.path.exists(TEST_STORAGE_DIR) and not os.listdir(TEST_STORAGE_DIR):
                os.rmdir(TEST_STORAGE_DIR)
        except OSError:
            pass

    def test_01_initialization_and_empty_store(self):
        print("\nRunning test_01_initialization_and_empty_store...")
        self.assertIsNotNone(self.ham_manager)
        self.assertEqual(len(self.ham_manager.core_memory_store), 0)
        self.assertEqual(self.ham_manager.next_memory_id, 1)
        self.assertTrue(os.path.exists(self.ham_manager.core_storage_filepath))
        print("test_01_initialization_and_empty_store PASSED")

    def test_02_store_and_recall_text_experience(self):
        print("\nRunning test_02_store_and_recall_text_experience...")
        raw_text = "Miko had a productive day coding the HAM model."
        # Using DialogueMemoryEntryMetadata for metadata
        metadata: DialogueMemoryEntryMetadata = { # type: ignore
            "speaker": "system_log",
            "timestamp": datetime.now(timezone.utc).isoformat(), # Ensure timezone aware
            "project": "MikoAI", "task": "HAM_implementation" # Custom fields still allowed in Dict[str,Any] part of metadata
        }

        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata)
        self.assertIsNotNone(memory_id)
        self.assertEqual(memory_id, "mem_000001")
        self.assertEqual(len(self.ham_manager.core_memory_store), 1)

        recalled_data: Optional[HAMRecallResult] = self.ham_manager.recall_gist(memory_id) # type: ignore
        self.assertIsNotNone(recalled_data)
        self.assertIsInstance(recalled_data, dict) # HAMRecallResult is a TypedDict
        recalled_data = recalled_data # type: ignore # To satisfy mypy after assertIsNotNone

        self.assertEqual(recalled_data['id'], memory_id)
        self.assertEqual(recalled_data['data_type'], "dialogue_text")

        # Metadata comparison: current_metadata in store_experience adds 'sha256_checksum'
        # So, check if original metadata items are present.
        self.assertEqual(recalled_data['metadata']['speaker'], metadata['speaker'])
        self.assertEqual(recalled_data['metadata']['project'], metadata['project']) # type: ignore
        self.assertIn('sha256_checksum', recalled_data['metadata'])


        self.assertIn("Summary: Miko had a productive day coding the HAM model.", recalled_data['rehydrated_gist'])
        self.assertIn("Keywords:", recalled_data['rehydrated_gist'])
        gist_keywords_section = recalled_data['rehydrated_gist'].split("Keywords: ", 1)
        if len(gist_keywords_section) > 1:
            gist_keywords = [kw.strip() for kw in gist_keywords_section[1].split("\n")[0].split(",") if kw.strip()]
            self.assertIn("miko", gist_keywords)
            self.assertIn("coding", gist_keywords)
        else:
            self.fail("Keywords section not found in rehydrated_gist")
        print("test_02_store_and_recall_text_experience PASSED")

    def test_03_store_and_recall_generic_data(self):
        print("\nRunning test_03_store_and_recall_generic_data...")
        raw_data = {"temperature": 25, "unit": "Celsius"}
        metadata: Dict[str, Any] = {"sensor_id": "temp001"} # Keep as Dict for this generic test

        memory_id = self.ham_manager.store_experience(raw_data, "sensor_reading", metadata) # type: ignore
        self.assertIsNotNone(memory_id)

        recalled_data: Optional[HAMRecallResult] = self.ham_manager.recall_gist(memory_id) # type: ignore
        self.assertIsNotNone(recalled_data)
        recalled_data = recalled_data # type: ignore # MyPy satisfaction

        self.assertEqual(recalled_data['data_type'], "sensor_reading")
        self.assertEqual(recalled_data['rehydrated_gist'], str(raw_data))
        self.assertEqual(recalled_data['metadata']['sensor_id'], "temp001")
        print("test_03_store_and_recall_generic_data PASSED")

    def test_04_persistence(self):
        print("\nRunning test_04_persistence...")
        test_session_key = Fernet.generate_key()

        with patch.dict(os.environ, {"MIKO_HAM_KEY": test_session_key.decode()}):
            ham_manager_initial = HAMMemoryManager(core_storage_filename=self.test_filename)
            if os.path.exists(ham_manager_initial.core_storage_filepath):
                os.remove(ham_manager_initial.core_storage_filepath)
            ham_manager_initial = HAMMemoryManager(core_storage_filename=self.test_filename)

            raw_text = "Testing persistence of HAM."
            exp_id = ham_manager_initial.store_experience(raw_text, "log_entry")
            self.assertIsNotNone(exp_id)

            ham_reloaded = HAMMemoryManager(core_storage_filename=self.test_filename)
            self.assertEqual(len(ham_reloaded.core_memory_store), 1)
            self.assertEqual(ham_reloaded.next_memory_id, ham_manager_initial.next_memory_id)

            recalled_data: Optional[HAMRecallResult] = ham_reloaded.recall_gist(exp_id) # type: ignore
            self.assertIsNotNone(recalled_data)
            recalled_data = recalled_data # type: ignore
            self.assertEqual(recalled_data.get("rehydrated_gist"), str(raw_text))
        print("test_04_persistence PASSED")

    def test_05_recall_non_existent_memory(self):
        print("\nRunning test_05_recall_non_existent_memory...")
        recalled_data = self.ham_manager.recall_gist("mem_nonexistent")
        self.assertIsNone(recalled_data)
        print("test_05_recall_non_existent_memory PASSED")

    def test_06_query_memory_keywords(self):
        print("\nRunning test_06_query_memory_keywords...")
        self.ham_manager.store_experience("User query about weather.", "dialogue_text", {"speaker":"user", "timestamp":"ts1", "user": "Alice", "topic": "weather"}) # type: ignore
        self.ham_manager.store_experience("User query about news.", "dialogue_text", {"speaker":"user", "timestamp":"ts2", "user": "Bob", "topic": "news"}) # type: ignore
        self.ham_manager.store_experience("Another weather update.", "log_entry", {"speaker":"system", "timestamp":"ts3", "source": "system", "topic": "weather"}) # type: ignore

        results: List[HAMRecallResult] = self.ham_manager.query_core_memory(keywords=["weather", "alice"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['metadata']['user'], "Alice")

        results_topic_simple: List[HAMRecallResult] = self.ham_manager.query_core_memory(keywords=["weather"])
        self.assertEqual(len(results_topic_simple), 2)
        print("test_06_query_memory_keywords PASSED")

    def test_07_query_memory_data_type(self):
        print("\nRunning test_07_query_memory_data_type...")
        self.ham_manager.store_experience("Dialogue 1", "dialogue_text")
        self.ham_manager.store_experience("Log 1", "log_entry")
        self.ham_manager.store_experience("Dialogue 2", "dialogue_text")

        results: List[HAMRecallResult] = self.ham_manager.query_core_memory(data_type_filter="dialogue_text", limit=10)
        self.assertEqual(len(results), 2)
        for item in results:
            self.assertEqual(item["data_type"], "dialogue_text")
        print("test_07_query_memory_data_type PASSED")

    def test_08_query_memory_date_range(self):
        print("\nRunning test_08_query_memory_date_range...")
        id1 = self.ham_manager.store_experience("Event A", "event", {"speaker":"system", "timestamp":datetime.now(timezone.utc).isoformat()}) # type: ignore

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        results: List[HAMRecallResult] = self.ham_manager.query_core_memory(date_range=(today_start, today_end))
        self.assertGreaterEqual(len(results), 1)

        future_start = datetime.now(timezone.utc) + timedelta(days=10)
        future_end = future_start + timedelta(days=1)
        results_future: List[HAMRecallResult] = self.ham_manager.query_core_memory(date_range=(future_start, future_end))
        self.assertEqual(len(results_future), 0)
        print("test_08_query_memory_date_range PASSED (basic check)")

    def test_09_empty_text_abstraction(self):
        print("\nRunning test_09_empty_text_abstraction...")
        raw_text = " "
        metadata: DialogueMemoryEntryMetadata = {"speaker":"system", "timestamp":datetime.now(timezone.utc).isoformat(), "test_case": "empty_text"} # type: ignore
        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata)
        recalled_data: Optional[HAMRecallResult] = self.ham_manager.recall_gist(memory_id) # type: ignore
        self.assertIsNotNone(recalled_data)
        recalled_data = recalled_data # type: ignore
        self.assertIn("Summary: .", recalled_data["rehydrated_gist"])
        self.assertIn("Keywords: ", recalled_data["rehydrated_gist"])
        actual_keywords_section = recalled_data["rehydrated_gist"].split("Keywords: ", 1)
        if len(actual_keywords_section) > 1:
            actual_keywords = actual_keywords_section[1].split("\n")[0] # Take only the first line for keywords
            self.assertEqual(actual_keywords.strip(), "")
        else:
            self.fail("Keywords section not found or malformed in rehydrated_gist for empty text.")
        print("test_09_empty_text_abstraction PASSED")

    def test_10_encryption_decryption(self):
        print("\nRunning test_10_encryption_decryption...")
        original_data_bytes = b"secret data to encrypt"
        encrypted_bytes = self.ham_manager._encrypt(original_data_bytes)
        if self.ham_manager.fernet:
            self.assertNotEqual(encrypted_bytes, original_data_bytes)
        else:
            self.assertEqual(encrypted_bytes, original_data_bytes)
        decrypted_bytes = self.ham_manager._decrypt(encrypted_bytes)
        self.assertEqual(decrypted_bytes, original_data_bytes)
        if self.ham_manager.fernet:
            invalid_token_bytes = b"gAAAAABw..."
            with patch('builtins.print') as mock_print:
                decrypted_invalid = self.ham_manager._decrypt(invalid_token_bytes)
            self.assertEqual(decrypted_invalid, b'')
            self.assertTrue(any("Invalid token" in call_args[0][0] for call_args in mock_print.call_args_list if call_args[0]))
        print("test_10_encryption_decryption PASSED")

    def test_11_checksum_verification(self):
        print("\nRunning test_11_checksum_verification...")
        raw_text = "Data for checksum test."
        metadata_in: DialogueMemoryEntryMetadata = {"speaker":"system","timestamp":datetime.now(timezone.utc).isoformat(),"source": "checksum_test"} # type: ignore
        memory_id = self.ham_manager.store_experience(raw_text, "dialogue_text", metadata_in)
        self.assertIsNotNone(memory_id)
        stored_package = self.ham_manager.core_memory_store.get(memory_id) # type: ignore
        self.assertIsNotNone(stored_package)
        self.assertIn("metadata", stored_package)
        self.assertIn("sha256_checksum", stored_package["metadata"]) # type: ignore
        with patch('builtins.print') as mock_print:
            recalled_data = self.ham_manager.recall_gist(memory_id)
            self.assertIsNotNone(recalled_data)
            self.assertNotIn("CRITICAL WARNING: Checksum mismatch", "\n".join(str(c[0][0]) for c in mock_print.call_args_list if c[0]))
        if memory_id and self.ham_manager.fernet:
            corrupted_package_encrypted = self.ham_manager.core_memory_store[memory_id]["encrypted_package"][:-5] + b"xxxxx"
            original_package = self.ham_manager.core_memory_store[memory_id].copy()
            self.ham_manager.core_memory_store[memory_id]["encrypted_package"] = corrupted_package_encrypted
            with patch('builtins.print') as mock_print_corrupt:
                recalled_corrupted = self.ham_manager.recall_gist(memory_id)
                if recalled_corrupted is None: # Expected if decryption/decompression fails
                     self.assertTrue(any("decryption" in call_args[0][0].lower() or "decompression" in call_args[0][0].lower() for call_args in mock_print_corrupt.call_args_list if call_args[0]))
                else: # Should not happen if corruption is severe enough
                    self.assertTrue(any("CRITICAL WARNING: Checksum mismatch" in call_args[0][0] for call_args in mock_print_corrupt.call_args_list if call_args[0]))
            self.ham_manager.core_memory_store[memory_id] = original_package
        print("test_11_checksum_verification PASSED (mismatch test depends on encryption state)")

    def test_12_advanced_text_abstraction_placeholders(self):
        print("\nRunning test_12_advanced_text_abstraction_placeholders...")
        eng_text = "Hello world, this is a test."
        eng_mem_id = self.ham_manager.store_experience(eng_text, "user_dialogue_text")
        recalled_eng: Optional[HAMRecallResult] = self.ham_manager.recall_gist(eng_mem_id) # type: ignore
        self.assertIsNotNone(recalled_eng)
        recalled_eng = recalled_eng # type: ignore
        self.assertIn("POS Tags (Placeholder):", recalled_eng["rehydrated_gist"])
        self.assertNotIn("Radicals (Placeholder):", recalled_eng["rehydrated_gist"])

        self.ham_manager.core_memory_store = {}
        self.ham_manager.next_memory_id = 1
        if os.path.exists(self.ham_manager.core_storage_filepath):
            os.remove(self.ham_manager.core_storage_filepath)
        self.ham_manager._load_core_memory_from_file()

        chn_text = "你好世界，这是一个测试。"
        chn_mem_id = self.ham_manager.store_experience(chn_text, "user_dialogue_text")
        recalled_chn: Optional[HAMRecallResult] = self.ham_manager.recall_gist(chn_mem_id) # type: ignore
        self.assertIsNotNone(recalled_chn)
        recalled_chn = recalled_chn # type: ignore
        self.assertIn("Radicals (Placeholder):", recalled_chn["rehydrated_gist"])
        self.assertNotIn("POS Tags (Placeholder):", recalled_chn["rehydrated_gist"])
        print("test_12_advanced_text_abstraction_placeholders PASSED")

    # --- Tests for Resource Awareness ---
    def test_13_store_experience_simulated_disk_full(self):
        print("\nRunning test_13_store_experience_simulated_disk_full...")
        # Configure mock resource service to report disk as full
        disk_config_full: SimulatedDiskConfig = { # type: ignore
            "space_gb": 1.0, # Simulated total space
            "warning_threshold_percent": 80,
            "critical_threshold_percent": 95,
            "lag_factor_warning": 1.0,
            "lag_factor_critical": 1.0
        }
        self.mock_resource_service.get_simulated_disk_config.return_value = disk_config_full

        # Mock _get_current_disk_usage_gb to report usage AT or EXCEEDING the limit
        # The save operation itself might add a few bytes, so check against total.
        with patch.object(self.ham_manager_with_res, '_get_current_disk_usage_gb', return_value=1.0) as mock_get_usage:
            # Try to store an experience
            exp_id = self.ham_manager_with_res.store_experience("Data that won't fit", "test_data_disk_full")

            self.assertIsNone(exp_id, "store_experience should return None when simulated disk is full.")
            mock_get_usage.assert_called() # Should be called by _simulate_disk_lag_and_check_limit

            # Verify that the in-memory store also did not grow (or was reverted)
            self.assertEqual(len(self.ham_manager_with_res.core_memory_store), 0,
                             "In-memory store should not contain the item if save failed due to disk full.")
        print("test_13_store_experience_simulated_disk_full PASSED")


    @patch('time.sleep', return_value=None) # Mock time.sleep to avoid actual delays
    def test_14_store_experience_simulated_lag_warning(self, mock_sleep: MagicMock):
        print("\nRunning test_14_store_experience_simulated_lag_warning...")
        disk_config_warning: SimulatedDiskConfig = { # type: ignore
            "space_gb": 10.0,
            "warning_threshold_percent": 70, # Warning at 7GB
            "critical_threshold_percent": 95, # Critical at 9.5GB
            "lag_factor_warning": 2.0,
            "lag_factor_critical": 5.0
        }
        self.mock_resource_service.get_simulated_disk_config.return_value = disk_config_warning

        # Simulate disk usage at 8GB (80% of 10GB), which is above warning (70%) but below critical (95%)
        with patch.object(self.ham_manager_with_res, '_get_current_disk_usage_gb', return_value=8.0):
            with patch('builtins.print') as mock_print: # To check log messages
                exp_id = self.ham_manager_with_res.store_experience("Lag test data - warning", "lag_test_warning")
                self.assertIsNotNone(exp_id, "Experience should still be stored in warning state.")

                mock_sleep.assert_called_once()
                expected_lag = self.ham_manager_with_res.BASE_SAVE_DELAY_SECONDS * disk_config_warning["lag_factor_warning"]
                self.assertAlmostEqual(mock_sleep.call_args[0][0], expected_lag, places=5)

                printed_texts = "".join(str(call_arg[0][0]) for call_arg in mock_print.call_args_list if call_arg[0])
                self.assertIn("INFO - Simulated disk usage", printed_texts)
                self.assertIn("is at WARNING level", printed_texts)
        print("test_14_store_experience_simulated_lag_warning PASSED")

    @patch('time.sleep', return_value=None) # Mock time.sleep
    def test_15_store_experience_simulated_lag_critical(self, mock_sleep: MagicMock):
        print("\nRunning test_15_store_experience_simulated_lag_critical...")
        disk_config_critical: SimulatedDiskConfig = { # type: ignore
            "space_gb": 10.0,
            "warning_threshold_percent": 80, # Warning at 8GB
            "critical_threshold_percent": 90, # Critical at 9GB
            "lag_factor_warning": 1.5,
            "lag_factor_critical": 4.0
        }
        self.mock_resource_service.get_simulated_disk_config.return_value = disk_config_critical

        # Simulate disk usage at 9.5GB (95% of 10GB), which is above critical (90%)
        with patch.object(self.ham_manager_with_res, '_get_current_disk_usage_gb', return_value=9.5):
             with patch('builtins.print') as mock_print:
                exp_id = self.ham_manager_with_res.store_experience("Lag test data - critical", "lag_test_critical")
                self.assertIsNotNone(exp_id, "Experience should still be stored in critical state (if not full).")

                mock_sleep.assert_called_once()
                expected_lag = self.ham_manager_with_res.BASE_SAVE_DELAY_SECONDS * disk_config_critical["lag_factor_critical"]
                self.assertAlmostEqual(mock_sleep.call_args[0][0], expected_lag, places=5)

                printed_texts = "".join(str(call_arg[0][0]) for call_arg in mock_print.call_args_list if call_arg[0])
                self.assertIn("WARNING - Simulated disk usage", printed_texts)
                self.assertIn("is at CRITICAL level", printed_texts)
        print("test_15_store_experience_simulated_lag_critical PASSED")

    def test_16_get_current_disk_usage_gb(self):
        print("\nRunning test_16_get_current_disk_usage_gb...")
        # Test when file doesn't exist (using ham_manager_with_res as its file is cleaned up and not auto-created by default HAM init)
        # Ensure its specific file is gone for this part of the test
        if os.path.exists(self.ham_manager_with_res.core_storage_filepath):
            os.remove(self.ham_manager_with_res.core_storage_filepath)
        self.assertAlmostEqual(self.ham_manager_with_res._get_current_disk_usage_gb(), 0.0, "Disk usage should be 0 if file does not exist.")

        # Test with an actual file (small) - use the ham_manager_no_res instance that does create its file
        self.ham_manager_no_res.store_experience("some data to create file", "test_file_size")
        file_path = self.ham_manager_no_res.core_storage_filepath
        self.assertTrue(os.path.exists(file_path))

        actual_size_bytes = os.path.getsize(file_path)
        expected_gb = actual_size_bytes / (1024**3)

        self.assertAlmostEqual(self.ham_manager_no_res._get_current_disk_usage_gb(), expected_gb, places=9)
        print("test_16_get_current_disk_usage_gb PASSED")

if __name__ == '__main__':
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)
    print(f"HAM Test: Current working directory: {os.getcwd()}")
    print(f"HAM Test: Sys.path: {sys.path}")
    print(f"HAM Test: Test storage directory: {TEST_STORAGE_DIR}")
    unittest.main(verbosity=2)
