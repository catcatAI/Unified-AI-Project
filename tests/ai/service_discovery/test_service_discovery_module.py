import pytest
from unittest.mock import MagicMock, AsyncMock
from ai.service_discovery.service_discovery_module import ServiceDiscoveryModule


@pytest.fixture
def trust_mock():
    tm = MagicMock()
    tm.get_trust_score.return_value = 0.8
    return tm


@pytest.fixture
def sdm(trust_mock):
    return ServiceDiscoveryModule(trust_mock, staleness_threshold_seconds=3600)


def test_sdm_init(sdm):
    assert sdm.known_capabilities == {}
    assert sdm.staleness_threshold_seconds == 3600


def test_sdm_process_advertisement(sdm):
    payload = {
        "capability_id": "cap_001",
        "ai_id": "ai_001",
        "name": "test_capability",
        "description": "A test capability",
        "version": "1.0",
        "availability_status": "online",
        "tags": ["test"],
    }
    envelope = {"hsp_envelope_version": "1.0", "message_id": "msg_001", "correlation_id": None, "sender_ai_id": "ai_001", "recipient_ai_id": "ai_002", "timestamp_sent": "2025-01-01T00:00:00Z", "message_type": "HSP::CapabilityAdvertisement", "protocol_version": "1.0", "communication_pattern": "unicast", "security_parameters": None, "qos_parameters": None, "routing_info": None, "payload_schema_uri": None, "payload": payload}
    sdm.process_capability_advertisement(payload, "ai_001", envelope)
    assert "cap_001" in sdm.known_capabilities


def test_sdm_process_advertisement_no_id(sdm):
    payload = {"name": "test", "ai_id": "ai_001", "description": "test", "version": "1.0", "availability_status": "online"}
    envelope = {"hsp_envelope_version": "1.0", "message_id": "msg_002", "correlation_id": None, "sender_ai_id": "ai_001", "recipient_ai_id": "ai_002", "timestamp_sent": "2025-01-01T00:00:00Z", "message_type": "HSP::CapabilityAdvertisement", "protocol_version": "1.0", "communication_pattern": "unicast", "security_parameters": None, "qos_parameters": None, "routing_info": None, "payload_schema_uri": None, "payload": payload}
    sdm.process_capability_advertisement(payload, "ai_001", envelope)
    assert sdm.known_capabilities == {}


def test_sdm_get_capability_nonexistent(sdm):
    result = sdm.get_capability_by_id("nonexistent")
    assert result is None


def test_sdm_is_capability_available_false(sdm):
    assert sdm.is_capability_available("nonexistent") is False


def test_sdm_get_all_capabilities_empty(sdm):
    assert sdm.get_all_capabilities() == []
async def test_sdm_find_capabilities_empty(sdm):
    results = await sdm.find_capabilities()
    assert results == []
async def test_sdm_get_all_capabilities_async_empty(sdm):
    results = await sdm.get_all_capabilities_async()
    assert results == []


def test_sdm_remove_stale_capabilities_empty(sdm):
    sdm.remove_stale_capabilities()
    assert sdm.known_capabilities == {}