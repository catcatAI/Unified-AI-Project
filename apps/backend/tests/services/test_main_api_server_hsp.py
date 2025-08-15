import pytest
from fastapi.testclient import TestClient
import uuid
import time
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, ANY
from typing import List, Dict, Any

# Ensure src is in path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the FastAPI app and core services
from src.services.main_api_server import app # Main FastAPI app
from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID
from src.hsp.connector import HSPConnector
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.core_ai.dialogue.project_coordinator import ProjectCoordinator
from tests.conftest import mqtt_broker_available


import logging

# --- Constants for API Tests ---
TEST_API_PEER_AI_ID = "did:hsp:test_api_peer_007"
MQTT_BROKER_ADDRESS = "127.0.0.1" # Must match what core_services will use
MQTT_BROKER_PORT = 1883

# Set logging level for HSPConnector to DEBUG for detailed output during tests
logging.getLogger("src.hsp.connector").setLevel(logging.DEBUG)
logging.getLogger("src.core_ai.service_discovery.service_discovery_module").setLevel(logging.DEBUG)
logging.getLogger("src.core_ai.dialogue.dialogue_manager").setLevel(logging.DEBUG)

class MockSDM:
    def __init__(self):
        self._mock_sdm_capabilities_store = {}

    async def process_capability_advertisement(self, payload, sender_ai_id, envelope):
        try:
            print(f"DEBUG: Processing capability advertisement, payload type: {type(payload)}, payload: {payload}")
            if isinstance(payload, dict):
                if 'availability_status' not in payload:
                    raise ValueError(f"Missing required field: availability_status")
                processed_payload = HSPCapabilityAdvertisementPayload(**payload)
            elif isinstance(payload, HSPCapabilityAdvertisementPayload):
                processed_payload = payload
            else:
                logging.error(f"Invalid payload type: {type(payload)}")
                return
            capability_id = processed_payload['capability_id']
            self._mock_sdm_capabilities_store[capability_id] = (processed_payload, datetime.now(timezone.utc))
            print(f"DEBUG: Added capability {capability_id} to SDM store")
        except Exception as e:
            logging.error(f"Failed to process capability advertisement: {e}")
            print(f"DEBUG: Failed to process capability advertisement: {e}, payload: {payload}, payload type: {type(payload)}")
            import traceback
            traceback.print_exc()

    async def find_capabilities(self, capability_id_filter=None, capability_name_filter=None, tags_filter=None, min_trust_score=None, sort_by_trust=False):
        print(f"DEBUG find_capabilities: Looking for capability_id_filter='{capability_id_filter}'")
        print(f"DEBUG find_capabilities: Store keys: {list(self._mock_sdm_capabilities_store.keys())}")
        results = []
        for cap_id, (payload, last_seen) in self._mock_sdm_capabilities_store.items():
            print(f"DEBUG find_capabilities: Checking cap_id='{cap_id}' vs filter='{capability_id_filter}'")
            if capability_id_filter and cap_id != capability_id_filter:
                print(f"DEBUG find_capabilities: Skipping {cap_id} because it doesn't match filter {capability_id_filter}")
                continue
            payload_name = payload.get('name')
            if capability_name_filter and payload_name != capability_name_filter:
                print(f"DEBUG find_capabilities: Skipping {cap_id} because name doesn't match")
                continue
            payload_tags = payload.get('tags', [])
            if tags_filter and not all(tag in payload_tags for tag in tags_filter):
                print(f"DEBUG find_capabilities: Skipping {cap_id} because tags don't match")
                continue
            print(f"DEBUG find_capabilities: Adding {cap_id} to results")
            results.append(payload)
        print(f"DEBUG find_capabilities: Returning {len(results)} results")
        return results

    async def get_all_capabilities(self):
        results = []
        for cap_id, (payload, _) in self._mock_sdm_capabilities_store.items():
            results.append(payload)
        return results

class MockHAMMemoryManager:
    def __init__(self):
        self.memory_store = {}
        self._next_id = 1

    def store_experience(self, raw_data: str, data_type: str, metadata: Dict[str, Any]) -> str:
        mem_id = f"mem_{self._next_id:06d}"
        self._next_id += 1
        record_pkg = {
            "raw_data": raw_data,
            "data_type": data_type,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mem_id": mem_id
        }
        self.memory_store[mem_id] = record_pkg
        return mem_id

    def query_memory(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for mem_id, record_pkg in self.memory_store.items():
            match = True
            for key, value in query_params.items():
                if key == "hsp_correlation_id":
                    if record_pkg.get("metadata", {}).get("hsp_correlation_id") != value:
                        match = False
                        break
                # Add other query parameters as needed
            if match:
                results.append(record_pkg)
        return results


@pytest.fixture
async def api_test_peer_connector():
    """A separate HSPConnector for a mock peer to interact with the API's AI."""
    # Mock HSPConnector instead of using real one for tests
    peer_conn = AsyncMock(spec=HSPConnector)
    peer_conn.ai_id = TEST_API_PEER_AI_ID
    peer_conn.connect.return_value = True
    
    # Setup mock behaviors
    connect_event = asyncio.Event()
    connect_event.set()  # Immediately mark as connected
    disconnect_event = asyncio.Event()
    
    async def mock_publish(*args, **kwargs):
        return True
        
    async def mock_subscribe(*args, **kwargs):
        return True
        
    peer_conn.publish_capability_advertisement.side_effect = mock_publish
    peer_conn.subscribe.side_effect = mock_subscribe
    peer_conn.send_task_result.return_value = True # Mock send_task_result
    peer_conn._task_request_callbacks = [] # Store registered callbacks

    def mock_register_on_task_request_callback(callback):
        peer_conn._task_request_callbacks.append(callback)

    peer_conn.register_on_task_request_callback.side_effect = mock_register_on_task_request_callback

    async def mock_send_task_request(payload, recipient_ai_id, envelope):
        # Simulate the task request being received by the peer's registered callback
        for callback in peer_conn._task_request_callbacks:
            await callback(payload, recipient_ai_id, envelope) # Await the callback
        return True

    peer_conn.send_task_request.side_effect = mock_send_task_request

    yield peer_conn
    peer_conn.disconnect()

async def wait_for_event(event: asyncio.Event, timeout: float = 2.0):
    """Waits for an asyncio.Event to be set, with a timeout."""
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(f"Event was not set within the {timeout}s timeout.")

@pytest.mark.skipif(not mqtt_broker_available, reason="MQTT broker not available for API HSP tests")
class TestHSPEndpoints:

    @pytest.mark.timeout(10)
    async def test_list_hsp_services_empty(self, client_with_overrides):
        client, sdm, dm, ham, mock_hsp_connector = client_with_overrides

        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        assert response.json() == []
        sdm.get_all_capabilities.assert_called_once() # 修正 - 不能await MockAsyncMock的assert方法

    @pytest.mark.timeout(10)
    async def test_list_hsp_services_with_advertisements(self, client_with_overrides):
        client, sdm, dm, ham, mock_hsp_connector = client_with_overrides

        # Simulate a capability advertisement being processed
        mock_advertisement = HSPCapabilityAdvertisementPayload(
            capability_id="test_cap_id_123",
            name="Test Capability",
            description="A test capability for API endpoint",
            version="1.0",
            supported_interfaces=["hsp.chat"],
            ai_id="did:hsp:test_ai_1",
            timestamp=datetime.now(timezone.utc),
            metadata={"test_key": "test_value"},
            availability_status="online" # Added missing required field
        )
        sdm.process_capability_advertisement(mock_advertisement, "did:hsp:test_ai_1", MagicMock())

        # Verify that the capability is in the mock store before making the API call
        # The sdm.get_all_capabilities() should reflect the state after processing
        stored_capabilities = await sdm.get_all_capabilities()
        assert len(stored_capabilities) == 1
        assert stored_capabilities[0].capability_id == "test_cap_id_123"

        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["capability_id"] == "test_cap_id_123"
        assert data[0]["name"] == "Test Capability"

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_request_hsp_task_success(self, client_with_overrides, api_test_peer_connector):
        client, sdm, api_dm, ham, mock_hsp_connector = client_with_overrides
        peer_ai_id = "did:hsp:test_api_peer_007"
        mock_echo_cap_id = f"{peer_ai_id}_echo_for_api_v1"
        print(f"\nDEBUG: mock_echo_cap_id = '{mock_echo_cap_id}'")
        print(f"DEBUG: len(mock_echo_cap_id) = {len(mock_echo_cap_id)}")
        print(f"DEBUG: repr(mock_echo_cap_id) = {repr(mock_echo_cap_id)}")
        
        # Use the existing api_test_peer_connector fixture
        peer_conn = api_test_peer_connector
        
        # Create a capability advertisement with all required fields
        mock_cap_adv = HSPCapabilityAdvertisementPayload(
            capability_id=mock_echo_cap_id,
            ai_id=peer_ai_id,  # Required field
            agent_name="test_echo_agent",
            name="Echo capability for API test",  # Required field
            description="Echo capability for API test",  # Required field
            version="1.0",  # Required field
            availability_status="online",  # Required field
            tags=["echo", "test"],
        )
        
        # Process the capability advertisement directly
        print(f"\nProcessing capability advertisement: {mock_cap_adv}")
        try:
            sdm.process_capability_advertisement(mock_cap_adv, peer_ai_id, None)
            print(f"\nCapability advertisement processed successfully")
        except Exception as e:
            print(f"\nError processing capability advertisement: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Access the MockSDM instance through the side_effect
        mock_sdm_instance = sdm.process_capability_advertisement.side_effect.__self__
        print(f"\nSDM store after processing: {list(mock_sdm_instance._mock_sdm_capabilities_store.keys())}")
        
        # Debug: Print all capabilities in SDM
        all_caps = sdm.get_all_capabilities()
        cap_ids = []
        for cap in all_caps:
            if hasattr(cap, 'capability_id'):
                cap_ids.append(cap['capability_id'])
        print(f"\nAll capabilities in SDM: {cap_ids}")
        
        # Verify the capability is in SDM
        found_caps = await sdm.find_capabilities(capability_id_filter=mock_echo_cap_id)
        found_cap_ids = []
        for cap in found_caps:
            found_cap_ids.append(cap['capability_id'])
        print(f"\nFound capabilities with filter '{mock_echo_cap_id}': {found_cap_ids}")
        
        # If capability not found, print debug info before asserting
        if len(found_caps) == 0:
            print(f"\nCapability {mock_echo_cap_id} not found in SDM!")
            print(f"Available capabilities:")
            all_caps = await sdm.get_all_capabilities()
            for cap in all_caps:
                cap_id = cap['capability_id']
                cap_name = cap['name']
                print(f"  - {cap_id}: {cap_name}")
        
        assert len(found_caps) == 1, f"Capability {mock_echo_cap_id} not found in SDM"
        
        # Set up the peer to handle the task request
        task_request_received = asyncio.Event()
        task_request_payload = None
        
        async def api_peer_task_handler(payload, sender_ai_id, envelope):
            nonlocal task_request_payload
            task_request_payload = payload
            print(f"\nPeer received task request: {payload}")
            print(f"Capability ID filter: {payload.get('capability_id_filter', 'None')}")
            
            # Send back a success result directly using the callback
            result_payload = HSPTaskResultPayload(
                correlation_id=payload["correlation_id"],
                status="success",
                result={"message": f"Echo: {payload.get('parameters', {}).get('message', 'No message')}"},
            )
            
            # Call the registered callback directly
            if hasattr(mock_hsp_connector, '_registered_task_result_callback') and mock_hsp_connector._registered_task_result_callback:
                await mock_hsp_connector._registered_task_result_callback(result_payload, peer_ai_id, None)
            task_request_received.set()
        
        # Register the task handler
        peer_conn.register_on_task_request_callback(api_peer_task_handler)
        
        # Subscribe to the main API server's AI ID topic
        await peer_conn.subscribe(f"hsp/{mock_hsp_connector.ai_id}/task_request/#")
        
        # Make the API request
        mock_corr_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/hsp/tasks",
            json={
                "target_capability_id": mock_echo_cap_id,
                "parameters": {"message": "Hello from API test"},
            },
        )
        
        # Debug: Print API response
        print(f"\nAPI response: {response.status_code} {response.json()}")
        
        # Debug: Print API response
        print(f"\nAPI response: {response.status_code} {response.json()}")
        
        if response.status_code != 200:
            print(f"\nAPI request failed with status {response.status_code}")
            print(f"Response content: {response.text}")
            request_payload = {
                'target_capability_id': mock_echo_cap_id,
                'parameters': {'message': 'Hello from API test'}
            }
            print(f"Request payload: {request_payload}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Check if the capability was found
        if "not found" in response_data.get("status_message", ""):
            print(f"\nCapability not found. Available capabilities:")
            available_caps = sdm.get_all_capabilities()
            for cap in available_caps:
                cap_id = cap.capability_id if hasattr(cap, 'capability_id') else cap.get('capability_id', 'Unknown ID')
                cap_name = cap.name if hasattr(cap, 'name') else cap.get('name', 'Unknown Name')
                print(f"  - {cap_id}: {cap_name}")
            print(f"\nLooking for: {mock_echo_cap_id}")
            assert False, f"Capability {mock_echo_cap_id} not found in SDM"
        
        assert response_data["correlation_id"] is not None
        actual_correlation_id = response_data["correlation_id"]
        
        # Wait for the task to be handled
        try:
            await asyncio.wait_for(task_request_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            assert False, "Timeout waiting for task request to be handled"
        
        # Verify the task request was received by the peer
        assert task_request_payload is not None
        assert task_request_payload["correlation_id"] == actual_correlation_id
        
        # Verify the task was removed from pending requests
        assert actual_correlation_id not in api_dm._pending_hsp_task_requests
        
        # Clean up
        await peer_conn.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_request_hsp_task_capability_not_found(self, client_with_overrides):
        client, sdm, dm, ham, mock_hsp_connector = client_with_overrides
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

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_get_hsp_task_status_pending(self, client_with_overrides, api_test_peer_connector): # Added api_test_peer_connector fixture
        client, sdm, dialogue_manager, ham, mock_hsp_connector = client_with_overrides

        # Simulate a task request that remains pending
        mock_corr_id = "pending_corr_id_123"
        # Instead of setting return_value on a non-existent attribute,
        # we ensure the mock_hsp_connector's register_on_task_request_callback
        # is properly set up to capture the callback.
        # The client_with_overrides fixture already sets up mock_hsp_connector
        # with a side_effect for register_on_task_request_callback.
        # We just need to ensure the DM registers its callback.

        # Trigger a task request from the API, which will cause the DM to register
        # a callback with the mock_hsp_connector.
        # We need to ensure the mock_hsp_connector's send_task_request is mocked
        # to simulate the task being sent and then the result being received.

        # The `client_with_overrides` fixture already sets up `mock_hsp_connector`
        # with a `register_on_task_request_callback` side effect that captures the callback.
        # We need to ensure that the `DialogueManager` (dm) registers its callback.
        # This happens during the `initialize_services` call within the FastAPI lifespan.

        # To simulate a pending task, we need to prevent the peer from immediately responding.
        # We can temporarily disable the peer's task handling for this specific test.
        # Access the fixture's return value directly
        peer_conn_obj = api_test_peer_connector
        original_peer_task_handler_side_effect = peer_conn_obj.send_task_request.side_effect
        peer_conn_obj.send_task_request.side_effect = AsyncMock(return_value=True) # Prevent peer from responding

        # Make an initial request to trigger the pending state
        response = client.post("/api/v1/hsp/tasks", json={
            "target_capability_id": "test_cap_pending",
            "parameters": {"data": "test"}
        })
        assert response.status_code == 200
        initial_response_data = response.json()
        assert initial_response_data["status_message"] == "HSP Task request sent successfully."
        assert initial_response_data["correlation_id"] is not None

        # Restore the original side_effect for other tests
        peer_conn_obj.send_task_request.side_effect = original_peer_task_handler_side_effect

        # Now check the status of the pending task
        response = client.get(f"/api/v1/hsp/tasks/{initial_response_data['correlation_id']}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == initial_response_data['correlation_id']
        assert status_data["status"] == "pending"
        assert "pending" in status_data["message"].lower() #type: ignore
        assert response.status_code == 200
        initial_response_data = response.json()
        assert initial_response_data["status"] == "pending"
        assert initial_response_data["correlation_id"] is not None

        # Restore the original side_effect for other tests
        api_test_peer_connector.send_task_request.side_effect = original_peer_task_handler

        # Now check the status of the pending task
        response = client.get(f"/api/v1/hsp/tasks/{initial_response_data['correlation_id']}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == initial_response_data['correlation_id']
        assert status_data["status"] == "pending"
        assert "pending" in status_data["message"].lower() #type: ignore

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_get_hsp_task_status_completed_from_ham(self, client_with_overrides):
        client, sdm, dm, ham_manager, mock_hsp_connector = client_with_overrides

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
        await asyncio.sleep(0.1) # Give time for HAM to process
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "completed", f"Expected status 'completed', but got {status_data['status']}"
        assert status_data["result_payload"] == expected_result_payload # Now API should return this
        assert status_data["message"] == "Task completed successfully."

        if hasattr(ham_manager, "memory_store"):
             ham_manager.memory_store = {k:v for k,v in ham_manager.memory_store.items() if v['metadata'].get('hsp_correlation_id') != mock_corr_id}


    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_get_hsp_task_status_failed_from_ham(self, client_with_overrides):
        client, sdm, dm, ham_manager, mock_hsp_connector = client_with_overrides

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
        await asyncio.sleep(0.1) # Give time for HAM to process
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "failed", f"Expected status 'failed', but got {status_data['status']}"
        assert status_data["error_details"] == expected_error_details
        if hasattr(ham_manager, "memory_store"):
             ham_manager.memory_store = {k:v for k,v in ham_manager.memory_store.items() if v['metadata'].get('hsp_correlation_id') != mock_corr_id}


    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_get_hsp_task_status_unknown(self, client_with_overrides):
        client, sdm, dm, ham, mock_hsp_connector = client_with_overrides
        mock_corr_id = "unknown_corr_id_000"
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "unknown_or_expired"
