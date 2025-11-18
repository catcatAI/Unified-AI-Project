import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from ai.agents.agent_collaboration_manager import AgentCollaborationManager, BaseAgent
from core.hsp.connector import HSPConnector
from typing import Any, Dict, List # Added for type hinting in MockRespondingAgent
import pytest_asyncio

# Mock HSPConnector for testing purposes
@pytest.fixture
def mock_hsp_connector():
    with patch('core.hsp.connector.HSPConnector', autospec=True) as MockHSPConnector:
        instance = MockHSPConnector.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.disconnect = AsyncMock()
        instance.subscribe = AsyncMock()
        instance.send_message = AsyncMock(return_value=True)
        instance.is_connected = True # Simulate connected state
        yield instance

# A simple mock agent that can receive tasks and send responses
class MockRespondingAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, hsp_connector: HSPConnector, **kwargs: Any):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        self.hsp_connector = hsp_connector
        self.task_topic = f"agent/{self.agent_id}/tasks"
        self.received_tasks = asyncio.Queue()
        self.is_running = False # Override BaseAgent's is_running for mock

    async def perceive(self, task: Dict[str, Any]) -> Any:
        await asyncio.sleep(0.01)
        return {"perceived_data": f"Processed: {task.get('description', 'N/A')}"}

    async def decide(self, perceived_info: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"action_type": "complete", "result_info": perceived_info}

    async def act(self, decision: Dict[str, Any]) -> Any:
        await asyncio.sleep(0.01)
        return {"action_status": "success", "final_result": decision.get("result_info")}

    async def feedback(self, original_task: Dict[str, Any], action_result: Any) -> None:
        response_topic = original_task.get("response_topic")
        manager_id = original_task.get("manager_id")
        if response_topic and manager_id and self.hsp_connector:
            response_payload = {
                "status": "completed",
                "agent_id": self.agent_id,
                "original_task_id": original_task.get("id"),
                "result": action_result
            }
            await self.hsp_connector.send_message(response_topic, response_payload)

    async def _hsp_task_handler(self, topic: str, payload: Dict[str, Any]):
        await self.received_tasks.put(payload)
        # Simulate processing and sending feedback
        await self.handle_task(payload)

    async def start(self):
        self.is_running = True
        await self.hsp_connector.subscribe(self.task_topic, self._hsp_task_handler)
        # In a real scenario, we'd run the BaseAgent's start loop, but for mock, we just subscribe.
        # super().start() would block, so we don't call it directly here.

    async def stop(self):
        self.is_running = False
        # No explicit unsubscribe needed for mock

@pytest_asyncio.fixture
async def collaboration_manager(mock_hsp_connector):
    manager = AgentCollaborationManager(name="TestTeamLead", hsp_connector=mock_hsp_connector)
    # Manually set the hsp_connector for the manager instance
    manager.hsp_connector = mock_hsp_connector
    # Start the manager's HSP connection and subscription
    await manager.hsp_connector.connect()
    await manager.hsp_connector.subscribe(f"collab_manager/{manager.agent_id}/responses", manager._response_handler)
    yield manager
    await manager.stop()

@pytest.mark.asyncio
async def test_manager_initialization(collaboration_manager: AgentCollaborationManager, mock_hsp_connector: MagicMock):
    """Test if the manager initializes correctly and connects HSP."""
    assert collaboration_manager.name == "TestTeamLead"
    assert collaboration_manager.agent_id is not None
    mock_hsp_connector.connect.assert_called_once()
    mock_hsp_connector.subscribe.assert_called_once_with(
        f"collab_manager/{collaboration_manager.agent_id}/responses",
        collaboration_manager._response_handler
    )

@pytest.mark.asyncio
async def test_register_agent_operation(collaboration_manager: AgentCollaborationManager):
    """Test the manager's ability to register a new agent."""
    agent_id = "test_agent_1"
    register_task = {"operation": "register_agent", "payload": {"agent_name": "WriterBot", "agent_id": agent_id}}
    
    result = await collaboration_manager.handle_task(register_task)
    
    assert result["status"] == "completed"
    assert "Agent 'WriterBot' registered with ID 'test_agent_1'." in result["result"]["message"]
    assert agent_id in collaboration_manager.registered_agents
    assert agent_id in collaboration_manager.agent_response_queues

@pytest.mark.asyncio
async def test_orchestrate_operation(collaboration_manager: AgentCollaborationManager, mock_hsp_connector: MagicMock):
    """Test the manager's ability to orchestrate subtasks to registered agents."""
    # Register a mock agent first
    writer_agent_id = "writer_agent_1"
    writer_agent = MockRespondingAgent(agent_id=writer_agent_id, name="WriterBot", hsp_connector=mock_hsp_connector)
    await writer_agent.start() # Start the mock agent's HSP subscription

    register_task = {"operation": "register_agent", "payload": {"agent_name": "WriterBot", "agent_id": writer_agent_id}}
    await collaboration_manager.handle_task(register_task)

    # Simulate the manager's response queue for the mock agent
    # This is crucial because the manager waits for responses on this queue
    collaboration_manager.agent_response_queues[writer_agent_id] = asyncio.Queue()

    orchestration_task = {
        "operation": "orchestrate",
        "payload": {
            "subtasks": [
                {"target_agent_id": writer_agent_id, "description": "Write a short story.", "type": "write_story", "id": "story_task_1"}
            ]
        }
    }

    # Simulate the mock agent sending a response back to the manager
    response_payload = {
        "status": "completed",
        "agent_id": writer_agent_id,
        "original_task_id": "story_task_1",
        "result": {"action_status": "success", "processed_item": "Processed: Write a short story."}
    }
    # Put the response directly into the manager's queue for this agent
    await collaboration_manager.agent_response_queues[writer_agent_id].put(response_payload)

    result = await collaboration_manager.handle_task(orchestration_task)
    
    assert result["status"] == "completed"
    assert "orchestration_summary" in result["result"]
    assert len(result["result"]["subtask_results"]) == 1
    assert result["result"]["subtask_results"][0]["agent_id"] == writer_agent_id
    assert result["result"]["subtask_results"][0]["subtask_result"] == response_payload

    # Verify send_message was called on the mock HSP connector for the subtask
    mock_hsp_connector.send_message.assert_called_with(
        f"agent/{writer_agent_id}/tasks",
        {
            "target_agent_id": writer_agent_id,
            "description": "Write a short story.",
            "type": "write_story",
            "id": "story_task_1",
            "response_topic": f"collab_manager/{collaboration_manager.agent_id}/responses",
            "manager_id": collaboration_manager.agent_id
        }
    )
    await writer_agent.stop()

@pytest.mark.asyncio
async def test_orchestrate_operation_timeout(collaboration_manager: AgentCollaborationManager, mock_hsp_connector: MagicMock):
    """Test orchestration when a subtask times out."""
    # Register a mock agent that won't send a response
    timeout_agent_id = "timeout_agent_1"
    timeout_agent = MockRespondingAgent(agent_id=timeout_agent_id, name="TimeoutBot", hsp_connector=mock_hsp_connector)
    await timeout_agent.start()

    register_task = {"operation": "register_agent", "payload": {"agent_name": "TimeoutBot", "agent_id": timeout_agent_id}}
    await collaboration_manager.handle_task(register_task)

    # Set a short timeout for the manager's internal wait_for
    collaboration_manager.task_timeout = 1 # Short timeout for this test

    orchestration_task = {
        "operation": "orchestrate",
        "payload": {
            "subtasks": [
                {"target_agent_id": timeout_agent_id, "description": "Task that will time out.", "type": "timeout_task", "id": "timeout_task_1"}
            ]
        }
    }

    result = await collaboration_manager.handle_task(orchestration_task)

    assert result["status"] == "failed"
    assert "error" in result
    assert f"Task timed out after {collaboration_manager.task_timeout} seconds." in result["error"]
    
    await timeout_agent.stop()

@pytest.mark.asyncio
async def test_orchestrate_operation_unregistered_agent(collaboration_manager: AgentCollaborationManager):
    """Test orchestration with an unregistered agent."""
    orchestration_task = {
        "operation": "orchestrate",
        "payload": {
            "subtasks": [
                {"target_agent_id": "unregistered_agent", "description": "Task for unregistered agent.", "type": "unreg_task", "id": "unreg_task_1"}
            ]
        }
    }

    result = await collaboration_manager.handle_task(orchestration_task)

    assert result["status"] == "completed"
    assert len(result["result"]["subtask_results"]) == 1
    assert result["result"]["subtask_results"][0]["agent_id"] == "unregistered_agent"
    assert result["result"]["subtask_results"][0]["subtask_result"]["status"] == "failed"
    assert "Target agent not found or specified." in result["result"]["subtask_results"][0]["subtask_result"]["error"]
