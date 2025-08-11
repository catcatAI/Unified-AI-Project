import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.base_agent import BaseAgent

@pytest.fixture
def mock_hsp_connector():
    """Fixture to provide a mock HSPConnector."""
    mock = MagicMock()
    mock.register_on_task_request_callback = MagicMock()
    mock.advertise_capability = AsyncMock()
    mock.send_task_result = AsyncMock()
    mock.is_connected = True
    return mock

@pytest.fixture
async def base_agent(mock_hsp_connector):
    """Fixture to provide a BaseAgent instance with a mocked HSPConnector."""
    agent = BaseAgent(
        agent_name="test_agent",
        agent_id="did:hsp:test_agent_123",
        capabilities=[{"name": "test_capability"}]
    )
    # Patch initialize_services and shutdown_services to prevent real service calls
    with patch('src.core_services.initialize_services', new_callable=AsyncMock):
        with patch('src.core_services.shutdown_services', new_callable=AsyncMock):
            await agent._ainit() # This will call the mocked initialize_services
    # After _ainit, explicitly set the agent's hsp_connector to our mock
    agent.hsp_connector = mock_hsp_connector
    return agent

@pytest.mark.asyncio
async def test_base_agent_init(base_agent):
    """Test that the BaseAgent initializes correctly."""
    # _ainit is now called by the fixture, so no explicit call here
    assert base_agent.agent_name == "test_agent"
    assert base_agent.agent_id == "did:hsp:test_agent_123"
    assert base_agent.capabilities == [{"name": "test_capability"}]
    assert base_agent.is_running is False # Should still be False at this point as start() hasn't been called

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
    mock_hsp_connector.send_task_result.assert_called_once_with(
        {'request_id': 'test_request', 'status': 'failure', 'error_details': {'error_code': 'NOT_IMPLEMENTED', 'error_message': "The 'BaseAgent' has not implemented the 'handle_task_request' method."}},
        'test_callback',
        'test_request'
    )
