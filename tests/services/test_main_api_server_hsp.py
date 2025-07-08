import pytest
from fastapi.testclient import TestClient
import uuid
import time
from unittest.mock import MagicMock, ANY

# Ensure src is in path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the FastAPI app and core services
from src.services.main_api_server import app # Main FastAPI app
from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID
from src.hsp.connector import HSPConnector
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.dialogue.dialogue_manager import DialogueManager

# --- Constants for API Tests ---
TEST_API_PEER_AI_ID = "did:hsp:test_api_peer_007"
MQTT_BROKER_ADDRESS = "localhost" # Must match what core_services will use
MQTT_BROKER_PORT = 1883

@pytest.fixture(scope="module")
def client():
    """
    Provides a TestClient for the FastAPI app.
    Manages service initialization and shutdown for the test module.
    """
    # Initialize services before creating TestClient
    # API server's lifespan will call initialize_services with its own AI ID.
    # For testing, we might want to control this more directly or ensure mocks are in place.
    # The lifespan will run. We can use it as is.

    with TestClient(app) as test_client:
        # Ensure services are up, especially the HSP connector for the main API's AI instance
        # The lifespan should have initialized services. Let's give it a moment.
        time.sleep(1.0) # Allow time for lifespan startup and MQTT connection
        services = get_services()
        assert services.get("hsp_connector") is not None, "HSPConnector not initialized in API for tests"
        if services.get("hsp_connector"):
             assert services.get("hsp_connector").is_connected, "API HSPConnector failed to connect for tests"
        yield test_client
    # Lifespan's shutdown part will call shutdown_services


@pytest.fixture
def api_test_peer_connector():
    """A separate HSPConnector for a mock peer to interact with the API's AI."""
    peer_conn = HSPConnector(TEST_API_PEER_AI_ID, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix=f"api_test_peer_{uuid.uuid4().hex[:4]}")
    if not peer_conn.connect():
        pytest.fail("Failed to connect api_test_peer_connector for API tests.")
    time.sleep(0.5)
    yield peer_conn
    peer_conn.disconnect()
    time.sleep(0.1)

class TestHSPEndpoints:

    def test_list_hsp_services_empty(self, client: TestClient):
        # Clear any existing services from ServiceDiscoveryModule first for a clean test
        services = get_services()
        sdm = services.get("service_discovery")
        if sdm:
            for cap in sdm.get_all_capabilities(): # type: ignore
                sdm.remove_capability(cap["capability_id"]) # type: ignore

        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_hsp_services_with_advertisements(self, client: TestClient, api_test_peer_connector: HSPConnector, service_discovery_module_fixture: ServiceDiscoveryModule):
        # service_discovery_module_fixture is from the other test file, might cause issues if not careful with scope.
        # For this test, we want the API's own ServiceDiscoveryModule instance.
        api_sdm = get_services().get("service_discovery")
        assert api_sdm is not None, "ServiceDiscoveryModule not found in API services"

        # Clear any existing capabilities first
        current_caps = api_sdm.get_all_capabilities() # type: ignore
        for cap_to_clear in current_caps:
             api_sdm.remove_capability(cap_to_clear["capability_id"]) # type: ignore


        adv_payload = HSPCapabilityAdvertisementPayload(
            capability_id=f"{TEST_API_PEER_AI_ID}_test_cap_1", ai_id=TEST_API_PEER_AI_ID,
            name="API Test Capability", description="A capability for API testing.",
            version="1.0", availability_status="online", tags=["test", "api"] #type: ignore
        )
        # Peer advertises a capability
        adv_topic = "hsp/capabilities/advertisements/general" # As subscribed by core_services init
        assert api_test_peer_connector.publish_capability_advertisement(adv_payload, adv_topic)
        time.sleep(0.5) # Allow time for MQTT message to arrive and be processed by API's SDM

        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        capabilities = response.json()
        assert len(capabilities) >= 1

        found_it = False
        for cap in capabilities:
            if cap.get("capability_id") == adv_payload["capability_id"]:
                assert cap.get("name") == adv_payload["name"]
                assert cap.get("ai_id") == TEST_API_PEER_AI_ID # Corrected constant
                found_it = True
                break
        assert found_it, "Advertised capability not found in API response."

    def test_request_hsp_task_success(self, client: TestClient, api_test_peer_connector: HSPConnector): # Removed dialogue_manager_fixture as we get it from API context
        # We need the DialogueManager from the API's context, not the test_hsp_integration's one
        api_dm = get_services().get("dialogue_manager")
        assert api_dm is not None

        # 1. Peer advertises a capability that the API's DM can request
        peer_ai_id = TEST_API_PEER_AI_ID
        mock_echo_cap_id = f"{peer_ai_id}_echo_for_api_v1"
        adv_payload = HSPCapabilityAdvertisementPayload( #type: ignore
            capability_id=mock_echo_cap_id, ai_id=peer_ai_id, name="API Echo Service",
            description="Echoes for API tests", version="1.0", availability_status="online", tags=["echo"]
        )
        assert api_test_peer_connector.publish_capability_advertisement(adv_payload, CAP_ADVERTISEMENT_TOPIC)
        time.sleep(0.5) # Allow SDM to process

        # 2. Setup peer to handle the task request for this capability
        received_task_requests_on_peer: List[HSPTaskRequestPayload] = []
        def api_peer_task_handler(payload: HSPTaskRequestPayload, sender: str, envelope: HSPMessageEnvelope):
            if payload.get("capability_id_filter") == mock_echo_cap_id:
                received_task_requests_on_peer.append(payload)
                result = HSPTaskResultPayload( #type: ignore
                    result_id=f"res_{uuid.uuid4().hex[:4]}", request_id=payload['request_id'],
                    executing_ai_id=peer_ai_id, status="success",
                    payload={"echoed": payload.get("parameters")},
                    timestamp_completed=datetime.now(timezone.utc).isoformat()
                )
                # Ensure callback_address and correlation_id are present
                cb_addr = payload.get('callback_address')
                corr_id = envelope.get('correlation_id')
                if cb_addr and corr_id:
                    api_test_peer_connector.send_task_result(result, cb_addr, corr_id)

        api_test_peer_connector.register_on_task_request_callback(api_peer_task_handler)
        peer_req_topic = f"hsp/requests/{peer_ai_id}/#" # Topic where peer listens for its tasks
        assert api_test_peer_connector.subscribe(peer_req_topic)
        time.sleep(0.2)

        # 3. Make API request to trigger the HSP task
        task_params = {"data": "hello from API test"}
        response = client.post("/api/v1/hsp/tasks", json={
            "target_capability_id": mock_echo_cap_id,
            "parameters": task_params
        })
        assert response.status_code == 200
        response_data = response.json()
        assert "Request sent successfully" in response_data.get("status_message", "")
        assert response_data.get("correlation_id") is not None
        correlation_id_from_api = response_data["correlation_id"]

        time.sleep(1.0) # Allow for full HSP round trip

        # 4. Assertions
        #    - Peer received the task request
        assert len(received_task_requests_on_peer) == 1
        assert received_task_requests_on_peer[0].get("parameters") == task_params

        #    - API's DialogueManager handled the result (check pending_hsp_task_requests)
        #      The result is handled asynchronously. The API call returns before result is back.
        #      The pending request should be removed after result is handled.
        assert correlation_id_from_api not in api_dm.pending_hsp_task_requests # type: ignore

    def test_request_hsp_task_capability_not_found(self, client: TestClient):
        response = client.post("/api/v1/hsp/tasks", json={
            "target_capability_id": "non_existent_capability_for_api",
            "parameters": {"data": "test"}
        })
        assert response.status_code == 200 # The API endpoint itself worked
        response_data = response.json()
        assert "Error: Capability ID" in response_data.get("status_message", "")
        assert "not found" in response_data.get("status_message", "")
        assert response_data.get("correlation_id") is None
        assert response_data.get("error") == "Capability not discovered."

    def test_get_hsp_task_status_pending(self, client: TestClient):
        services = get_services()
        dialogue_manager = services.get("dialogue_manager")
        assert dialogue_manager is not None

        mock_corr_id = "pending_corr_id_123"
        dialogue_manager.pending_hsp_task_requests[mock_corr_id] = { #type: ignore
            "capability_id": "test_cap_pending", "target_ai_id": "test_target_pending"
        }

        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "pending"
        assert "pending" in status_data["message"].lower() #type: ignore

        del dialogue_manager.pending_hsp_task_requests[mock_corr_id] # Clean up

    def test_get_hsp_task_status_completed_from_ham(self, client: TestClient):
        services = get_services()
        ham_manager = services.get("ham_manager")
        assert ham_manager is not None

        mock_corr_id = "completed_corr_id_456"
        expected_result_payload = {"data": "task was successful"}
        # Simulate storing a success result in HAM by DialogueManager's _handle_incoming_hsp_task_result
        # This metadata structure needs to align with what _handle_incoming_hsp_task_result actually stores.
        # Crucially, it needs "hsp_correlation_id" and the actual result payload.
        # The current DM stores the user-facing message in raw_data.
        # The API endpoint currently returns a generic success message if type is success.
        # DM's _handle_incoming_hsp_task_result now stores "hsp_task_service_payload" in metadata.

        ham_manager.store_experience(
            raw_data="User-facing success message including " + str(expected_result_payload), # Raw data is the user message
            data_type="ai_dialogue_text_hsp_result_success",
            metadata={
                "hsp_correlation_id": mock_corr_id,
                "source": "hsp_task_result_success",
                "hsp_task_service_payload": expected_result_payload # Simulate DM storing this
            } #type: ignore
        )

        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "completed"
        assert status_data["result_payload"] == expected_result_payload # Now API should return this
        assert status_data["message"] == "Task completed successfully."

        if hasattr(ham_manager, "memory_store"):
             ham_manager.memory_store = {k:v for k,v in ham_manager.memory_store.items() if v['metadata'].get('hsp_correlation_id') != mock_corr_id}


    def test_get_hsp_task_status_failed_from_ham(self, client: TestClient):
        services = get_services()
        ham_manager = services.get("ham_manager")
        assert ham_manager is not None

        mock_corr_id = "failed_corr_id_789"
        expected_error_details = {"error_code": "TEST_FAIL", "error_message": "Task failed for test"}

        ham_manager.store_experience( #type: ignore
            raw_data="User-facing failure message",
            data_type="ai_dialogue_text_hsp_error", # Matches what DM stores
            metadata={
                "hsp_correlation_id": mock_corr_id,
                "source": "hsp_task_result_error",
                "error_details": expected_error_details
            }
        )
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "failed"
        assert status_data["error_details"] == expected_error_details
        if hasattr(ham_manager, "memory_store"):
             ham_manager.memory_store = {k:v for k,v in ham_manager.memory_store.items() if v['metadata'].get('hsp_correlation_id') != mock_corr_id}


    def test_get_hsp_task_status_unknown(self, client: TestClient):
        mock_corr_id = "unknown_corr_id_000"
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "unknown_or_expired"
