import pytest
from apps.backend.src.core_ai.trust.trust_manager_module import TrustManager
from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope

# --- Mock TrustManager ---
@pytest.fixture
def mock_trust_manager():
    mock_tm = MagicMock(spec=TrustManager)
    mock_tm.get_trust_score.return_value = 0.5
    return mock_tm

# --- Fixture for populated_sdm ---:
pytest.fixture
def populated_sdm(mock_trust_manager: MagicMock):
    sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager)

    mock_trust_manager.get_trust_score.side_effect = lambda ai_id: {"ai_high_trust": 0.9, "ai_mid_trust": 0.6, "ai_low_trust": 0.3}.get(ai_id, 0.1)

    caps_data = [
        {"capability_id":"c1", "ai_id":"ai_high_trust", "name":"CapAlpha", "tags":["nlp", "translation"]},
        {"capability_id":"c2", "ai_id":"ai_mid_trust", "name":"CapBeta", "tags":["image", "nlp"]},
        {"capability_id":"c3", "ai_id":"ai_low_trust", "name":"CapAlpha", "version":"2.0", "tags":["storage"]},
        {"capability_id":"c4", "ai_id":"ai_high_trust", "name":"CapGamma", "tags":["math"]},
    ]

    for data in caps_data:
        payload = HSPCapabilityAdvertisementPayload(
#             capability_id=data["capability_id"], ai_id=data["ai_id"], name=data["name"],
#             description=data.get("description", "Test Desc"), version=data.get("version", "1.0"),
#             availability_status=data.get("availability_status", "online"),
#             tags=data.get("tags"), input_schema_uri=None, input_schema_example=None,
#             output_schema_uri=None, output_schema_example=None, data_format_preferences=None,
#             hsp_protocol_requirements=None, cost_estimate_template=None, access_policy_id=None
        )
        sdm.process_capability_advertisement(payload, payload['ai_id'], MagicMock(spec=HSPMessageEnvelope))
    return sdm

# --- Problematic test ---
@pytest.mark.asyncio
async def test_find_capabilities_no_filters(populated_sdm: ServiceDiscoveryModule) -> None:
    results = await populated_sdm.find_capabilities()
    assert len(results) == 4