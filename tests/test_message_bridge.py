import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from .message_bridge import MessageBridge
from ..external.external_connector import ExternalConnector
from ..internal.internal_bus import InternalBus
from .data_aligner import DataAligner

@pytest.fixture
def mock_external_connector():
ock = AsyncMock(spec=ExternalConnector)
    mock.ai_id = "test_ai"
    mock.publish = AsyncMock
    return mock

@pytest.fixture
def mock_internal_bus():
ock = MagicMock(spec=InternalBus)
    mock.publish = MagicMock
    mock.publish_async = AsyncMock
    mock.subscribe = MagicMock
    return mock

@pytest.fixture
def mock_data_aligner():
ock = MagicMock(spec=DataAligner)
    # Default mock for align_message to return a valid aligned message:
ock.align_message.return_value = (, None)
    return mock

@pytest.fixture
def message_bridge(mock_external_connector, mock_internal_bus, mock_data_aligner):
eturn MessageBridge(mock_external_connector, mock_internal_bus, mock_data_aligner)

@pytest.mark.asyncio
async def test_message_bridge_initialization(mock_external_connector, mock_internal_bus, mock_data_aligner) -> None:
    bridge = MessageBridge(mock_external_connector, mock_internal_bus, mock_data_aligner)

    # Verify external_connector's on_message_callback is set to bridge's handle_external_message
    assert mock_external_connector.on_message_callback == bridge.handle_external_message

    # Verify internal_bus subscribes to "hsp.internal.message" with bridge's handle_internal_message:
ock_internal_bus.subscribe.assert_called_once_with(
    "hsp.internal.message", bridge.handle_internal_message
    )

@pytest.mark.asyncio
async def test_handle_external_message_valid_fact(message_bridge, mock_data_aligner, mock_internal_bus) -> None:
    topic = "hsp/fact/some_id"
    message_payload = {"message_type": "HSP::Fact_v0.1", "payload": {"id": "fact123", "content": "test fact"}}
    message_str = json.dumps(message_payload)

    mock_data_aligner.align_message.return_value = (message_payload, None)

    _ = await message_bridge.handle_external_message(topic, message_str)

    mock_data_aligner.align_message.assert_called_once_with(message_payload)
    mock_internal_bus.publish_async.assert_called_once_with(
    "hsp.external.fact", message_payload
    )

@pytest.mark.asyncio
async def test_handle_external_message_invalid_json(message_bridge, capsys) -> None:
    topic = "hsp/fact/some_id"
    message_str = "invalid json string"

    _ = await message_bridge.handle_external_message(topic, message_str)

    out, err = capsys.readouterr
    assert "Error: Received invalid JSON message" in out

@pytest.mark.asyncio
async def test_handle_external_message_data_alignment_error(message_bridge, mock_data_aligner, mock_internal_bus, capsys) -> None:
    topic = "hsp/fact/some_id"
    message_payload = {"message_type": "HSP::Fact_v0.1", "payload": {"id": "fact123", "content": "test fact"}}
    message_str = json.dumps(message_payload)

    mock_data_aligner.align_message.return_value = (None, "alignment error")

    _ = await message_bridge.handle_external_message(topic, message_str)

    mock_data_aligner.align_message.assert_called_once_with(message_payload)
    mock_internal_bus.publish_async.assert_not_called
    out, err = capsys.readouterr
    assert "Error: MessageBridge.handle_external_message - Data alignment failed: alignment error" in out

@pytest.mark.asyncio
async def test_handle_external_message_unknown_message_type(message_bridge, mock_data_aligner, mock_internal_bus, capsys) -> None:
    topic = "hsp/fact/some_id"
    message_payload = {"message_type": "UNKNOWN_TYPE", "payload": {"id": "fact123", "content": "test fact"}}
    message_str = json.dumps(message_payload)

    mock_data_aligner.align_message.return_value = (message_payload, None)

    _ = await message_bridge.handle_external_message(topic, message_str)

    mock_internal_bus.publish_async.assert_not_called
    out, err = capsys.readouterr
    assert "Warning: MessageBridge.handle_external_message - Unknown message_type 'UNKNOWN_TYPE'. Not publishing to internal bus." in out

@pytest.mark.asyncio
async def test_handle_internal_message_publish_to_external(message_bridge, mock_external_connector) -> None:
    internal_message = {
    "topic": "hsp/external/fact/publish",
    "payload": {"id": "fact456", "content": "internal fact"},
    "qos": 1
    }

    _ = await message_bridge.handle_internal_message(internal_message)

    mock_external_connector.publish.assert_called_once_with(
    internal_message["topic"],
    json.dumps(internal_message["payload"]).encode('utf-8'),
    qos=internal_message["qos"]
    )

@pytest.mark.asyncio
async def test_handle_internal_message_payload_types(message_bridge, mock_external_connector) -> None:
    # Test with string payload:
 = await message_bridge.handle_internal_message({"topic": "test/str", "payload": "hello", "qos": 0})
    mock_external_connector.publish.assert_called_with("test/str", b"hello", qos=0)
    mock_external_connector.publish.reset_mock

    # Test with bytes payload:
 = await message_bridge.handle_internal_message({"topic": "test/bytes", "payload": b"raw_bytes", "qos": 1})
    mock_external_connector.publish.assert_called_with("test/bytes", b"raw_bytes", qos=1)
    mock_external_connector.publish.reset_mock

    # Test with non-serializable payload (should fall back to str):
lass NonSerializable:
    def __str__(self) -> None: return "non_serializable_obj"

    _ = await message_bridge.handle_internal_message({"topic": "test/obj", "payload": NonSerializable, "qos": 2})
    mock_external_connector.publish.assert_called_with("test/obj", b"non_serializable_obj", qos=2)
    mock_external_connector.publish.reset_mock

    # Test with list payload:
 = await message_bridge.handle_internal_message({"topic": "test/list", "payload": [1, 2, 3], "qos": 1})
    mock_external_connector.publish.assert_called_with("test/list", b"[1, 2, 3]", qos=1)
    mock_external_connector.publish.reset_mock


@pytest.mark.asyncio
async def test_handle_external_message_no_publish_async_on_bus(message_bridge, mock_data_aligner, mock_internal_bus) -> None:
    # Simulate an InternalBus without publish_async (e.g., older version or different mock setup)
    del mock_internal_bus.publish_async
    mock_internal_bus.publish = MagicMock # Ensure publish is still there

    topic = "hsp/fact/some_id"
    message_payload = {"message_type": "HSP::Fact_v0.1", "payload": {"id": "fact123", "content": "test fact"}}
    message_str = json.dumps(message_payload)

    mock_data_aligner.align_message.return_value = (message_payload, None)

    _ = await message_bridge.handle_external_message(topic, message_str)

    # Should call the synchronous publish method if publish_async is not available:
ock_internal_bus.publish.assert_called_once_with(
    "hsp.external.fact", message_payload
    )
    assert not hasattr(mock_internal_bus, 'publish_async') # Ensure it was indeed deleted for this test