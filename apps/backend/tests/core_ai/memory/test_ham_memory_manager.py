import asyncio
import pytest
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# Add the backend to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.core_ai.memory.types import HAMRecallResult
from src.services.types import SimulatedDiskConfig
from src.shared.types.common_types import (
    DialogueMemoryEntryMetadata,
)
from src.services.resource_awareness_service import ResourceAwarenessService
from cryptography.fernet import Fernet, InvalidToken
import hashlib
from unittest.mock import patch, MagicMock
import time

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Define a consistent test output directory (relative to project root)
PROJECT_ROOT_FOR_TEST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEST_STORAGE_DIR = os.path.join(PROJECT_ROOT_FOR_TEST, "tests", "test_output_data", "ham_memory")

@pytest.fixture(scope="function")
def ham_manager_fixture(): # Remove async from fixture
    test_filename = "test_ham_core_memory.json"
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)

    # Standard HAM manager without resource awareness for most tests
    ham_manager_no_res = HAMMemoryManager(core_storage_filename=test_filename)
    if os.path.exists(ham_manager_no_res.core_storage_filepath):
        os.remove(ham_manager_no_res.core_storage_filepath)
    # Re-initialize to ensure it creates a new file if it was removed
    ham_manager_no_res = HAMMemoryManager(core_storage_filename=test_filename)

    # For resource awareness tests, we'll set up a specific HAM manager with a mock service
    mock_resource_service = MagicMock(spec=ResourceAwarenessService)
    mock_resource_service.get_simulated_disk_config.return_value = {
        "space_gb": 10.0,
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 95,
        "lag_factor_warning": 1.0,
        "lag_factor_critical": 1.0
    }
    ham_manager_with_res = HAMMemoryManager(
        core_storage_filename="test_ham_res_aware_memory.json",
        resource_awareness_service=mock_resource_service
    )
    if os.path.exists(ham_manager_with_res.core_storage_filepath):
        os.remove(ham_manager_with_res.core_storage_filepath)
    # Re-initialize this one too
    ham_manager_with_res = HAMMemoryManager(
        core_storage_filename="test_ham_res_aware_memory.json",
        resource_awareness_service=mock_resource_service
    )

    # Yield the managers for the tests
    yield ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename

    # Teardown
    if os.path.exists(ham_manager_no_res.core_storage_filepath):
        os.remove(ham_manager_no_res.core_storage_filepath)
    if os.path.exists(ham_manager_with_res.core_storage_filepath):
        os.remove(ham_manager_with_res.core_storage_filepath)
    try:
        if os.path.exists(TEST_STORAGE_DIR) and not os.listdir(TEST_STORAGE_DIR):
            os.rmdir(TEST_STORAGE_DIR)
    except OSError:
        pass

# Now, rewrite the tests as functions, using the fixture
@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_01_initialization_and_empty_store(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_01_initialization_and_empty_store...")
    assert ham_manager_no_res is not None
    assert len(ham_manager_no_res.core_memory_store) == 0
    assert ham_manager_no_res.next_memory_id == 1
    assert os.path.exists(ham_manager_no_res.core_storage_filepath)
    print("test_01_initialization_and_empty_store PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_02_store_and_recall_text_experience(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_02_store_and_recall_text_experience...")
    raw_text = "Miko had a productive day coding the HAM model."
    metadata: DialogueMemoryEntryMetadata = {
        "speaker": "system_log",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": "MikoAI", "task": "HAM_implementation"
    }

    memory_id = ham_manager_no_res.store_experience(raw_text, "dialogue_text", metadata)
    assert memory_id is not None
    assert memory_id == "mem_000001"
    assert len(ham_manager_no_res.core_memory_store) == 1

    recalled_data: Optional[HAMRecallResult] = ham_manager_no_res.recall_gist(memory_id)
    assert recalled_data is not None
    assert isinstance(recalled_data, dict)
    recalled_data = recalled_data

    assert recalled_data['id'] == memory_id
    assert recalled_data['data_type'] == "dialogue_text"

    assert recalled_data['metadata']['speaker'] == metadata['speaker']
    assert recalled_data['metadata']['project'] == metadata['project']
    assert 'sha256_checksum' in recalled_data['metadata']

    assert "Summary: Miko had a productive day coding the HAM model." in recalled_data['rehydrated_gist']
    assert "Keywords:" in recalled_data['rehydrated_gist']
    gist_keywords_section = recalled_data['rehydrated_gist'].split("Keywords: ", 1)
    if len(gist_keywords_section) > 1:
        gist_keywords = [kw.strip() for kw in gist_keywords_section[1].split("\n")[0].split(",") if kw.strip()]
        assert "miko" in gist_keywords
        assert "coding" in gist_keywords
    else:
        pytest.fail("Keywords section not found in rehydrated_gist")
    print("test_02_store_and_recall_text_experience PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_03_store_and_recall_generic_data(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_03_store_and_recall_generic_data...")
    raw_data = {"temperature": 25, "unit": "Celsius"}
    metadata: Dict[str, Any] = {"sensor_id": "temp001"}

    memory_id = ham_manager_no_res.store_experience(raw_data, "sensor_reading", metadata)
    assert memory_id is not None

    recalled_data: Optional[HAMRecallResult] = ham_manager_no_res.recall_gist(memory_id)
    assert recalled_data is not None
    recalled_data = recalled_data

    assert recalled_data['data_type'] == "sensor_reading"
    assert recalled_data['rehydrated_gist'] == str(raw_data)
    assert recalled_data['metadata']['sensor_id'] == "temp001"
    print("test_03_store_and_recall_generic_data PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_04_persistence(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_04_persistence...")
    test_session_key = Fernet.generate_key()

    with patch.dict(os.environ, {"MIKO_HAM_KEY": test_session_key.decode()}):
        # 使用傳入的 test_filename 變量
        ham_manager_initial = HAMMemoryManager(core_storage_filename=test_filename)
        if os.path.exists(ham_manager_initial.core_storage_filepath):
            os.remove(ham_manager_initial.core_storage_filepath)
        ham_manager_initial = HAMMemoryManager(core_storage_filename=test_filename)

        raw_text = "Testing persistence of HAM."
        exp_id = ham_manager_initial.store_experience(raw_text, "log_entry")
        assert exp_id is not None

        ham_reloaded = HAMMemoryManager(core_storage_filename=test_filename)
        assert len(ham_reloaded.core_memory_store) == 1
        assert ham_reloaded.next_memory_id == ham_manager_initial.next_memory_id

        recalled_data: Optional[HAMRecallResult] = ham_reloaded.recall_gist(exp_id)
        assert recalled_data is not None
        recalled_data = recalled_data
        assert recalled_data.get("rehydrated_gist") == str(raw_text)
    print("test_04_persistence PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_05_recall_non_existent_memory(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_05_recall_non_existent_memory...")
    recalled_data = ham_manager_no_res.recall_gist("mem_nonexistent")
    assert recalled_data is None
    print("test_05_recall_non_existent_memory PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_06_query_memory_keywords(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_06_query_memory_keywords...")
    ham_manager_no_res.store_experience("User query about weather.", "dialogue_text", {"speaker":"user", "timestamp":"ts1", "user": "Alice", "topic": "weather"})
    ham_manager_no_res.store_experience("User query about news.", "dialogue_text", {"speaker":"user", "timestamp":"ts2", "user": "Bob", "topic": "news"})
    ham_manager_no_res.store_experience("Another weather update.", "log_entry", {"speaker":"system", "timestamp":"ts3", "source": "system", "topic": "weather"})

    results: List[HAMRecallResult] = ham_manager_no_res.query_core_memory(keywords=["weather", "alice"])
    assert len(results) == 1
    assert results[0]['metadata']['user'] == "Alice"

    results_topic_simple: List[HAMRecallResult] = ham_manager_no_res.query_core_memory(keywords=["weather"])
    assert len(results_topic_simple) == 2
    print("test_06_query_memory_keywords PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_07_query_memory_data_type(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_07_query_memory_data_type...")
    ham_manager_no_res.store_experience("Dialogue 1", "dialogue_text")
    ham_manager_no_res.store_experience("Log 1", "log_entry")
    ham_manager_no_res.store_experience("Dialogue 2", "dialogue_text")

    results: List[HAMRecallResult] = ham_manager_no_res.query_core_memory(data_type_filter="dialogue_text", limit=10)
    assert len(results) == 2
    for item in results:
        assert item["data_type"] == "dialogue_text"
    print("test_07_query_memory_data_type PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_08_query_memory_date_range(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_08_query_memory_date_range...")
    id1 = ham_manager_no_res.store_experience("Event A", "event", {"speaker":"system", "timestamp":datetime.now(timezone.utc).isoformat()})

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    results: List[HAMRecallResult] = ham_manager_no_res.query_core_memory(date_range=(today_start, today_end))
    assert len(results) >= 1

    future_start = datetime.now(timezone.utc) + timedelta(days=10)
    future_end = future_start + timedelta(days=1)
    results_future: List[HAMRecallResult] = ham_manager_no_res.query_core_memory(date_range=(future_start, future_end))
    assert len(results_future) == 0
    print("test_08_query_memory_date_range PASSED (basic check)")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_09_empty_text_abstraction(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_09_empty_text_abstraction...")
    raw_text = " "
    metadata: DialogueMemoryEntryEntryMetadata = {"speaker":"system", "timestamp":datetime.now(timezone.utc).isoformat(), "test_case": "empty_text"}
    memory_id = ham_manager_no_res.store_experience(raw_text, "dialogue_text", metadata)
    recalled_data: Optional[HAMRecallResult] = ham_manager_no_res.recall_gist(memory_id)
    assert recalled_data is not None
    recalled_data = recalled_data
    assert "Summary: ." in recalled_data["rehydrated_gist"]
    assert "Keywords: " in recalled_data["rehydrated_gist"]
    actual_keywords_section = recalled_data["rehydrated_gist"].split("Keywords: ", 1)
    if len(actual_keywords_section) > 1:
        actual_keywords = actual_keywords_section[1].split("\n")[0]
        assert actual_keywords.strip() == ""
    else:
        pytest.fail("Keywords section not found or malformed in rehydrated_gist for empty text.")
    print("test_09_empty_text_abstraction PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_10_encryption_decryption(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_10_encryption_decryption...")
    original_data_bytes = b"secret data to encrypt"
    encrypted_bytes = ham_manager_no_res._encrypt(original_data_bytes)
    if ham_manager_no_res.fernet:
        assert encrypted_bytes != original_data_bytes
    else:
        assert encrypted_bytes == original_data_bytes
    decrypted_bytes = ham_manager_no_res._decrypt(encrypted_bytes)
    assert decrypted_bytes == original_data_bytes
    if ham_manager_no_res.fernet:
        invalid_token_bytes = b"gAAAAABw..."
        with patch('builtins.print') as mock_print:
            decrypted_invalid = ham_manager_no_res._decrypt(invalid_token_bytes)
        assert decrypted_invalid == b''
        assert any("Invalid token" in call_args[0][0] for call_args in mock_print.call_args_list if call_args[0])
    print("test_10_encryption_decryption PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_11_checksum_verification(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_11_checksum_verification...")
    raw_text = "Data for checksum test."
    metadata_in: DialogueMemoryEntryMetadata = {"speaker":"system","timestamp":datetime.now(timezone.utc).isoformat(),"source": "checksum_test"}
    memory_id = ham_manager_no_res.store_experience(raw_text, "dialogue_text", metadata_in)
    assert memory_id is not None
    stored_package = ham_manager_no_res.core_memory_store.get(memory_id)
    assert stored_package is not None
    assert "metadata" in stored_package
    assert "sha256_checksum" in stored_package["metadata"]
    with patch('builtins.print') as mock_print:
        recalled_data = ham_manager_no_res.recall_gist(memory_id)
        assert recalled_data is not None
        assert "CRITICAL WARNING: Checksum mismatch" not in "".join(str(c[0][0]) for c in mock_print.call_args_list if c[0])
    if memory_id and ham_manager_no_res.fernet:
        corrupted_package_encrypted = ham_manager_no_res.core_memory_store[memory_id]["encrypted_package"][:-5] + b"xxxxx"
        original_package = ham_manager_no_res.core_memory_store[memory_id].copy()
        ham_manager_no_res.core_memory_store[memory_id]["encrypted_package"] = corrupted_package_encrypted
        with patch('builtins.print') as mock_print_corrupt:
            recalled_corrupted = ham_manager_no_res.recall_gist(memory_id)
            if recalled_corrupted is None:
                 assert any("decryption" in call_args[0][0].lower() or "decompression" in call_args[0][0].lower() for call_args in mock_print_corrupt.call_args_list if call_args[0])
            else:
                assert any("CRITICAL WARNING: Checksum mismatch" in call_args[0][0] for call_args in mock_print_corrupt.call_args_list if call_args[0])
        ham_manager_no_res.core_memory_store[memory_id] = original_package
    print("test_11_checksum_verification PASSED (mismatch test depends on encryption state)")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_12_advanced_text_abstraction_placeholders(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_12_advanced_text_abstraction_placeholders...")
    eng_text = "Hello world, this is a test."
    eng_mem_id = ham_manager_no_res.store_experience(eng_text, "user_dialogue_text")
    recalled_eng: Optional[HAMRecallResult] = ham_manager_no_res.recall_gist(eng_mem_id)
    assert recalled_eng is not None
    recalled_eng = recalled_eng
    assert "POS Tags (Placeholder):" in recalled_eng["rehydrated_gist"]
    assert "Radicals (Placeholder):" not in recalled_eng["rehydrated_gist"]

    ham_manager_no_res.core_memory_store = {}
    ham_manager_no_res.next_memory_id = 1
    if os.path.exists(ham_manager_no_res.core_storage_filepath):
        os.remove(ham_manager_no_res.core_storage_filepath)
    ham_manager_no_res._load_core_memory_from_file()

    chn_text = "你好世界，这是一个测试。"
    chn_mem_id = ham_manager_no_res.store_experience(chn_text, "user_dialogue_text")
    recalled_chn: Optional[HAMRecallResult] = ham_manager_no_res.recall_gist(chn_mem_id)
    assert recalled_chn is not None
    recalled_chn = recalled_chn
    assert "Radicals (Placeholder):" in recalled_chn["rehydrated_gist"]
    assert "POS Tags (Placeholder):" not in recalled_chn["rehydrated_gist"]
    print("test_12_advanced_text_abstraction_placeholders PASSED")

# --- Tests for Resource Awareness ---
@pytest.mark.timeout(10)  # 10秒超時，模擬磁盤滿的情況
@pytest.mark.asyncio
async def test_13_store_experience_simulated_disk_full(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_13_store_experience_simulated_disk_full...")
    disk_config_full: SimulatedDiskConfig = {
        "space_gb": 1.0,
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 95,
        "lag_factor_warning": 1.0,
        "lag_factor_critical": 1.0
    }
    mock_resource_service.get_simulated_disk_config.return_value = disk_config_full

    with patch.object(ham_manager_with_res, '_get_current_disk_usage_gb', return_value=1.0) as mock_get_usage:
        exp_id = ham_manager_with_res.store_experience("Data that won't fit", "test_data_disk_full")

        assert exp_id is None, "store_experience should return None when simulated disk is full."
        mock_get_usage.assert_called()

        assert len(ham_manager_with_res.core_memory_store) == 0, \
               "In-memory store should not contain the item if save failed due to disk full."
    print("test_13_store_experience_simulated_disk_full PASSED")

@pytest.mark.timeout(10)  # 10秒超時，模擬延遲警告
@pytest.mark.asyncio
async def test_14_store_experience_simulated_lag_warning(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_14_store_experience_simulated_lag_warning...")
    disk_config_warning: SimulatedDiskConfig = {
        "space_gb": 10.0,
        "warning_threshold_percent": 70,
        "critical_threshold_percent": 95,
        "lag_factor_warning": 2.0,
        "lag_factor_critical": 5.0
    }
    mock_resource_service.get_simulated_disk_config.return_value = disk_config_warning

    with patch.object(ham_manager_with_res, '_get_current_disk_usage_gb', return_value=8.0):
        with patch('builtins.print') as mock_print:
            exp_id = ham_manager_with_res.store_experience("Lag test data - warning", "lag_test_warning")
            assert exp_id is None, "Experience should not be stored in warning state."

            printed_texts = "".join(str(call_arg[0][0]) for call_arg in mock_print.call_args_list if call_arg[0])
            assert "INFO - Simulated disk usage" in printed_texts
            assert "is at WARNING level" in printed_texts
    print("test_14_store_experience_simulated_lag_warning PASSED")

@pytest.mark.timeout(10)  # 10秒超時，模擬嚴重延遲
@pytest.mark.asyncio
async def test_15_store_experience_simulated_lag_critical(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_15_store_experience_simulated_lag_critical...")
    disk_config_critical: SimulatedDiskConfig = {
        "space_gb": 10.0,
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 90,
        "lag_factor_warning": 1.5,
        "lag_factor_critical": 4.0
    }
    mock_resource_service.get_simulated_disk_config.return_value = disk_config_critical

    with patch.object(ham_manager_with_res, '_get_current_disk_usage_gb', return_value=9.5):
         with patch('builtins.print') as mock_print:
            exp_id = ham_manager_with_res.store_experience("Lag test data - critical", "lag_test_critical")
            assert exp_id is None, "Experience should not be stored in critical state."

            printed_texts = "".join(str(call_arg[0][0]) for call_arg in mock_print.call_args_list if call_arg[0])
            assert "WARNING - Simulated disk usage" in printed_texts
            assert "is at CRITICAL level" in printed_texts
    print("test_15_store_experience_simulated_lag_critical PASSED")

@pytest.mark.timeout(10)  # 10秒超時，可能需要較長時間
@pytest.mark.asyncio
async def test_16_get_current_disk_usage_gb(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_16_get_current_disk_usage_gb...")
    if os.path.exists(ham_manager_with_res.core_storage_filepath):
        os.remove(ham_manager_with_res.core_storage_filepath)
    assert ham_manager_with_res._get_current_disk_usage_gb() == pytest.approx(0.0), "Disk usage should be 0 if file does not exist."

    ham_manager_no_res.store_experience("some data to create file", "test_file_size")
    file_path = ham_manager_no_res.core_storage_filepath
    assert os.path.exists(file_path)

    actual_size_bytes = os.path.getsize(file_path)
    expected_gb = actual_size_bytes / (1024**3)

    assert ham_manager_no_res._get_current_disk_usage_gb() == pytest.approx(expected_gb, rel=1e-9)
    print("test_16_get_current_disk_usage_gb PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_17_query_core_memory_return_multiple_candidates(ham_manager_fixture):
    ham_manager_no_res, ham_manager_with_res, mock_resource_service, test_filename = ham_manager_fixture
    print("\nRunning test_17_query_core_memory_return_multiple_candidates...")
    ham = ham_manager_no_res
    for i in range(10):
        ham.store_experience(f"Candidate test item {i}", "candidate_test", {})

    results = ham.query_core_memory(data_type_filter="candidate_test", limit=5, return_multiple_candidates=True)
    assert len(results) == 5
    print("test_17_query_core_memory_return_multiple_candidates PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_18_encryption_failure(ham_manager_fixture, monkeypatch):
    """測試加密失敗時的錯誤處理"""
    ham_manager_no_res, _, _, _ = ham_manager_fixture
    print("\nRunning test_18_encryption_failure...")
    
    # 模擬加密失敗
    def mock_encrypt(data):
        raise Exception("Encryption failed")
    
    monkeypatch.setattr(ham_manager_no_res, '_encrypt', mock_encrypt)
    
    # 存儲應該失敗
    with pytest.raises(Exception, match="Failed to store experience: Encryption failed"):
        ham_manager_no_res.store_experience("Test data", "test_type")
    print("test_18_encryption_failure PASSED")

@pytest.mark.timeout(5)  # 5秒超時
@pytest.mark.asyncio
async def test_19_disk_full_handling(ham_manager_fixture, monkeypatch):
    """測試磁盤空間不足時的處理"""
    ham_manager_no_res, _, _, _ = ham_manager_fixture
    print("\nRunning test_19_disk_full_handling...")
    
    # 模擬_get_current_disk_usage_gb返回高使用率（超過10GB閾值）
    def mock_get_disk_usage():
        return 10.5  # 超過10GB閾值，觸發磁盤空間不足
    
    monkeypatch.setattr(ham_manager_no_res, '_get_current_disk_usage_gb', mock_get_disk_usage)
    
    # 存儲應該失敗
    with pytest.raises(Exception, match="Insufficient disk space"):
        ham_manager_no_res.store_experience("Test data", "test_type")
    print("test_19_disk_full_handling PASSED")

@pytest.mark.timeout(10)  # 10秒超時，因為這個測試可能涉及等待
@pytest.mark.asyncio
async def test_20_delete_old_experiences(ham_manager_fixture, monkeypatch):
    """測試自動清理舊記憶"""
    ham_manager_no_res, _, _, _ = ham_manager_fixture
    print("\nRunning test_20_delete_old_experiences...")
    
    # 添加一些測試記憶
    for i in range(5):
        ham_manager_no_res.store_experience(f"Test memory {i}", "test_type")
    
    # 保存初始記憶數量
    initial_count = len(ham_manager_no_res.core_memory_store)
    
    # 模擬高內存使用率
    def mock_memory_usage():
        return 0.9  # 90% 使用率
    
    # 創建一個模擬的 personality_manager
    class MockPersonalityManager:
        def get_current_personality_trait(self, trait_name, default=None):
            return 0.1  # 低保留率，更積極地清理
    
    # 替換 personality_manager
    ham_manager_no_res.personality_manager = MockPersonalityManager()
    
    # 模擬高內存使用率
    with patch('psutil.virtual_memory') as mock_virtual_memory:
        mock_virtual_memory.return_value.total = 100
        mock_virtual_memory.return_value.available = 10 # 90% usage

        # Manually trigger cleanup
        ham_manager_no_res._perform_deletion_check()
    
    # 驗證部分記憶已被清理
    final_count = len(ham_manager_no_res.core_memory_store)
    assert final_count < initial_count, f"Expected some memories to be deleted, but count remained at {final_count}"
    print("test_20_delete_old_experiences PASSED")

@pytest.mark.timeout(10)  # 10秒超時，因為這個測試涉及並發操作
@pytest.mark.asyncio
async def test_21_concurrent_access(ham_manager_fixture):
    """測試並發訪問記憶管理器"""
    ham_manager_no_res, _, _, _ = ham_manager_fixture
    print("\nRunning test_21_concurrent_access...")
    
    async def store_memory(i):
        memory_id = ham_manager_no_res.store_experience(
            f"Concurrent test {i}", 
            "concurrent_test",
            {"index": i, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        return memory_id, i
    
    # 並發存儲多個記憶
    tasks = [store_memory(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    # 驗證所有記憶都已正確存儲
    for mem_id, i in results:
        result = ham_manager_no_res.recall_gist(mem_id)
        assert result is not None, f"Memory {i} was not stored correctly"
        assert f"Concurrent test {i}" in str(result['rehydrated_gist']), f"Incorrect content for memory {i}"
    
    # 驗證查詢功能正常工作
    query_results = ham_manager_no_res.query_core_memory(
        data_type_filter="concurrent_test",
        limit=10
    )
    assert len(query_results) == 10, "Expected 10 concurrent test memories"
    print("test_21_concurrent_access PASSED")
