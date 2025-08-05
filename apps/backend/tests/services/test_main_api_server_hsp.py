import pytest
from fastapi.testclient import TestClient
import uuid
import time
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, ANY
from typing import List

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
            if isinstance(payload, dict):
                processed_payload = HSPCapabilityAdvertisementPayload(**payload)
            elif isinstance(payload, HSPCapabilityAdvertisementPayload):
                processed_payload = payload
            else:
                logging.error(f"Invalid payload type: {type(payload)}")
                return
            self._mock_sdm_capabilities_store[processed_payload.capability_id] = (processed_payload, datetime.now(timezone.utc))
            print(f"DEBUG: Added capability {processed_payload.capability_id} to SDM store")
        except Exception as e:
            logging.error(f"Failed to process capability advertisement: {e}")
            print(f"DEBUG: Failed to process capability advertisement: {e}, payload: {payload}")

    async def find_capabilities(self, capability_id_filter=None, capability_name_filter=None, tags_filter=None, min_trust_score=None, sort_by_trust=False):
        results = []
        for cap_id, (payload, last_seen) in self._mock_sdm_capabilities_store.items():
            if isinstance(payload, dict):
                try:
                    payload = HSPCapabilityAdvertisementPayload(**payload)
                except Exception:
                    continue
            elif not isinstance(payload, HSPCapabilityAdvertisementPayload):
                continue

            if capability_id_filter and cap_id != capability_id_filter:
                continue
            if capability_name_filter and payload.name != capability_name_filter:
                continue
            if tags_filter and not all(tag in payload.tags for tag in tags_filter):
                continue
            results.append(payload)
        return results

    async def get_all_capabilities(self):
        results = []
        for cap_id, (payload, _) in self._mock_sdm_capabilities_store.items():
            if isinstance(payload, dict):
                try:
                    payload = HSPCapabilityAdvertisementPayload(**payload)
                except Exception:
                    continue
            elif not isinstance(payload, HSPCapabilityAdvertisementPayload):
                continue
            results.append(payload)
        return results

@pytest.fixture(scope="function")
async def client_with_overrides(api_test_peer_connector):
    """
    Provides a TestClient for the FastAPI app and the instances used for dependency overrides.
    This fixture is updated to provide all necessary mocks for DialogueManager.
    """
    from unittest.mock import MagicMock, AsyncMock
    from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
    from src.core_ai.trust_manager.trust_manager_module import TrustManager
    from src.core_ai.dialogue.dialogue_manager import DialogueManager
    from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
    from src.core_ai.personality.personality_manager import PersonalityManager
    from src.services.multi_llm_service import MultiLLMService
    from src.core_ai.emotion_system import EmotionSystem
    from src.core_ai.crisis_system import CrisisSystem
    from src.core_ai.time_system import TimeSystem
    from src.core_ai.formula_engine import FormulaEngine
    from src.tools.tool_dispatcher import ToolDispatcher
    from src.core_ai.learning.learning_manager import LearningManager
    from src.hsp.connector import HSPConnector
    from src.core_ai.agent_manager import AgentManager
    from src.tools.tool_dispatcher import ToolDispatcherResponse

    # Create instances that will be shared and controlled by the tests
    trust_manager_for_test = TrustManager()
    mock_sdm_instance = MockSDM()
    sdm_for_test = MagicMock(spec=ServiceDiscoveryModule)

    sdm_for_test.process_capability_advertisement.side_effect = mock_sdm_instance.process_capability_advertisement
    sdm_for_test.find_capabilities.side_effect = mock_sdm_instance.find_capabilities
    sdm_for_test.get_all_capabilities.side_effect = mock_sdm_instance.get_all_capabilities

    ham_for_test = MagicMock(spec=HAMMemoryManager)
    
    # Create mocks for all other DialogueManager dependencies
    mock_personality_manager = MagicMock(spec=PersonalityManager)
    mock_llm_service = MagicMock(spec=MultiLLMService)
    mock_llm_interface = mock_llm_service
    mock_emotion_system = MagicMock(spec=EmotionSystem)
    mock_crisis_system = MagicMock(spec=CrisisSystem)
    mock_time_system = MagicMock(spec=TimeSystem)
    mock_formula_engine = MagicMock(spec=FormulaEngine)
    mock_tool_dispatcher = AsyncMock(spec=ToolDispatcher)
    # Configure the mock tool_dispatcher to return a successful ToolDispatcherResponse
    mock_tool_dispatcher.dispatch.return_value = ToolDispatcherResponse(
        status="no_tool_found", # Or "success" depending on the test's needs
        payload="Mocked tool response",
        tool_name_attempted="none",
        original_query_for_tool="mock query",
        error_message=None
    )
    mock_learning_manager = MagicMock(spec=LearningManager)
    mock_hsp_connector = AsyncMock(spec=HSPConnector)
    mock_hsp_connector.ai_id = "test_hsp_connector_id"
    mock_hsp_connector.connect.return_value = True
    mock_hsp_connector.publish_capability_advertisement.return_value = True
    mock_hsp_connector.subscribe.return_value = True

    # New: Capture the on_task_result_callback
    mock_hsp_connector._registered_task_result_callback = None
    def mock_register_on_task_result_callback(callback):
        mock_hsp_connector._registered_task_result_callback = callback
    mock_hsp_connector.register_on_task_result_callback.side_effect = mock_register_on_task_result_callback
    mock_agent_manager = MagicMock(spec=AgentManager)

    # Define mock_project_coordinator here
    mock_project_coordinator = MagicMock(spec=ProjectCoordinator)
    mock_project_coordinator.handle_project.return_value = "Mocked project response"
    mock_project_coordinator.handle_task_result.return_value = None # Or a more specific mock if needed
    mock_project_coordinator.pending_hsp_task_requests = {}
    mock_project_coordinator.task_results = {}
    mock_project_coordinator.task_completion_events = {}



    dm_for_test = DialogueManager(
        ai_id="test_api_dm_id",
        personality_manager=mock_personality_manager,
        memory_manager=ham_for_test,
        llm_interface=mock_llm_interface,
        emotion_system=mock_emotion_system,
        crisis_system=mock_crisis_system,
        time_system=mock_time_system,
        formula_engine=mock_formula_engine,
        tool_dispatcher=mock_tool_dispatcher,
        learning_manager=mock_learning_manager,
        service_discovery_module=sdm_for_test,
        hsp_connector=mock_hsp_connector, # Ensure hsp_connector is passed
        agent_manager=mock_agent_manager,
        project_coordinator=mock_project_coordinator
    )
    # Manually set the pending_hsp_task_requests attribute on the mocked DialogueManager
    # as it's accessed directly in main_api_server.py


    # Override the dependencies in the FastAPI app
    app.dependency_overrides[get_services] = lambda: {
        "service_discovery": sdm_for_test,
        "trust_manager": trust_manager_for_test,
        "dialogue_manager": dm_for_test,
        "ham_manager": ham_for_test,
        # Add other mocked services if the API endpoints need them
        "personality_manager": mock_personality_manager,
        "llm_interface": mock_llm_interface,
        "emotion_system": mock_emotion_system,
        "crisis_system": mock_crisis_system,
        "time_system": mock_time_system,
        "formula_engine": mock_formula_engine,
        "tool_dispatcher": mock_tool_dispatcher,
        "learning_manager": mock_learning_manager,
        "hsp_connector": mock_hsp_connector,
        "agent_manager": mock_agent_manager,
        "project_coordinator": dm_for_test.project_coordinator # Use the actual project_coordinator from DM
    }

    with TestClient(app) as test_client:
        yield test_client, sdm_for_test, dm_for_test, ham_for_test, mock_hsp_connector

    # Clean up the override
    app.dependency_overrides = {}


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
        await sdm.find_capabilities.assert_called_once_with()

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
            metadata={"test_key": "test_value"}
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
        
        # Use the existing api_test_peer_connector fixture
        peer_conn = api_test_peer_connector
        
        # Create a capability advertisement
        mock_cap_adv = HSPCapabilityAdvertisementPayload(
            capability_id=mock_echo_cap_id,
            name="Echo capability for API test",
            description="Echo capability for API test",
            tags=["echo", "test"],
            parameters_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            result_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            trust_score=0.9,
            provider_ai_id=peer_ai_id,
        )
        
        # Process the capability advertisement directly
        await sdm.process_capability_advertisement(mock_cap_adv, peer_ai_id, None)
        
        # Debug: Print all capabilities in SDM
        all_caps = await sdm.get_all_capabilities()
        print(f"\nAll capabilities in SDM: {[cap.capability_id for cap in all_caps]}")
        
        # Verify the capability is in SDM
        found_caps = await sdm.find_capabilities(capability_id_filter=mock_echo_cap_id)
        print(f"\nFound capabilities with filter '{mock_echo_cap_id}': {[cap.capability_id for cap in found_caps]}")
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
                "correlation_id": mock_corr_id,
                "capability_id_filter": mock_echo_cap_id,
                "parameters": {"message": "Hello from API test"},
            },
        )
        
        # Debug: Print API response
        print(f"\nAPI response: {response.status_code} {response.json()}")
        
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["correlation_id"] == mock_corr_id
        
        # Wait for the task to be handled
        try:
            await asyncio.wait_for(task_request_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            assert False, "Timeout waiting for task request to be handled"
        
        # Verify the task request was received by the peer
        assert task_request_payload is not None
        assert task_request_payload["correlation_id"] == mock_corr_id
        
        # Verify the task was removed from pending requests
        assert mock_corr_id not in api_dm._pending_hsp_task_requests
        
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
    async def test_get_hsp_task_status_pending(self, client_with_overrides):
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

        # Simulate the HSPConnector receiving a task request and the DM registering its callback
        # The DM's internal logic will register a callback with mock_hsp_connector.
        # We need to ensure that when the API calls request_hsp_task, it triggers
        # the DM's internal logic, which then uses the mock_hsp_connector.

        # The `client_with_overrides` fixture already sets up `mock_hsp_connector`
        # with a `register_on_task_request_callback` side effect that captures the callback.
        # We need to ensure that the `DialogueManager` (dm) registers its callback.
        # This happens during the `initialize_services` call within the FastAPI lifespan.

        # To simulate a pending task, we need to prevent the peer from immediately responding.
        # We can temporarily disable the peer's task handling for this specific test.
        original_peer_task_handler = api_test_peer_connector.send_task_request.side_effect
        api_test_peer_connector.send_task_request.side_effect = AsyncMock(return_value=True) # Prevent peer from responding

        # Make an initial request to trigger the pending state
        response = client.post("/api/v1/hsp/tasks", json={
            "target_capability_id": "test_cap_pending",
            "parameters": {"data": "test"}
        })
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
