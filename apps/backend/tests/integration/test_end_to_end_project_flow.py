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

from apps.backend.src.core.managers.agent_manager import AgentManager
from apps.backend.src.ai.dialogue.project_coordinator import ProjectCoordinator
from apps.backend.src.ai.discovery.service_discovery_module import ServiceDiscoveryModule
from apps.backend.src.ai.trust_manager.trust_manager_module import TrustManager
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.ai.personality.personality_manager import PersonalityManager
from apps.backend.src.hsp.connector import HSPConnector
from apps.backend.src.services.multi_llm_service import MultiLLMService

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
    # 确保正确注册能力广告回调
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

@pytest.mark.asyncio
@pytest.mark.timeout(30)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_full_project_flow_with_real_agent(project_coordinator, tmp_path):
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
    # Create a temporary directory for the agent script
    temp_agents_dir = tmp_path / "agents"
    temp_agents_dir.mkdir()
    agent_script_path = temp_agents_dir / "data_analysis_agent.py"

    # Create the script content dynamically to avoid format/f-string issues
    # Use raw string (r'...') and escape backslashes for Windows paths
    src_path_str = SRC_DIR.replace('\\', '\\\\')
    base_dir_str = os.path.dirname(src_path_str)

    agent_script_content = f"""
import asyncio
import json
import sys
import os
import logging

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

PROJECT_SRC_DIR = r'{src_path_str}'
if PROJECT_SRC_DIR not in sys.path:
    sys.path.insert(0, PROJECT_SRC_DIR)

PROJECT_BASE_DIR = r'{base_dir_str}'
if PROJECT_BASE_DIR not in sys.path:
    sys.path.insert(0, PROJECT_BASE_DIR)

from apps.backend.src.hsp.connector import HSPConnector
from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload

class DataAnalysisAgent:
    def __init__(self):
        self.ai_id = "data_analysis_agent_001"
        self.hsp_connector = HSPConnector(
            ai_id=self.ai_id,
            broker_address="127.0.0.1",
            broker_port=1883,
            mock_mode=True
        )

    async def run(self):
        print(f"[{{self.ai_id}}] Connecting to HSP...")
        await self.hsp_connector.connect()
        # 注册任务请求回调
        self.hsp_connector.register_on_task_request_callback(self.handle_task)

        # 修复能力广告，确保包含所有必需字段
        capability = HSPCapabilityAdvertisementPayload(
            capability_id="data_analysis_v1",
            ai_id=self.ai_id,
            name="Data Analysis",
            description="Performs data analysis tasks.",
            version="1.0",
            availability_status="online",
            agent_name="data_analysis_agent"
        )
        print(f"[{{self.ai_id}}] Advertising capability...")
        await self.hsp_connector.publish_capability_advertisement(capability)
        print(f"[{{self.ai_id}}] Capability advertised. Waiting for tasks.")
        
        # Keep running for a while to allow task processing
        for i in range(20):  # Run for 10 seconds
            await asyncio.sleep(0.5)
            print(f"[{{self.ai_id}}] Still running...")

    async def handle_task(self, task_payload, sender_ai_id, envelope):
        print(f"[{{self.ai_id}}] Received task: {{task_payload}}")
        params = task_payload.get("parameters", {{}})
        data = params.get("data", [])
        result_data = sum(data)

        result_payload = HSPTaskResultPayload(
            result_id="res_123",
            request_id=task_payload.get("request_id"),
            executing_ai_id=self.ai_id,
            status="success",
            payload=result_data,
            timestamp_completed="now"
        )
        await self.hsp_connector.send_task_result(
            result_payload,
            sender_ai_id,
            envelope.get("correlation_id")
        )
        print(f"[{{self.ai_id}}] Task completed and result sent.")

if __name__ == "__main__":
    agent = DataAnalysisAgent()
    asyncio.run(agent.run())
"""
    
    agent_script_path.write_text(agent_script_content)

    # Create a test-specific AgentManager pointing to the temporary directory
    test_agent_manager = AgentManager(
        python_executable=sys.executable,
        agents_dir=str(temp_agents_dir)
    )
    
    # Debug information
    print(f"Test agent manager script map: {test_agent_manager.agent_script_map}")
    print(f"Looking for agent 'data_analysis_agent' in script map")
    
    # Replace the default agent_manager in the project_coordinator with our test-specific one
    project_coordinator.agent_manager = test_agent_manager

    agent_name = "data_analysis_agent"
    agent_process = None

    try:
        # --- Act ---
        print(f"Attempting to launch agent: {agent_name}")
        pid = test_agent_manager.launch_agent(agent_name)
        print(f"Launch result PID: {pid}")
        assert pid is not None
        agent_process = test_agent_manager.active_agents[agent_name]
        print(f"Agent process: {agent_process}")

        # Give the agent more time to start and advertise its capability
        await asyncio.sleep(3)

        final_response = await project_coordinator.handle_project(
            "Calculate the sum of a list", "session_e2e", "user_e2e"
        )

        # --- Assert ---
        assert "Here's the result of your project request" in final_response
        assert "The result is: 15" in final_response

    finally:
        # --- Teardown ---
        if agent_process:
            test_agent_manager.shutdown_agent(agent_name)