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
def base_agent():
    """Fixture to provide a BaseAgent instance."""
    agent = BaseAgent(
        agent_name="test_agent",
        agent_id="did:hsp:test_agent_123",
        capabilities=[{"name": "test_capability"}]
    )
    return agent

@pytest.mark.asyncio
async def test_base_agent_init(base_agent):
    with patch('src.agents.base_agent.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('src.agents.base_agent.get_services') as mock_get_services:
            mock_get_services.return_value = {} # Init does not need hsp_connector for this test
            await base_agent._ainit()
    """Test that the BaseAgent initializes correctly."""
    assert base_agent.agent_name == "test_agent"
    assert base_agent.agent_id == "did:hsp:test_agent_123"
    assert base_agent.capabilities == [{"name": "test_capability"}]
    assert base_agent.is_running is False

@pytest.mark.asyncio
async def test_base_agent_start_stop(base_agent, mock_hsp_connector):
    """Test that the BaseAgent can start and stop correctly."""
    with patch('src.agents.base_agent.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('src.agents.base_agent.get_services') as mock_get_services:
            with patch('src.agents.base_agent.shutdown_services', new_callable=AsyncMock) as mock_shutdown_services:
                mock_get_services.return_value = {
                    'hsp_connector': mock_hsp_connector,
                    'llm_interface': MagicMock(),
                    'ham_manager': MagicMock(),
                    'personality_manager': MagicMock(),
                    'trust_manager': MagicMock(),
                    'service_discovery': MagicMock(),
                    'fact_extractor': MagicMock(),
                    'content_analyzer': MagicMock(),
                    'learning_manager': MagicMock(),
                    'emotion_system': MagicMock(),
                    'crisis_system': MagicMock(),
                    'time_system': MagicMock(),
                    'formula_engine': MagicMock(),
                    'tool_dispatcher': MagicMock(),
                    'dialogue_manager': MagicMock(),
                    'agent_manager': MagicMock(),
                    'ai_virtual_input_service': MagicMock(),
                    'audio_service': MagicMock(),
                    'vision_service': MagicMock(),
                    'resource_awareness_service': MagicMock(),
                }
                await base_agent.start()
                assert base_agent.is_running is True
                mock_hsp_connector.advertise_capability.assert_called_once()
                await base_agent.stop()
                mock_init_services.assert_called_once()
                mock_shutdown_services.assert_called_once()

@pytest.mark.asyncio
async def test_base_agent_handle_task_request(base_agent, mock_hsp_connector):
    """Test the default handle_task_request method."""
    with patch('src.agents.base_agent.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('src.agents.base_agent.get_services') as mock_get_services:
            mock_get_services.return_value = {
                'hsp_connector': mock_hsp_connector,
                'llm_interface': MagicMock(),
                'ham_manager': MagicMock(),
                'personality_manager': MagicMock(),
                'trust_manager': MagicMock(),
                'service_discovery': MagicMock(),
                'fact_extractor': MagicMock(),
                'content_analyzer': MagicMock(),
                'learning_manager': MagicMock(),
                'emotion_system': MagicMock(),
                'crisis_system': MagicMock(),
                'time_system': MagicMock(),
                'formula_engine': MagicMock(),
                'tool_dispatcher': MagicMock(),
                'dialogue_manager': MagicMock(),
                'agent_manager': MagicMock(),
                'ai_virtual_input_service': MagicMock(),
                'audio_service': MagicMock(),
                'vision_service': MagicMock(),
                'resource_awareness_service': MagicMock(),
            }
            await base_agent._ainit() # Call _ainit to set up the agent with mocked services
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
