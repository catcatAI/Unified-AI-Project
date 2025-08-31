import pytest
from fastapi.testclient import TestClient
import uuid
import time
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, ANY
from typing import List, Dict, Any, Optional

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
# Avoid importing fixtures at module import time; use a simple flag instead
# If a real broker check is needed, replace this with an actual availability check
mqtt_broker_available = True


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
            # Remove the isinstance check for TypedDict as it's not supported
            # Instead, we'll assume that if it's not a dict, it's already the correct type
            # In practice, TypedDict is just a dict at runtime
            else:
                processed_payload = payload
            # 使用 get 方法安全访问 capability_id，提供默认值以防键不存在
            capability_id = processed_payload.get('capability_id')
            if capability_id is None:
                logging.error("Missing required field: capability_id")
                return
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

    def query_core_memory(self, metadata_filters: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, Any]]:
        if not metadata_filters:
            return []
        results = []
        for mem_id, record_pkg in self.memory_store.items():
            match = True
            for key, value in metadata_filters.items():
                if key == "hsp_correlation_id":
                    if record_pkg.get("metadata", {}).get("hsp_correlation_id") != value:
                        match = False
                        break
                # Add other query parameters as needed
            if match:
                # 返回与实际HAM内存管理器相同格式的数据
                results.append({
                    "id": mem_id,
                    "timestamp": record_pkg.get("timestamp", ""),
                    "data_type": record_pkg.get("data_type", ""),
                    "rehydrated_gist": record_pkg.get("raw_data", ""),
                    "metadata": record_pkg.get("metadata", {})
                })
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
        
    peer_conn.publish_capability_advertisement.side_effect = mock_publish
    peer_conn.subscribe.side_effect = mock_publish
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

    try:
        yield peer_conn
    finally:
        # Disconnect may be async on the mock; if so, await it to avoid warnings
        maybe_disc = peer_conn.disconnect()
        if hasattr(maybe_disc, '__await__'):
            await maybe_disc

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

        # Mock both get_all_capabilities and get_all_capabilities_async methods
        # The API endpoint checks for get_all_capabilities_async first
        # Since sdm is already an AsyncMock, we need to ensure both methods are properly mocked
        sdm.get_all_capabilities_async = AsyncMock(return_value=[])
        sdm.get_all_capabilities = MagicMock(return_value=[])
        
        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        assert response.json() == []
        # Check that either method was called
        assert sdm.get_all_capabilities.called or sdm.get_all_capabilities_async.called

    @pytest.mark.timeout(10)
    async def test_list_hsp_services_with_advertisements(self, client_with_overrides):
        client, sdm, dm, ham, mock_hsp_connector = client_with_overrides

        # Simulate a capability advertisement being processed
        mock_advertisement = HSPCapabilityAdvertisementPayload(
            capability_id="test_cap_id_123",
            name="Test Capability",
            description="A test capability for API endpoint",
            version="1.0",
            ai_id="did:hsp:test_ai_1",
            availability_status="online" # Required field
            # Removed unsupported fields: supported_interfaces, timestamp, metadata
        )
        # Use sync call since process_capability_advertisement is now a sync MagicMock
        sdm.process_capability_advertisement(mock_advertisement, "did:hsp:test_ai_1", MagicMock())

        # Mock both get_all_capabilities and get_all_capabilities_async methods
        # Since sdm is an AsyncMock, we need to use AsyncMock for async methods and MagicMock for sync methods
        sdm.get_all_capabilities = MagicMock(return_value=[mock_advertisement])
        sdm.get_all_capabilities_async = AsyncMock(return_value=[mock_advertisement])

        response = client.get("/api/v1/hsp/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["capability_id"] == "test_cap_id_123"
        assert data[0]["name"] == "Test Capability"
        # Check that either method was called
        assert sdm.get_all_capabilities.called or sdm.get_all_capabilities_async.called

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_request_hsp_task_success(self, client_with_overrides, api_test_peer_connector):
        client, sdm, api_dm, ham, mock_hsp_connector = client_with_overrides
        peer_ai_id = "did:hsp:test_api_peer_007"
        mock_echo_cap_id = f"{peer_ai_id}_echo_for_api_v1"
        
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
        
        # Process the capability advertisement directly - use sync call since mock is sync
        sdm.process_capability_advertisement(mock_cap_adv, peer_ai_id, None)
        
        # Verify the capability is in SDM
        found_caps = await sdm.find_capabilities(capability_id_filter=mock_echo_cap_id)
        assert len(found_caps) == 1, f"Capability {mock_echo_cap_id} not found in SDM"
        
        # Make the API request
        response = client.post(
            "/api/v1/hsp/tasks",
            json={
                "target_capability_id": mock_echo_cap_id,
                "parameters": {"message": "Hello from API test"},
            },
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Check that capability was found and task was accepted
        assert "not found" not in response_data.get("status_message", "")
        assert response_data["correlation_id"] is not None
        assert response_data["status_message"] == "HSP Task request sent successfully."
        
        # Verify the send_task_request was called on the mock
        mock_hsp_connector.send_task_request.assert_called_once()
        
        # Clean up any pending task state for this test
        actual_correlation_id = response_data["correlation_id"]
        if hasattr(api_dm, 'pending_hsp_task_requests') and actual_correlation_id in api_dm.pending_hsp_task_requests:
            del api_dm.pending_hsp_task_requests[actual_correlation_id]

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
        # Ensure capability exists in SDM before making the request
        peer_ai_id = TEST_API_PEER_AI_ID
        pending_cap_id = "test_cap_pending"
        mock_cap_adv = HSPCapabilityAdvertisementPayload(
            capability_id=pending_cap_id,
            ai_id=peer_ai_id,
            agent_name="test_pending_agent",
            name="Pending capability for API test",
            description="A capability used to test pending state",
            version="1.0",
            availability_status="online",
            tags=["pending", "test"],
        )
        # Use sync wrapper on mock SDM
        sdm.process_capability_advertisement(mock_cap_adv, peer_ai_id, None)

        # Set up the dialogue manager to track this pending task
        if not hasattr(dialogue_manager, 'pending_hsp_task_requests'):
            dialogue_manager.pending_hsp_task_requests = {}
        dialogue_manager.pending_hsp_task_requests[mock_corr_id] = {
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
            "target": peer_ai_id,
            "capability_id": pending_cap_id,
        }

        # Now check the status of the pending task
        response = client.get(f"/api/v1/hsp/tasks/{mock_corr_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["correlation_id"] == mock_corr_id
        assert status_data["status"] == "pending"
        assert "pending" in status_data["message"].lower()

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
