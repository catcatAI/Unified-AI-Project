import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import logging # For caplog if needed, or to check logs from module

# Ensure src is in path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.trust_manager.trust_manager_module import TrustManager # For type hinting and mocking
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope # For creating test payloads

# --- Mock TrustManager ---
@pytest.fixture
def mock_trust_manager():
    mock_tm = MagicMock(spec=TrustManager)
    # Default behavior: always return a neutral trust score
    mock_tm.get_trust_score.return_value = 0.5
    return mock_tm

# --- Test ServiceDiscoveryModule ---
class TestServiceDiscoveryModule:

    def test_init(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)
        assert sdm.trust_manager == mock_trust_manager
        assert sdm.known_capabilities == {}
        assert sdm.lock is not None
        # logger.info("HSP ServiceDiscoveryModule initialized.") - Check log if desired with caplog

    def test_process_capability_advertisement_new_and_update(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)

        cap_id_1 = "cap_test_001"
        # Provide all required fields for HSPCapabilityAdvertisementPayload based on its TypedDict definition
        payload1 = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id_1, ai_id="ai1", name="TestCap1", description="Desc1",
            version="1.0", availability_status="online",
            # Optional fields can be omitted or set to None if that's how they are defined
            tags=["t1", "t2"],
            input_schema_uri=None, input_schema_example=None,
            output_schema_uri=None, output_schema_example=None,
            data_format_preferences=None, hsp_protocol_requirements=None,
            cost_estimate_template=None, access_policy_id=None
        )
        mock_envelope = MagicMock(spec=HSPMessageEnvelope)

        time_before_add = datetime.now(timezone.utc)
        sdm.process_capability_advertisement(payload1, "sender_ai_id_1", mock_envelope)
        time_after_add = datetime.now(timezone.utc)

        assert cap_id_1 in sdm.known_capabilities
        stored_payload1, stored_time1 = sdm.known_capabilities[cap_id_1]
        assert stored_payload1 == payload1
        assert time_before_add <= stored_time1 <= time_after_add

        # Test update
        payload1_updated = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id_1, ai_id="ai1", name="TestCap1_Updated", description="Desc1_Updated",
            version="1.1", availability_status="online", tags=["t1", "t3"],
            input_schema_uri=None, input_schema_example=None,
            output_schema_uri=None, output_schema_example=None,
            data_format_preferences=None, hsp_protocol_requirements=None,
            cost_estimate_template=None, access_policy_id=None
        )
        time_before_update = datetime.now(timezone.utc)
        sdm.process_capability_advertisement(payload1_updated, "sender_ai_id_1", mock_envelope)
        time_after_update = datetime.now(timezone.utc)

        assert cap_id_1 in sdm.known_capabilities
        stored_payload1_upd, stored_time1_upd = sdm.known_capabilities[cap_id_1]
        assert stored_payload1_upd == payload1_updated
        assert stored_payload1_upd.get("name") == "TestCap1_Updated"
        assert time_before_update <= stored_time1_upd <= time_after_update
        assert stored_time1_upd > stored_time1 # Ensure timestamp was updated

    def test_process_capability_advertisement_missing_ids(self, mock_trust_manager: MagicMock, caplog):
        caplog.set_level(logging.ERROR, logger="src.core_ai.service_discovery.service_discovery_module")
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)
        mock_envelope = MagicMock(spec=HSPMessageEnvelope)

        # Missing capability_id
        # Ensure all *required* fields for HSPCapabilityAdvertisementPayload are present for the parts that don't cause error
        payload_no_cap_id = { # type: ignore
            "ai_id": "ai_no_cap_id", "name": "NoCapIdService", "description": "d",
            "version": "v", "availability_status": "online"
        }
        sdm.process_capability_advertisement(payload_no_cap_id, "sender1", mock_envelope) # type: ignore
        assert "Received capability advertisement with no capability_id" in caplog.text
        assert not sdm.known_capabilities # Should not be added

        caplog.clear()
        # Missing ai_id in payload
        payload_no_ai_id = { # type: ignore
            "capability_id": "cap_no_ai_id", "name": "NoAiIdService", "description": "d",
            "version": "v", "availability_status": "online"
        }
        sdm.process_capability_advertisement(payload_no_ai_id, "sender2", mock_envelope) # type: ignore
        assert "Received capability advertisement (ID: cap_no_ai_id) with no 'ai_id'" in caplog.text
        assert not sdm.known_capabilities

    def test_get_capability_by_id(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)
        cap_id = "get_cap_001"
        payload = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id, ai_id="ai_get", name="GetCap", description="d", version="v",
            availability_status="online", input_schema_uri=None, input_schema_example=None,
            output_schema_uri=None, output_schema_example=None, data_format_preferences=None,
            hsp_protocol_requirements=None, cost_estimate_template=None, access_policy_id=None, tags=None
        )
        sdm.process_capability_advertisement(payload, "sender", MagicMock(spec=HSPMessageEnvelope))

        found_payload = sdm.get_capability_by_id(cap_id)
        assert found_payload == payload

        assert sdm.get_capability_by_id("non_existent_id") is None

    # --- Tests for find_capabilities ---
    @pytest.fixture
    def populated_sdm(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)

        mock_trust_manager.get_trust_score.side_effect = lambda ai_id: {"ai_high_trust": 0.9, "ai_mid_trust": 0.6, "ai_low_trust": 0.3}.get(ai_id, 0.1)

        caps_data = [
            {"capability_id":"c1", "ai_id":"ai_high_trust", "name":"CapAlpha", "tags":["nlp", "translation"]},
            {"capability_id":"c2", "ai_id":"ai_mid_trust", "name":"CapBeta", "tags":["image", "nlp"]},
            {"capability_id":"c3", "ai_id":"ai_low_trust", "name":"CapAlpha", "version":"2.0", "tags":["storage"]},
            {"capability_id":"c4", "ai_id":"ai_high_trust", "name":"CapGamma", "tags":["math"]},
        ]

        for data in caps_data:
            # Construct full payload ensuring all required fields are present
            payload = HSPCapabilityAdvertisementPayload(
                capability_id=data["capability_id"], ai_id=data["ai_id"], name=data["name"],
                description=data.get("description", "Test Desc"), version=data.get("version", "1.0"),
                availability_status=data.get("availability_status", "online"), # type: ignore
                tags=data.get("tags"), input_schema_uri=None, input_schema_example=None,
                output_schema_uri=None, output_schema_example=None, data_format_preferences=None,
                hsp_protocol_requirements=None, cost_estimate_template=None, access_policy_id=None
            )
            sdm.process_capability_advertisement(payload, payload['ai_id'], MagicMock(spec=HSPMessageEnvelope))
        return sdm

    def test_find_capabilities_no_filters(self, populated_sdm: ServiceDiscoveryModule):
        results = populated_sdm.find_capabilities()
        assert len(results) == 4

    def test_find_capabilities_by_id(self, populated_sdm: ServiceDiscoveryModule):
        results = populated_sdm.find_capabilities(capability_id_filter="c1")
        assert len(results) == 1
        assert results[0].get('capability_id') == "c1"

    def test_find_capabilities_by_name(self, populated_sdm: ServiceDiscoveryModule):
        results = populated_sdm.find_capabilities(capability_name_filter="CapAlpha")
        assert len(results) == 2
        assert {res.get('capability_id') for res in results} == {"c1", "c3"}

    def test_find_capabilities_by_tags(self, populated_sdm: ServiceDiscoveryModule):
        results_nlp = populated_sdm.find_capabilities(tags_filter=["nlp"])
        assert len(results_nlp) == 2
        assert {res.get('capability_id') for res in results_nlp} == {"c1", "c2"}

        results_nlp_translation = populated_sdm.find_capabilities(tags_filter=["nlp", "translation"])
        assert len(results_nlp_translation) == 1
        assert results_nlp_translation[0].get('capability_id') == "c1"

        results_non_existent_tag = populated_sdm.find_capabilities(tags_filter=["non_existent"])
        assert len(results_non_existent_tag) == 0

        results_mixed_tags = populated_sdm.find_capabilities(tags_filter=["nlp", "storage"])
        assert len(results_mixed_tags) == 0

    def test_find_capabilities_by_min_trust(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        results_min_trust_0_7 = populated_sdm.find_capabilities(min_trust_score=0.7)
        assert len(results_min_trust_0_7) == 2
        assert {res.get('capability_id') for res in results_min_trust_0_7} == {"c1", "c4"}

        results_min_trust_0_5 = populated_sdm.find_capabilities(min_trust_score=0.5)
        assert len(results_min_trust_0_5) == 3
        assert {res.get('capability_id') for res in results_min_trust_0_5} == {"c1", "c2", "c4"}

        results_min_trust_1_0 = populated_sdm.find_capabilities(min_trust_score=1.0)
        assert len(results_min_trust_1_0) == 0

    def test_find_capabilities_sort_by_trust(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        results = populated_sdm.find_capabilities(sort_by_trust=True)
        assert len(results) == 4

        trust_scores_ordered = [mock_trust_manager.get_trust_score(res.get('ai_id','')) for res in results] # type: ignore
        assert trust_scores_ordered == [0.9, 0.9, 0.6, 0.3]

        top_trust_ids = {results[0].get('capability_id'), results[1].get('capability_id')}
        assert top_trust_ids == {"c1", "c4"}
        assert results[2].get('capability_id') == "c2"
        assert results[3].get('capability_id') == "c3"

    def test_find_capabilities_combined_filters_and_sort(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        results = populated_sdm.find_capabilities(tags_filter=["nlp"], min_trust_score=0.5, sort_by_trust=True)
        assert len(results) == 2
        assert results[0].get('capability_id') == "c1"
        assert results[1].get('capability_id') == "c2"

    # TODO: Add tests for staleness once that logic is implemented
    # def test_find_capabilities_filters_stale_entries(self, populated_sdm_with_stale: ServiceDiscoveryModule):
    #     pass
    # def test_get_capability_by_id_returns_none_for_stale(self, populated_sdm_with_stale: ServiceDiscoveryModule):
    #     pass
