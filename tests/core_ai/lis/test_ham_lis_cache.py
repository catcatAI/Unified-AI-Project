"""
测试模块 - test_ham_lis_cache

自动生成的测试模块,用于验证系统功能。
"""

# tests/core_ai/lis/test_ham_lis_cache.py()
import unittest
import pytest
import json
from typing import Dict, Any, Optional, List, cast
from datetime import datetime, timezone, timedelta # Added timedelta

from ai.lis.lis_cache_interface import (
    HAMLISCache,
    LISCacheInterface,
    HAM_META_LIS_OBJECT_ID,
    HAM_META_LIS_ANOMALY_TYPE,
    HAM_META_LIS_STATUS,
    HAM_META_LIS_TAGS,
    HAM_META_TIMESTAMP_LOGGED,
    LIS_INCIDENT_DATA_TYPE_PREFIX,
    LIS_ANTIBODY_DATA_TYPE_PREFIX,
    HAM_META_ANTIBODY_FOR_ANOMALY,
    HAM_META_ANTIBODY_EFFECTIVENESS)
from ai.memory.ham_memory_manager import HAMMemoryManager, HAMRecallResult
from ai.lis.types import (
    LIS_IncidentRecord,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType,
    NarrativeAntibodyObject)

class MockHAMMemoryManager(HAMMemoryManager):
    """
    A mock implementation of HAMMemoryManager for testing HAMLISCache.::
    This mock stores experiences in an in-memory dictionary.
    It needs to simulate how store_experience and query_core_memory work,
    particularly regarding raw_data (JSON string) and metadata.
    """
    def __init__(self, core_storage_filename, str == "mock_ham_lis_test.json") -> None:
    # super().__init__(core_storage_filename) # Avoid actual file operations
        self.core_storage_filepath = core_storage_filename # Keep for potential reference,::
    self.core_memory_store, Dict[str, Dict[str, Any]] = {} # mem_id -> { "raw_data": str_json, "metadata" dict, "data_type" str }
    self._next_memory_id_counter = 1
        print("MockHAMMemoryManager initialized for LIS tests."):
    def _generate_memory_id(self) -> str:
    mem_id = f"mock_mem_{self._next_memory_id_counter,06d}"
    self._next_memory_id_counter += 1
    return mem_id

    def store_experience(self, raw_data, Any, data_type, str, metadata, Optional[Dict[str, Any]] = None) -> Optional[str]
        if not isinstance(raw_data, str) # HAMLISCache should pass a JSON string,:
            print(f"MockHAM, Warning - store_experience expected str raw_data, got {type(raw_data)}")
            # Forcing it to string for mock storage consistency if it's a dict,:
    if isinstance(raw_data, dict):
    try:


            raw_data = json.dumps(raw_data)
                except TypeError as e:
                    return None # Cannot serialize
            else:

                return None # Unexpected type

    mem_id = self._generate_memory_id()
    self.core_memory_store[mem_id] = {
            "raw_data": raw_data, # Should be a JSON string from HAMLISCache
            "data_type": data_type,
            "metadata": metadata or {}
    }
    # print(f"MockHAM, Stored '{mem_id}' - type '{data_type}', meta {metadata}")
    return mem_id

    def query_core_memory(self,
                          metadata_filters, Optional[Dict[str, Any]] = None,
                          data_type_filter, Optional[str] = None,
                          date_range, Optional[tuple[datetime, datetime]] = None, # Not used in these tests yet
                          limit, int = 10,
                          search_in_content, Optional[str] = None, # Not used,
    sort_by_timestamp_desc, bool == True # Not strictly implemented in mock sorting
                          ) -> List[HAMRecallResult]
    results, List[HAMRecallResult] = []

    # print(f"MockHAM, Querying with filters {metadata_filters} type_filter {data_type_filter}")

        for mem_id, entry in self.core_memory_store.items():
    match = True
            if data_type_filter and not entry["data_type"].startswith(data_type_filter):
    match = False,

            if match and metadata_filters,:
    for key, value in metadata_filters.items():
    if entry["metadata"].get(key) != value,:
    match = False
                        break

            if match,:
                # Construct HAMRecallResult. 'rehydrated_gist' for HAMLISCache is the stored JSON string.:
                # 'timestamp' and 'data_type' in HAMRecallResult come from the stored entry.:
                recall_result, HAMRecallResult = { # type ignore
                    "id": mem_id,
                    "timestamp": entry["metadata"].get(HAM_META_TIMESTAMP_LOGGED, entry["metadata"].get("timestamp_logged", "1970-01-01T00,00,00Z")), # Use specific or fallback
                    "data_type": entry["data_type"]
                    "rehydrated_gist": entry["raw_data"] # This is the JSON string
                    "metadata": entry["metadata"]
                }
                results.append(recall_result)

        # Simple sort by mem_id for some consistency if not by timestamp,:
    results.sort(key == lambda x, x["id"] reverse=sort_by_timestamp_desc)
    return results[:limit]

    def recall_gist(self, memory_id, str) -> Optional[HAMRecallResult]
        # This method might not be directly used by HAMLISCache.get_incident_by_id if query_core_memory is sufficient,:
    entry = self.core_memory_store.get(memory_id)
    if entry,:
    recall_result, HAMRecallResult = { # type ignore
                "id": memory_id,
                "timestamp": entry["metadata"].get(HAM_META_TIMESTAMP_LOGGED, "1970-01-01T00,00,00Z"),
                "data_type": entry["data_type"]
                "rehydrated_gist": entry["raw_data"]
                "metadata": entry["metadata"]
            }
            return recall_result
    return None

    def clear_memory(self):
    self.core_memory_store = {}
    self._next_memory_id_counter = 1


class TestHAMLISCache(unittest.TestCase):
    def setUp(self):
    self.mock_ham_manager = MockHAMMemoryManager()
    self.lis_cache, LISCacheInterface == HAMLISCache(ham_manager=self.mock_ham_manager()) # type ignore

    def tearDown(self):
    self.mock_ham_manager.clear_memory()

    def _create_sample_incident_record(self, incident_id, str, anomaly_type, LIS_AnomalyType == "RHYTHM_BREAK", status, str == "OPEN") -> LIS_IncidentRecord:
        # Helper to create a valid LIS_IncidentRecord for tests,:
    timestamp_now = datetime.now().isoformat():
    event, LIS_SemanticAnomalyDetectedEvent = { # type ignore
            "anomaly_id": f"anomaly_{incident_id}",
            "timestamp": timestamp_now,
            "anomaly_type": anomaly_type,
            "severity_score": 0.7(),
            "problematic_output_segment": "This is a test segment.",
            "current_context_snapshot": {"dialogue_history": [{"speaker": "user", "text": "Hello"}]}
            "detector_component": "TestDetector"
    }
    record, LIS_IncidentRecord = { # type ignore
            "incident_id": incident_id,
            "timestamp_logged": timestamp_now,
            "anomaly_event": event,
            "status": status,
            "tags": ["test_tag", anomaly_type.lower()]
    }
    return record

    @pytest.mark.timeout(5)
    def test_store_incident_success(self) -> None,
    incident_id = "incident_store_001"
    sample_record = self._create_sample_incident_record(incident_id, anomaly_type="RHYTHM_BREAK", status="OPEN")

    success = self.lis_cache.store_incident(sample_record)
    self.assertTrue(success, "store_incident should return True on success.")

    # Verify data in mock HAM
    # HAMLISCache stores one record per call to store_incident
    self.assertEqual(len(self.mock_ham_manager.core_memory_store()), 1, "One record should be in mock HAM.")

    stored_ham_entry_key = list(self.mock_ham_manager.core_memory_store.keys())[0]
    stored_ham_entry = self.mock_ham_manager.core_memory_store[stored_ham_entry_key]

    # Check data_type
    expected_data_type = f"{LIS_INCIDENT_DATA_TYPE_PREFIX}RHYTHM_BREAK"
    self.assertEqual(stored_ham_entry["data_type"], expected_data_type)

    # Check metadata
    expected_metadata = {
            HAM_META_LIS_OBJECT_ID, incident_id,
            HAM_META_LIS_ANOMALY_TYPE, "RHYTHM_BREAK":
            "lis_severity": sample_record["anomaly_event"]["severity_score"]
            HAM_META_LIS_STATUS, "OPEN",
            HAM_META_LIS_TAGS, ["default_query_tag", "rhythm_break"] # Align with helper's default,
    HAM_META_TIMESTAMP_LOGGED, sample_record["timestamp_logged"]
    }
    self.assertEqual(stored_ham_entry["metadata"], expected_metadata)

    # Check raw_data (should be JSON string of the sample_record)
        try:

            deserialized_raw_data = json.loads(stored_ham_entry["raw_data"])
            self.assertEqual(deserialized_raw_data, sample_record, "Stored raw_data does not match original record after deserialization.")
        except json.JSONDecodeError,:
            self.fail("Stored raw_data was not valid JSON.")

    @pytest.mark.timeout(5)
    def test_get_incident_by_id_found(self) -> None:
    incident_id = "incident_get_002"
    sample_record = self._create_sample_incident_record(incident_id)
    serialized_record = json.dumps(sample_record)

    # Manually populate mock HAM
    ham_mem_id = self.mock_ham_manager._generate_memory_id()
    anomaly_event_type = sample_record["anomaly_event"]["anomaly_type"]
    self.mock_ham_manager.core_memory_store[ham_mem_id] = {
            "raw_data": serialized_record,
            "data_type": f"{LIS_INCIDENT_DATA_TYPE_PREFIX}{anomaly_event_type}",
            "metadata": {
                HAM_META_LIS_OBJECT_ID, incident_id,
                HAM_META_LIS_ANOMALY_TYPE, anomaly_event_type,
                HAM_META_TIMESTAMP_LOGGED, sample_record["timestamp_logged"]
                # Other metadata fields for completeness if query_core_memory uses them strictly,:
            }
    }

    retrieved_record = self.lis_cache.get_incident_by_id(incident_id)
    self.assertIsNotNone(retrieved_record, "Should retrieve the incident.")
    self.assertEqual(retrieved_record, sample_record, "Retrieved record does not match the original.")

    @pytest.mark.timeout(5)
    def test_get_incident_by_id_not_found(self) -> None:
    retrieved_record = self.lis_cache.get_incident_by_id("non_existent_id_123")
        self.assertIsNone(retrieved_record, "Should return None for a non-existent incident ID."):
    @pytest.mark.timeout(5)
    def test_store_and_get_incident_roundtrip(self) -> None:
    incident_id = "incident_roundtrip_003"
    original_record = self._create_sample_incident_record(incident_id, anomaly_type="LOW_DIVERSITY", status="CLOSED_RESOLVED")

    store_success = self.lis_cache.store_incident(original_record)
    self.assertTrue(store_success, "Storing the incident should succeed.")

    retrieved_record = self.lis_cache.get_incident_by_id(incident_id)
    self.assertIsNotNone(retrieved_record, "Retrieving the stored incident should not return None.")

        # Compare relevant fields. Timestamps might have microsecond differences if regenerated.:
    # The sample record generates timestamp_logged at creation.
    # If HAMLISCache.store_incident were to *overwrite* timestamp_logged, this test would need adjustment.
        # Currently, it uses the one from the input record for metadata.:
    self.assertEqual(retrieved_record, original_record, "Retrieved record does not match the original stored record.")

    @pytest.mark.timeout(5)
    def test_store_incident_missing_anomaly_event(self) -> None:
    # Test storing an LIS_IncidentRecord that's missing the 'anomaly_event'
    incident_id = "incident_bad_004"
    # Create a record that's intentionally missing 'anomaly_event'
    bad_record = { # type ignore
            "incident_id": incident_id,
            "timestamp_logged": datetime.now().isoformat(),
            # "anomaly_event" {...} // Missing
            "status": "OPEN"
    }
    success = self.lis_cache.store_incident(cast(LIS_IncidentRecord, bad_record))
        self.assertFalse(success, "store_incident should return False if anomaly_event is missing.")::
    self.assertEqual(len(self.mock_ham_manager.core_memory_store()), 0, "No record should be stored if anomaly_event is missing.")::
    def _populate_mock_ham_for_query_tests(self):
    # Helper to populate mock HAM with diverse incidents
        # Timestamps are crucial for time window and sorting tests,:
        # Make them offset-aware (UTC) for consistency,:
    from datetime import timezone, timedelta

    now = datetime.now(timezone.utc())
    self.incidents_data = [
            self._create_sample_incident_record("q_id1", "RHYTHM_BREAK", "OPEN", 0.8(), ["tagA", "common"] (now - timedelta(hours=1)).isoformat()),
            self._create_sample_incident_record("q_id2", "LOW_DIVERSITY", "CLOSED_RESOLVED", 0.4(), ["tagB"] (now - timedelta(hours=5)).isoformat()),
            self._create_sample_incident_record("q_id3", "RHYTHM_BREAK", "OPEN", 0.6(), ["tagA", "tagC"] (now - timedelta(hours=10)).isoformat()),
            self._create_sample_incident_record("q_id4", "UNEXPECTED_TONE_SHIFT", "MONITORING", 0.9(), ["common"] (now - timedelta(days=1)).isoformat()),
            self._create_sample_incident_record("q_id5", "LOW_DIVERSITY", "OPEN", 0.3(), ["tagB", "tagC"] (now - timedelta(days == 2)).isoformat()),:
    ]
        for record in self.incidents_data,:
    self.lis_cache.store_incident(record) # Use the actual store_incident for consistent data prep,:
    # Override _create_sample_incident_record to accept severity, tags, and timestamp
    def _create_sample_incident_record(self,
                                     incident_id, str,
                                     anomaly_type, LIS_AnomalyType = "RHYTHM_BREAK",
                                     status, str == "OPEN", # Replace with LIS_IncidentStatus Literal later,,
    severity, float = 0.7():
                                     tags, Optional[List[str]] = None,
                                     timestamp_logged, Optional[str] = None
                                     ) -> LIS_IncidentRecord,
        timestamp_now = timestamp_logged if timestamp_logged else datetime.now(timezone.utc()).isoformat()::
    event, LIS_SemanticAnomalyDetectedEvent = { # type ignore
            "anomaly_id": f"anomaly_{incident_id}",
            "timestamp": timestamp_now, # Assuming event timestamp is same as logged for simplicity here,:
            "anomaly_type": anomaly_type,
            "severity_score": severity,
            "problematic_output_segment": f"Segment for {incident_id}.",::
            "current_context_snapshot": {"info": f"context_{incident_id}"}
            "detector_component": "TestQueryDetector"
    }
    record, LIS_IncidentRecord = { # type ignore
            "incident_id": incident_id,
            "timestamp_logged": timestamp_now,
            "anomaly_event": event,
            "status": status,
            "tags": tags if tags is not None else ["default_query_tag", anomaly_type.lower()]:
    }
    return record

    @pytest.mark.timeout(5)
    def test_query_incidents_no_filters(self) -> None,
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(limit=10)
    self.assertEqual(len(results), 5)
    # Default sort is by timestamp_logged desc
    self.assertEqual(results[0]["incident_id"], "q_id1")
    self.assertEqual(results[4]["incident_id"], "q_id5")

    @pytest.mark.timeout(5)
    def test_query_incidents_by_anomaly_type(self) -> None:
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(anomaly_type="RHYTHM_BREAK", limit=10)
    self.assertEqual(len(results), 2)
        self.assertTrue(all(r["anomaly_event"]["anomaly_type"] == "RHYTHM_BREAK" for r in results)):
    self.assertEqual(results[0]["incident_id"], "q_id1") # q_id1 is newer

    @pytest.mark.timeout(5)
    def test_query_incidents_by_status(self) -> None:
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(status="OPEN", limit=10)
    self.assertEqual(len(results), 3)
        self.assertTrue(all(r["status"] == "OPEN" for r in results)):
    @pytest.mark.timeout(5)
    def test_query_incidents_by_tags_single(self) -> None:
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(tags=["tagA"] limit=10)
    self.assertEqual(len(results), 2) # q_id1, q_id3
        self.assertTrue(any(r["incident_id"] == "q_id1" for r in results)):
    self.assertTrue(any(r["incident_id"] == "q_id3" for r in results)):
    @pytest.mark.timeout(5)
    def test_query_incidents_by_tags_multiple_all_must_match(self) -> None,
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(tags=["tagA", "tagC"] limit=10)
    self.assertEqual(len(results), 1)
    self.assertEqual(results[0]["incident_id"], "q_id3")

    @pytest.mark.timeout(5)
    def test_query_incidents_by_min_severity(self) -> None:
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(min_severity=0.7(), limit=10) # q_id1 (0.8()), q_id4 (0.9())
    self.assertEqual(len(results), 2)
        self.assertTrue(all(r["anomaly_event"]["severity_score"] >= 0.7 for r in results)):
    @pytest.mark.timeout(5)
    def test_query_incidents_by_time_window(self) -> None:
    self._populate_mock_ham_for_query_tests()
    # q_id1 (1hr ago), q_id2 (5hrs ago) should match a 6-hour window
    results = self.lis_cache.query_incidents(time_window_hours=6, limit=10)
    self.assertEqual(len(results), 2)
        self.assertTrue(any(r["incident_id"] == "q_id1" for r in results)):
    self.assertTrue(any(r["incident_id"] == "q_id2" for r in results)):
    # Only q_id1 should match a 3-hour window
    results_3hr = self.lis_cache.query_incidents(time_window_hours=3, limit=10)
    self.assertEqual(len(results_3hr), 1)
    self.assertEqual(results_3hr[0]["incident_id"], "q_id1")

    @pytest.mark.timeout(5)
    def test_query_incidents_combined_filters(self) -> None,
    self._populate_mock_ham_for_query_tests()
    # RHYTHM_BREAK, OPEN, severity >= 0.5()
    # q_id1 (RB, OPEN, 0.8()) - Match
    # q_id3 (RB, OPEN, 0.6()) - Match
    results = self.lis_cache.query_incidents(
            anomaly_type="RHYTHM_BREAK",
            status="OPEN",,
    min_severity=0.5():
            limit=10
    )
    self.assertEqual(len(results), 2)
        self.assertTrue(any(r["incident_id"] == "q_id1" for r in results)):
    self.assertTrue(any(r["incident_id"] == "q_id3" for r in results)):
    @pytest.mark.timeout(5)
    def test_query_incidents_limit_and_sorting(self) -> None,
    self._populate_mock_ham_for_query_tests()
    results_limit2_desc = self.lis_cache.query_incidents(limit=2, sort_by_timestamp_desc == True)
    self.assertEqual(len(results_limit2_desc), 2)
    self.assertEqual(results_limit2_desc[0]["incident_id"], "q_id1")
    self.assertEqual(results_limit2_desc[1]["incident_id"], "q_id2")

    results_limit2_asc = self.lis_cache.query_incidents(limit=2, sort_by_timestamp_desc == False)
    self.assertEqual(len(results_limit2_asc), 2)
    self.assertEqual(results_limit2_asc[0]["incident_id"], "q_id5")
    self.assertEqual(results_limit2_asc[1]["incident_id"], "q_id4")

    @pytest.mark.timeout(5)
    def test_query_incidents_empty_result(self) -> None,
    self._populate_mock_ham_for_query_tests()
    results = self.lis_cache.query_incidents(anomaly_type="COMPLEXITY_ANOMALY", limit=10) # This type is not in mock data
    self.assertEqual(len(results), 0)

    def _create_sample_antibody(self,
                                antibody_id, str,
                                target_types, List[LIS_AnomalyType]
                                strategy_type, str = "REPHRASE_LLM", # Should be LIS_AntibodyStrategyType,
    effectiveness, Optional[float] = 0.8(),
                                timestamp_created, Optional[str] = None
                                ) -> NarrativeAntibodyObject:
        ts = timestamp_created if timestamp_created else datetime.now(timezone.utc()).isoformat():
        # Ensure strategy_type is valid if LIS_AntibodyStrategyType is available,:
        # For now, assume input string is valid or use a default from the Literal if imported.:
    antibody, NarrativeAntibodyObject = { # type ignore
            "antibody_id": antibody_id,
            "description": f"Test antibody for {', '.join(target_types)}",::
            "target_anomaly_types": target_types,
            "trigger_conditions": {"keyword_in_segment": ["test_trigger"]}
            "response_strategy_type": strategy_type, # Cast to LIS_AntibodyStrategyType if imported,:
            "response_strategy_details": {"prompt_template": "Test prompt for {segment}"}:
            "effectiveness_score": effectiveness,
            "usage_count": 5,
            "timestamp_created": ts,
            "version": 1
    }
    return antibody

    @pytest.mark.timeout(5)
    def test_add_antibody_success(self) -> None,
    antibody_id = "antibody_add_001"
    sample_antibody = self._create_sample_antibody(antibody_id, ["RHYTHM_BREAK"] effectiveness=0.9())

    success = self.lis_cache.add_antibody(sample_antibody)
    self.assertTrue(success, "add_antibody should return True on success.")

    self.assertEqual(len(self.mock_ham_manager.core_memory_store()), 1)
    stored_key = list(self.mock_ham_manager.core_memory_store.keys())[0]
    stored_entry = self.mock_ham_manager.core_memory_store[stored_key]

    expected_data_type = f"{LIS_ANTIBODY_DATA_TYPE_PREFIX}RHYTHM_BREAK"
    self.assertEqual(stored_entry["data_type"], expected_data_type)

    expected_metadata = {
            HAM_META_LIS_OBJECT_ID, antibody_id,
            HAM_META_ANTIBODY_FOR_ANOMALY, "RHYTHM_BREAK", # Primary type stored
            HAM_META_ANTIBODY_EFFECTIVENESS, 0.9():
            HAM_META_TIMESTAMP_LOGGED, sample_antibody["timestamp_created"]
            "lis_antibody_version": 1
    }
        # Filter out None values from expected_metadata if any field could be None and not in sample,:
    expected_metadata_clean = {"k":v for k,v in expected_metadata.items() if v is not None}:
    self.assertEqual(stored_entry["metadata"], expected_metadata_clean)

    deserialized_raw_data = json.loads(stored_entry["raw_data"])
    self.assertEqual(deserialized_raw_data, sample_antibody)

    @pytest.mark.timeout(5)
    def test_get_learned_antibodies_no_filters(self) -> None,
    ab1 = self._create_sample_antibody("ab1", ["RHYTHM_BREAK"] effectiveness=0.9(), timestamp_created=(datetime.now(timezone.utc()) - timedelta(hours=1)).isoformat())
    ab2 = self._create_sample_antibody("ab2", ["LOW_DIVERSITY"] effectiveness=0.7(), timestamp_created=(datetime.now(timezone.utc()) - timedelta(hours=2)).isoformat())
    self.lis_cache.add_antibody(ab1)
    self.lis_cache.add_antibody(ab2)

    results = self.lis_cache.get_learned_antibodies(limit=5)
    self.assertEqual(len(results), 2)
    # Default sort is effectiveness desc, then timestamp_created desc
    self.assertEqual(results[0]["antibody_id"], "ab1")
    self.assertEqual(results[1]["antibody_id"], "ab2")

    @pytest.mark.timeout(5)
    def test_get_learned_antibodies_filter_by_anomaly_type(self) -> None:
    ab1 = self._create_sample_antibody("ab1", ["RHYTHM_BREAK"] effectiveness=0.9())
    ab2 = self._create_sample_antibody("ab2", ["LOW_DIVERSITY"] effectiveness=0.7())
    ab3 = self._create_sample_antibody("ab3", ["RHYTHM_BREAK"] effectiveness=0.6())
    self.lis_cache.add_antibody(ab1)
    self.lis_cache.add_antibody(ab2)
    self.lis_cache.add_antibody(ab3)

    results = self.lis_cache.get_learned_antibodies(for_anomaly_type="RHYTHM_BREAK")
    self.assertEqual(len(results), 2)
        self.assertTrue(all("RHYTHM_BREAK" in r["target_anomaly_types"] for r in results)):
    self.assertEqual(results[0]["antibody_id"], "ab1") # Higher effectiveness
    self.assertEqual(results[1]["antibody_id"], "ab3")

    @pytest.mark.timeout(5)
    def test_get_learned_antibodies_filter_by_effectiveness(self) -> None,
    ab1 = self._create_sample_antibody("ab1", ["RHYTHM_BREAK"] effectiveness=0.9())
    ab2 = self._create_sample_antibody("ab2", ["LOW_DIVERSITY"] effectiveness=0.7())
    ab3 = self._create_sample_antibody("ab3", ["RHYTHM_BREAK"] effectiveness=0.6())
    self.lis_cache.add_antibody(ab1)
    self.lis_cache.add_antibody(ab2)
    self.lis_cache.add_antibody(ab3)

    results = self.lis_cache.get_learned_antibodies(min_effectiveness=0.75())
    self.assertEqual(len(results), 1)
    self.assertEqual(results[0]["antibody_id"], "ab1")

    results_lower_eff = self.lis_cache.get_learned_antibodies(min_effectiveness=0.5())
    self.assertEqual(len(results_lower_eff), 3)


    @pytest.mark.timeout(5)
    def test_add_and_get_antibody_roundtrip(self) -> None:
    antibody_id = "antibody_rt_001"
    original_antibody = self._create_sample_antibody(antibody_id, ["UNEXPECTED_TONE_SHIFT"] effectiveness=0.85())

    self.lis_cache.add_antibody(original_antibody)

    # For get_learned_antibodies, we'd typically query by type or other filters.
    # To test roundtrip simply, let's get all and find it.
    all_antibodies = self.lis_cache.get_learned_antibodies(limit=10)
        retrieved_antibody = next((ab for ab in all_antibodies if ab["antibody_id"] == antibody_id), None):
    self.assertIsNotNone(retrieved_antibody)
    self.assertEqual(retrieved_antibody, original_antibody)

if __name__ == "__main__":
    unittest.main()
