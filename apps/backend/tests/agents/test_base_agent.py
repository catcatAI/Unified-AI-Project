import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.base_agent import BaseAgent

@pytest.fixture
def mock_hsp_connector():
    """Fixture to provide a mock HSPConnector."""
    mock = MagicMock()
    mock.advertise_capability = AsyncMock()
    mock.send_task_result = AsyncMock()
    mock.register_on_task_request_callback = MagicMock()
    mock.is_connected = True
    return mock

@pytest.fixture
def base_agent(mock_hsp_connector):
    """Fixture to provide a BaseAgent instance."""
    with patch('src.agents.base_agent.initialize_services'), \
         patch('src.agents.base_agent.get_services', return_value={'hsp_connector': mock_hsp_connector}):
        agent = BaseAgent(
            agent_name="test_agent",
            agent_id="did:hsp:test_agent_123",
            capabilities=[{"name": "test_capability"}]
        )
        return agent

@pytest.mark.asyncio
async def test_base_agent_init(base_agent):
    """Test that the BaseAgent initializes correctly."""
    assert base_agent.agent_name == "test_agent"
    assert base_agent.agent_id == "did:hsp:test_agent_123"
    assert base_agent.capabilities == [{"name": "test_capability"}]
    assert base_agent.is_running is False

@pytest.mark.asyncio
async def test_base_agent_start_stop(base_agent, mock_hsp_connector):
    """Test that the BaseAgent can start and stop correctly."""
    await base_agent.start()
    assert base_agent.is_running is True
    mock_hsp_connector.advertise_capability.assert_called_once()
    await base_agent.stop()

@pytest.mark.asyncio
async def test_base_agent_handle_task_request(base_agent, mock_hsp_connector):
    """Test the default handle_task_request method."""
    task_payload = {
        "request_id": "test_request",
        "capability_id_filter": "test_capability",
        "callback_address": "test_callback"
    }
    envelope = {"sender_ai_id": "test_sender"}
    await base_agent.handle_task_request(task_payload, "test_sender", envelope)
    mock_hsp_connector.send_task_result.assert_called_once()
    call_args = mock_hsp_connector.send_task_result.call_args[0]
    assert call_args[0]['status'] == 'failure'
    assert call_args[0]['error_details']['error_code'] == 'NOT_IMPLEMENTED'
    assert call_args[1] == 'test_callback'
