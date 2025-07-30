import asyncio
import pytest
from unittest.mock import MagicMock, patch
import json

from src.mcp.connector import MCPConnector
from src.mcp.types import MCPCommandRequest

@pytest.fixture
def mock_mqtt_client():
    with patch('src.mcp.connector.mqtt.Client') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_mcp_connector_initialization(mock_mqtt_client):
    """Test that MCPConnector initializes correctly."""
    connector = MCPConnector('test_ai', 'localhost', 1883, loop=asyncio.get_running_loop())
    assert connector.ai_id == 'test_ai'
    assert mock_mqtt_client.on_connect is not None
    assert mock_mqtt_client.on_message is not None

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_connect_and_disconnect(mock_mqtt_client):
    """Test the connect and disconnect methods."""
    connector = MCPConnector('test_ai', 'localhost', 1883, loop=asyncio.get_event_loop())
    
    await connector.connect()
    mock_mqtt_client.connect.assert_called_once_with('localhost', 1883, 60)
    mock_mqtt_client.loop_start.assert_called_once()

    connector.disconnect()
    mock_mqtt_client.loop_stop.assert_called_once()
    mock_mqtt_client.disconnect.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_send_command(mock_mqtt_client):
    """Test sending a command."""
    connector = MCPConnector('test_ai', 'localhost', 1883, loop=asyncio.get_event_loop())
    await connector.connect()

    target_ai_id = 'target_ai'
    command_name = 'test_command'
    params = {'arg1': 'value1'}

    await connector.send_command(target_ai_id, command_name, params)

    expected_topic = f"mcp/cmd/{target_ai_id}/{command_name}"
    mock_mqtt_client.publish.assert_called_once()
    args, kwargs = mock_mqtt_client.publish.call_args
    assert args[0] == expected_topic
    payload = json.loads(args[1])
    assert payload['payload']['command_name'] == command_name
    assert payload['payload']['parameters'] == params

@pytest.mark.timeout(5)
def test_on_message_callback(mock_mqtt_client):
    """Test the on_message callback handling."""
    callback = MagicMock()
    connector = MCPConnector('test_ai', 'localhost', 1883, loop=asyncio.get_event_loop())
    connector.register_command_handler("test_cmd", callback)

    # Simulate receiving a message
    msg = MagicMock()
    msg.topic = "mcp/cmd/test_ai/test_cmd"
    msg.payload = b'{"args": {"arg1": "value1"}}'

    # Directly call the internal on_message handler
    connector._on_message(mock_mqtt_client, None, msg)

    callback.assert_called_once_with({'arg1': 'value1'})