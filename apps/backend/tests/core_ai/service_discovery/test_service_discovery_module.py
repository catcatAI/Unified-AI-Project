import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta # Ensure timedelta is imported
import logging # For caplog if needed, or to check logs from module

import time

from apps.backend.src.ai.discovery.service_discovery_module import ServiceDiscoveryModule
from apps.backend.src.ai.trust.trust_manager_module import TrustManager
from apps.backend.src.core.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope

# --- Mock TrustManager ---
@pytest.fixture
def mock_trust_manager():
    mock_tm = MagicMock(spec=TrustManager)
    # Default behavior: always return a neutral trust score
    mock_tm.get_trust_score.return_value = 0.5
    return mock_tm

# --- Test ServiceDiscoveryModule ---
class TestServiceDiscoveryModule:
    @pytest.mark.timeout(10)
    def test_init(self, mock_trust_manager: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.core_ai.service_discovery.service_discovery_module")
        # Test with default staleness threshold
        sdm_default = ServiceDiscoveryModule(trust_manager=mock_trust_manager)
        assert sdm_default.trust_manager == mock_trust_manager
        assert sdm_default.known_capabilities == {}
        assert sdm_default.lock is not None
        assert sdm_default.staleness_threshold_seconds == ServiceDiscoveryModule.DEFAULT_STALENESS_THRESHOLD_SECONDS
        assert f"Staleness threshold: {ServiceDiscoveryModule.DEFAULT_STALENESS_THRESHOLD_SECONDS} seconds" in caplog.text

        caplog.clear()
        # Test with custom staleness threshold
        custom_threshold = 30
        sdm_custom = ServiceDiscoveryModule(trust_manager=mock_trust_manager, staleness_threshold_seconds=custom_threshold)
        assert sdm_custom.staleness_threshold_seconds == custom_threshold
        assert f"Staleness threshold: {custom_threshold} seconds" in caplog.text

    @pytest.mark.timeout(10)
    def test_process_capability_advertisement_new_and_update(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)

        cap_id_1 = "cap_test_001"
        # Provide all required fields for HSPCapabilityAdvertisementPayload based on its TypedDict definition
        payload1 = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id_1, ai_id="ai1", agent_name="test_agent", name="TestCap1", description="Desc1",
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
        # Since payload1 is a TypedDict, we need to compare the values directly
        assert stored_payload1['capability_id'] == payload1['capability_id']
        assert stored_payload1['ai_id'] == payload1['ai_id']
        assert stored_payload1['name'] == payload1['name']
        assert stored_payload1['description'] == payload1['description']
        assert stored_payload1['version'] == payload1['version']
        assert stored_payload1['availability_status'] == payload1['availability_status']
        assert stored_payload1['tags'] == payload1['tags']
        assert time_before_add <= stored_time1 <= time_after_add

        # Test update
        sdm.known_capabilities[cap_id_1] = (stored_payload1, time_before_add - timedelta(seconds=1))
        payload1_updated = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id_1, ai_id="ai1", agent_name="test_agent", name="TestCap1_Updated", description="Desc1_Updated",
            version="1.1", availability_status="online", tags=["t1", "t3"],
            input_schema_uri=None, input_schema_example=None,
            output_schema_uri=None, output_schema_example=None,
            data_format_preferences=None, hsp_protocol_requirements=None,
            cost_estimate_template=None, access_policy_id=None
        )
        # Add a small sleep to ensure timestamp changes for the update
        time.sleep(0.001) 
        time_before_update = datetime.now(timezone.utc)
        sdm.process_capability_advertisement(payload1_updated, "sender_ai_id_1", mock_envelope)
        time_after_update = datetime.now(timezone.utc)

        assert cap_id_1 in sdm.known_capabilities
        stored_payload1_upd, stored_time1_upd = sdm.known_capabilities[cap_id_1]
        # Since payload1_updated is a TypedDict, we need to compare the values directly
        assert stored_payload1_upd['capability_id'] == payload1_updated['capability_id']
        assert stored_payload1_upd['ai_id'] == payload1_updated['ai_id']
        assert stored_payload1_upd['name'] == payload1_updated['name']
        assert stored_payload1_upd['description'] == payload1_updated['description']
        assert stored_payload1_upd['version'] == payload1_updated['version']
        assert stored_payload1_upd['availability_status'] == payload1_updated['availability_status']
        assert stored_payload1_upd['tags'] == payload1_updated['tags']
        assert time_before_update <= stored_time1_upd <= time_after_update
        assert stored_time1_upd > stored_time1 # Ensure timestamp was updated

    @pytest.mark.timeout(10)
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

    @pytest.mark.timeout(10)
    def test_get_capability_by_id(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)
        cap_id = "get_cap_001"
        payload = HSPCapabilityAdvertisementPayload(
            capability_id=cap_id, ai_id="ai_get", agent_name="test_agent", name="GetCap", description="d", version="v",
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
                capability_id=data["capability_id"], ai_id=data["ai_id"], agent_name="test_agent", name=data["name"],
                description=data.get("description", "Test Desc"), version=data.get("version", "1.0"),
                availability_status=data.get("availability_status", "online"), # type: ignore
                tags=data.get("tags"), input_schema_uri=None, input_schema_example=None,
                output_schema_uri=None, output_schema_example=None, data_format_preferences=None,
                hsp_protocol_requirements=None, cost_estimate_template=None, access_policy_id=None
            )
            sdm.process_capability_advertisement(payload, payload['ai_id'], MagicMock(spec=HSPMessageEnvelope))
        return sdm

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_no_filters(self, populated_sdm: ServiceDiscoveryModule):
        results = await populated_sdm.find_capabilities()
        assert len(results) == 4

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_by_id(self, populated_sdm: ServiceDiscoveryModule):
        results = await populated_sdm.find_capabilities(capability_id_filter="c1")
        assert len(results) == 1
        assert results[0].get('capability_id') == "c1"

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_by_name(self, populated_sdm: ServiceDiscoveryModule):
        results = await populated_sdm.find_capabilities(capability_name_filter="CapAlpha")
        assert len(results) == 2
        assert {res.get('capability_id') for res in results} == {"c1", "c3"}

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_by_tags(self, populated_sdm: ServiceDiscoveryModule):
        results_nlp = await populated_sdm.find_capabilities(tags_filter=["nlp"])
        assert len(results_nlp) == 2
        assert {res.get('capability_id') for res in results_nlp} == {"c1", "c2"}

        results_nlp_translation = await populated_sdm.find_capabilities(tags_filter=["nlp", "translation"])
        assert len(results_nlp_translation) == 1
        assert results_nlp_translation[0].get('capability_id') == "c1"

        results_non_existent_tag = await populated_sdm.find_capabilities(tags_filter=["non_existent"])
        assert len(results_non_existent_tag) == 0

        results_mixed_tags = await populated_sdm.find_capabilities(tags_filter=["nlp", "storage"])
        assert len(results_mixed_tags) == 0

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_by_min_trust(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        results_min_trust_0_7 = await populated_sdm.find_capabilities(min_trust_score=0.7)
        # Only ai_high_trust (0.9) should qualify
        assert len(results_min_trust_0_7) == 2
        assert all(res.get('ai_id') == "ai_high_trust" for res in results_min_trust_0_7)

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_sort_by_trust(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        results = await populated_sdm.find_capabilities(sort_by_trust=True)
        assert len(results) == 4
        # Should be sorted by trust score descending: high (0.9), mid (0.6), low (0.3)
        # ai_high_trust entries should come first
        high_trust_results = [r for r in results if r.get('ai_id') == "ai_high_trust"]
        mid_trust_results = [r for r in results if r.get('ai_id') == "ai_mid_trust"]
        low_trust_results = [r for r in results if r.get('ai_id') == "ai_low_trust"]
        
        # Check that high trust results come first
        first_high_index = next(i for i, r in enumerate(results) if r.get('ai_id') == "ai_high_trust")
        last_high_index = next(len(results) - 1 - i for i, r in enumerate(reversed(results)) if r.get('ai_id') == "ai_high_trust")
        first_mid_index = next(i for i, r in enumerate(results) if r.get('ai_id') == "ai_mid_trust")
        first_low_index = next(i for i, r in enumerate(results) if r.get('ai_id') == "ai_low_trust")
        
        assert first_high_index < first_mid_index < first_low_index

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_find_capabilities_combined_filters_and_sort(self, populated_sdm: ServiceDiscoveryModule, mock_trust_manager: MagicMock):
        # Find capabilities with name "CapAlpha" AND min trust 0.5, sorted by trust
        results = await populated_sdm.find_capabilities(
            capability_name_filter="CapAlpha",
            min_trust_score=0.5,
            sort_by_trust=True
        )
        # Should find c1 (high trust 0.9) and c3 (low trust 0.3), but c3 should be filtered out by min_trust
        # Actually, c3 has ai_low_trust (0.3) which is below 0.5, so only c1 should be returned
        assert len(results) == 1
        assert results[0].get('capability_id') == "c1"
        assert results[0].get('ai_id') == "ai_high_trust"

    @pytest.mark.timeout(10)
    def test_staleness_checks(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager, staleness_threshold_seconds=1)  # 1 second for test
        payload = HSPCapabilityAdvertisementPayload(
            capability_id="stale_test", ai_id="ai_stale", agent_name="test_agent", name="StaleTest", description="d",
            version="v", availability_status="online"
        )
        sdm.process_capability_advertisement(payload, "sender", MagicMock(spec=HSPMessageEnvelope))
        
        assert "stale_test" in sdm.known_capabilities
        
        # Wait for it to become stale
        time.sleep(1.1)
        
        # find_capabilities should filter out stale entries
        results = sdm._find_capabilities_sync()
        assert len(results) == 0
        assert "stale_test" not in [r.get('capability_id') for r in results]

    @pytest.mark.timeout(10)
    def test_get_capability_by_id_staleness_direct_variant(self, mock_trust_manager: MagicMock):
        sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager, staleness_threshold_seconds=1)
        payload = HSPCapabilityAdvertisementPayload(
            capability_id="stale_direct", ai_id="ai_stale", agent_name="test_agent", name="StaleDirect", description="d",
            version="v", availability_status="online"
        )
        sdm.process_capability_advertisement(payload, "sender", MagicMock(spec=HSPMessageEnvelope))
        
        # Wait for it to become stale
        time.sleep(1.1)
        
        # Direct lookup should also respect staleness
        result = sdm.get_capability_by_id("stale_direct")
        assert result is None

    @pytest.mark.timeout(10)
    def test_get_all_capabilities(self, populated_sdm: ServiceDiscoveryModule):
        """Test the get_all_capabilities method"""
        # get_all_capabilities should return all non-stale capabilities
        results = populated_sdm.get_all_capabilities()
        assert len(results) == 4
        # Check that all expected capabilities are present
        capability_ids = {r.get('capability_id') for r in results}
        assert capability_ids == {"c1", "c2", "c3", "c4"}

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_get_all_capabilities_async(self, populated_sdm: ServiceDiscoveryModule):
        """Test the async version of get_all_capabilities"""
        # get_all_capabilities_async should return all non-stale capabilities
        results = await populated_sdm.get_all_capabilities_async()
        assert len(results) == 4
        # Check that all expected capabilities are present
        capability_ids = {r.get('capability_id') for r in results}
        assert capability_ids == {"c1", "c2", "c3", "c4"}

# Path for patching datetime.now within the module under test
DATETIME_NOW_PATCH_PATH = "src.core_ai.service_discovery.service_discovery_module.datetime"