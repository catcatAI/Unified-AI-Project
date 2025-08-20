import pytest
import asyncio
import sys
import json
import os
from unittest.mock import MagicMock, AsyncMock

# Ensure the src directory is in the Python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core_ai.agent_manager import AgentManager
from core_ai.dialogue.project_coordinator import ProjectCoordinator
from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from core_ai.trust_manager.trust_manager_module import TrustManager
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.personality.personality_manager import PersonalityManager
from hsp.connector import HSPConnector
from services.multi_llm_service import MultiLLMService

# A simplified mock MQTT broker for this test
class MockMqttBroker:
    def __init__(self):
        self.subscriptions = {}
        self.queue = asyncio.Queue()
        self.is_running = False

    async def start(self):
        self.is_running = True
        asyncio.create_task(self._dispatch_loop())

    async def stop(self):
        self.is_running = False
        # Put a sentinel value to unblock the queue
        await self.queue.put(None)

    async def _dispatch_loop(self):
        while self.is_running:
            message = await self.queue.get()
            if message is None:
                break
            topic, payload = message
            for sub_topic, callbacks in self.subscriptions.items():
                if self._topic_matches(sub_topic, topic):
                    for cb in callbacks:
                        # The gmqtt client expects a specific object, not just a raw payload
                        mock_message = MagicMock()
                        mock_message.topic = topic
                        mock_message.payload = payload
                        # The on_message callback in ExternalConnector expects (client, topic, payload, qos, properties)
                        # We are bypassing this and calling the HSPConnector's internal handler, which is not ideal.
                        # Let's adjust to call the external_connector's on_message
                        asyncio.create_task(cb(None, topic, payload, 1, {}))

    def _topic_matches(self, sub, pub):
        # Simplified topic matching for this test
        return sub == pub or sub == "#" or pub.startswith(sub.replace("#", ""))

    async def publish(self, topic, payload, qos=1, retain=False, **kwargs):
        if self.is_running:
            await self.queue.put((topic, payload))

    def subscribe(self, topic, qos=1):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []

    def on_message(self, callback):
        # This is a simplification. A real gmqtt client would have a more complex callback registration.
        # We will assume a wildcard subscription for simplicity.
        if "#" not in self.subscriptions:
            self.subscriptions["#"] = []
        self.subscriptions["#"].append(callback)

# Fixtures
@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def mock_broker():
    broker = MockMqttBroker()
    await broker.start()
    yield broker
    await broker.stop()

@pytest.fixture
def trust_manager():
    return TrustManager()

@pytest.fixture
def agent_manager():
    # This assumes the test is run from the root of the monorepo
    python_executable = sys.executable
    return AgentManager(python_executable=python_executable)

@pytest.fixture
async def hsp_connector(mock_broker, event_loop):
    # This connector will be used by the ProjectCoordinator (the "main AI")
    connector = HSPConnector(
        ai_id="project_coordinator_ai",
        broker_address="127.0.0.1",
        broker_port=1883,
        mock_mode=True  # Use mock mode to avoid real MQTT client issues
    )
    # Monkey-patch the mqtt client to use our mock broker
    connector.external_connector.mqtt_client.connect = AsyncMock(return_value=None)
    connector.external_connector.mqtt_client.disconnect = AsyncMock(return_value=None)
    # Use AsyncMock with proper return value to avoid NoneType errors
    connector.external_connector.mqtt_client.publish = AsyncMock(return_value=True, side_effect=mock_broker.publish)
    # Fix subscribe to be an AsyncMock that also calls mock_broker.subscribe
    async def mock_subscribe(topic, qos=1):
        mock_broker.subscribe(topic, qos)
        return True
    connector.external_connector.mqtt_client.subscribe = AsyncMock(side_effect=mock_subscribe)
    # Also ensure external_connector.publish and subscribe are properly mocked
    connector.external_connector.publish = AsyncMock(return_value=True, side_effect=mock_broker.publish)
    connector.external_connector.subscribe = AsyncMock(return_value=True)
    # Register the on_message callback with the mock broker
    mock_broker.on_message(connector.on_message)

    await connector.connect()
    yield connector
    await connector.disconnect()

@pytest.fixture
def service_discovery(trust_manager, hsp_connector):
    sdm = ServiceDiscoveryModule(trust_manager=trust_manager)
    hsp_connector.register_on_capability_advertisement_callback(sdm.process_capability_advertisement)
    sdm.start_cleanup_task()
    yield sdm
    sdm.stop_cleanup_task()

@pytest.fixture
def project_coordinator(hsp_connector, service_discovery, agent_manager):
    # Mock dependencies that are not under test
    mock_llm = AsyncMock(spec=MultiLLMService)
    mock_ham = MagicMock(spec=HAMMemoryManager)
    mock_learning = AsyncMock()
    mock_personality = MagicMock(spec=PersonalityManager)
    mock_personality.get_current_personality_trait.return_value = "TestCoordinator"

    # Simplified decomposition for the test
    async def fake_decompose(query, caps):
        return [{
            "capability_needed": "data_analysis_v1",
            "task_parameters": {"data": [1, 2, 3, 4, 5]},
            "task_description": "Calculate the sum of the list"
        }]

    async def fake_integrate(query, results):
        # ProjectCoordinator._wait_for_task_result returns payload directly or error dict
        # results[0] should contain the payload (15) or an error dict {"error": "..."}
        result_value = results[0]
        if isinstance(result_value, dict) and "error" in result_value:
            return f"Task failed: {result_value['error']}"
        else:
            return f"The result is: {result_value}"

    mock_llm.generate_response.side_effect = [
        json.dumps([{
            "capability_needed": "data_analysis_v1",
            "task_parameters": {"data": [1, 2, 3, 4, 5]},
            "task_description": "Calculate the sum of the list"
        }]),
        "The result is: 15" # This will be replaced by the real integration logic
    ]

    pc = ProjectCoordinator(
        llm_interface=mock_llm,
        service_discovery=service_discovery,
        hsp_connector=hsp_connector,
        agent_manager=agent_manager,
        memory_manager=mock_ham,
        learning_manager=mock_learning,
        personality_manager=mock_personality,
        dialogue_manager_config={"turn_timeout_seconds": 15}
    )
    # Replace the LLM-based integration with a simpler one for this test
    pc._integrate_subtask_results = fake_integrate
    return pc

# A dummy agent script that will be created dynamically for the test
DATA_ANALYSIS_AGENT_SCRIPT = """
import asyncio
import json
import sys
import os

# Add both src and parent directory to path to allow imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
# Also add the parent of src to allow 'src.module' imports
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from hsp.connector import HSPConnector
from hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload

class DataAnalysisAgent:
    def __init__(self):
        self.ai_id = "data_analysis_agent_001"
        self.hsp_connector = HSPConnector(
            ai_id=self.ai_id,
            broker_address="127.0.0.1",
            broker_port=1883,
            mock_mode=False
        )
        # In a real scenario, this would use a real MQTT client.
        # For this test, we need to patch it to use the mock broker.
        # This is tricky as it's a different process. The test will rely on the default address.

    async def run(self):
        # This is a simplified connection for the test.
        # A real agent would have more robust connection logic.
        await self.hsp_connector.connect()
        self.hsp_connector.register_on_task_request_callback(self.handle_task)

        capability = HSPCapabilityAdvertisementPayload(
            capability_id="data_analysis_v1",
            ai_id=self.ai_id,
            name="Data Analysis",
            description="Performs data analysis tasks.",
            version="1.0",
            availability_status="online",
        )
        await self.hsp_connector.publish_capability_advertisement(capability)
        print(f"[{self.ai_id}] Capability advertised. Waiting for tasks.")
        await asyncio.Event().wait() # Keep running

    async def handle_task(self, task_payload, sender_ai_id, envelope):
        print(f"[{self.ai_id}] Received task: {task_payload}")
        params = task_payload.get("parameters", {})
        data = params.get("data", [])
        result_data = sum(data)

        result_payload = HSPTaskResultPayload(
            result_id="res_123",
            request_id=task_payload.get("request_id"),
            executing_ai_id=self.ai_id,
            status="success",
            payload=result_data,
            timestamp_completed= "now"
        )
        await self.hsp_connector.send_task_result(
            result_payload,
            sender_ai_id,
            envelope.get("correlation_id")
        )
        print(f"[{self.ai_id}] Task completed and result sent.")

if __name__ == "__main__":
    agent = DataAnalysisAgent()
    asyncio.run(agent.run())
"""

@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_full_project_flow_with_real_agent(project_coordinator, agent_manager):
    """
    Tests the full end-to-end flow:
    1. ProjectCoordinator receives a project.
    2. Decomposes it to a task for a capability that is not yet available.
    3. Launches the DataAnalysisAgent via AgentManager.
    4. The agent starts, connects to the mock broker, and advertises its capability.
    5. ProjectCoordinator discovers the capability and sends the task.
    6. The agent receives the task, computes the result, and sends it back.
    7. ProjectCoordinator receives the result and integrates it into a final answer.
    """
    # --- Arrange ---
    # Create the dummy agent script file
    agent_script_path = os.path.join(SRC_DIR, "agents", "data_analysis_agent.py")
    os.makedirs(os.path.dirname(agent_script_path), exist_ok=True)
    with open(agent_script_path, "w") as f:
        f.write(DATA_ANALYSIS_AGENT_SCRIPT)

    # Refresh AgentManager discovery to include the newly created script
    agent_manager.agent_script_map = agent_manager._discover_agent_scripts()

    # The agent_manager fixture already discovered this script.
    # We need to patch the HSPConnector inside the agent process to use the mock broker.
    # This is the hardest part of this test. Since we can't easily patch a separate
    # process, we will rely on the fact that both the test and the agent script
    # default to connecting to 127.0.0.1:1883, and our mock broker will be the
    # only thing listening there.

    agent_name = "data_analysis_agent"
    agent_process = None

    try:
        # --- Act ---
        # Launch the agent in the background. It will connect and advertise.
        pid = agent_manager.launch_agent(agent_name)
        assert pid is not None
        agent_process = agent_manager.active_agents[agent_name]

        # Give the agent a moment to start up and advertise its capability.
        await asyncio.sleep(5)

        # Now, trigger the project. The ProjectCoordinator should find the capability.
        final_response = await project_coordinator.handle_project(
            "Calculate the sum of a list", "session_e2e", "user_e2e"
        )

        # --- Assert ---
        assert "Here's the result of your project request" in final_response
        assert "The result is: 15" in final_response

    finally:
        # --- Teardown ---
        if agent_process:
            agent_manager.shutdown_agent(agent_name)
        # It's good practice to clean up the created file
        if os.path.exists(agent_script_path):
            os.remove(agent_script_path)

@pytest.mark.asyncio
async def test_mocked_end_to_end_flow(project_coordinator):
    """
    A fully mocked version of the end-to-end flow. This tests the
    ProjectCoordinator's orchestration logic without the overhead of
    subprocesses or networking.
    """
    # Arrange
    pc = project_coordinator
    user_query = "Build a website for me."

    # Mock the LLM decomposition
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=[
        {"capability_needed": "create_files_v1", "task_parameters": {"files": ["index.html"]}}
    ])

    # Mock the dispatch logic
    pc._dispatch_single_subtask = AsyncMock(return_value={"status": "success", "result": "index.html created."})

    # Mock the integration logic
    pc._integrate_subtask_results = AsyncMock(return_value="The website is ready.")

    # Act
    response = await pc.handle_project(user_query, "session_mock", "user_mock")

    # Assert
    pc._decompose_user_intent_into_subtasks.assert_awaited_once()
    pc._dispatch_single_subtask.assert_awaited_once() # In a single-task project
    pc._integrate_subtask_results.assert_awaited_once()
    assert "The website is ready." in response
