import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.base_agent import BaseAgent

@pytest.fixture
def base_agent():
    """Create a BaseAgent instance for testing."""
    agent_id = "test_agent_123"
    capabilities = [
        {
            "capability_id": "test_capability_1",
            "name": "Test Capability",
            "description": "A test capability",
            "version": "1.0"
        }
    ]
    return BaseAgent(agent_id=agent_id, capabilities=capabilities, agent_name="TestAgent")

@pytest.mark.asyncio
async def test_base_agent_initialization(base_agent):
    """Test BaseAgent initialization."""
    assert base_agent.agent_id == "test_agent_123"
    assert base_agent.agent_name == "TestAgent"
    assert len(base_agent.capabilities) == 1
    assert base_agent.capabilities[0]["name"] == "Test Capability"
    assert base_agent.hsp_connector is None
    assert base_agent.is_running is False

@pytest.mark.asyncio
async def test_base_agent_start(base_agent):
    """Test BaseAgent start method."""
    # Import the module inside the test to avoid import issues
    import core_services
    
    # Mock the service initialization to avoid creating real services
    with patch.object(core_services, 'initialize_services') as mock_init_services, \
         patch.object(core_services, 'get_services') as mock_get_services, \
         patch.object(core_services, 'shutdown_services') as mock_shutdown_services:
        
        # Make initialize_services a coroutine function
        mock_init_services.return_value = asyncio.Future()
        mock_init_services.return_value.set_result(None)
        
        # Setup mocks
        mock_hsp_connector = AsyncMock()
        mock_hsp_connector.is_connected = True
        mock_get_services.return_value = {"hsp_connector": mock_hsp_connector}
        
        # Start the agent
        await base_agent.start()
        
        # Assertions
        assert base_agent.is_running is True
        assert base_agent.hsp_connector == mock_hsp_connector
        mock_init_services.assert_called_once()
        mock_get_services.assert_called_once()
        if base_agent.hsp_connector:
            base_agent.hsp_connector.register_on_task_request_callback.assert_called_once_with(base_agent.handle_task_request)
        
        # Test that capabilities are advertised
        if base_agent.hsp_connector:
            assert base_agent.hsp_connector.advertise_capability.call_count == len(base_agent.capabilities)

@pytest.mark.asyncio
async def test_base_agent_stop(base_agent):
    """Test BaseAgent stop method."""
    # Import the module inside the test to avoid import issues
    import core_services
    
    # First start the agent
    with patch.object(core_services, 'initialize_services') as mock_init_services, \
         patch.object(core_services, 'get_services') as mock_get_services, \
         patch.object(core_services, 'shutdown_services') as mock_shutdown_services:
        
        # Make initialize_services a coroutine function
        mock_init_services.return_value = asyncio.Future()
        mock_init_services.return_value.set_result(None)
        
        mock_hsp_connector = AsyncMock()
        mock_get_services.return_value = {"hsp_connector": mock_hsp_connector}
        
        await base_agent.start()
        assert base_agent.is_running is True
        
        # Now stop the agent
        await base_agent.stop()
        assert base_agent.is_running is False
        mock_shutdown_services.assert_called_once()

@pytest.mark.asyncio
async def test_base_agent_is_healthy(base_agent):
    """Test BaseAgent health check."""
    # Initially not healthy
    assert base_agent.is_healthy() is False
    
    # Make it healthy
    base_agent.is_running = True
    base_agent.hsp_connector = Mock()
    base_agent.hsp_connector.is_connected = True
    
    assert base_agent.is_healthy() is True

@pytest.mark.asyncio
async def test_base_agent_handle_task_request(base_agent):
    """Test BaseAgent default task request handler."""
    # Mock the HSP connector
    base_agent.hsp_connector = AsyncMock()
    
    # Create a test task payload
    task_payload = {
        "request_id": "test_request_123",
        "capability_id_filter": "nonexistent_capability",
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await base_agent.handle_task_request(task_payload, "sender_456", {})
    
    # Verify that a failure response was sent
    base_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = base_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "failure"
    assert result_payload["error_details"]["error_code"] == "NOT_IMPLEMENTED"
    assert "not implemented" in result_payload["error_details"]["error_message"].lower()

@pytest.mark.asyncio
async def test_base_agent_send_task_success(base_agent):
    """Test BaseAgent send_task_success method."""
    # Mock the HSP connector
    base_agent.hsp_connector = AsyncMock()
    
    # Send a success response
    await base_agent.send_task_success(
        request_id="test_request_123",
        sender_ai_id="sender_456",
        callback_address="test/callback/topic",
        payload={"result": "success"}
    )
    
    # Verify the success response was sent
    base_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = base_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_123"
    assert result_payload["payload"] == {"result": "success"}

@pytest.mark.asyncio
async def test_base_agent_send_task_failure(base_agent):
    """Test BaseAgent send_task_failure method."""
    # Mock the HSP connector
    base_agent.hsp_connector = AsyncMock()
    
    # Send a failure response
    await base_agent.send_task_failure(
        request_id="test_request_123",
        sender_ai_id="sender_456",
        callback_address="test/callback/topic",
        error_message="Test error message"
    )
    
    # Verify the failure response was sent
    base_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = base_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "failure"
    assert result_payload["request_id"] == "test_request_123"
    assert result_payload["error_details"]["error_code"] == "TASK_EXECUTION_FAILED"
    assert result_payload["error_details"]["error_message"] == "Test error message"

if __name__ == '__main__':
    # Run the tests using pytest
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-m', 'pytest', __file__, '-v'])
    sys.exit(result.returncode)