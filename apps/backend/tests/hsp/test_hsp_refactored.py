"""import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.hsp.external.external_connector import ExternalConnector
from src.hsp.internal.internal_bus import InternalBus
from src.hsp.bridge.data_aligner import DataAligner
from src.hsp.bridge.message_bridge import MessageBridge

@pytest.fixture
def mock_external_connector():
    return AsyncMock(spec=ExternalConnector)

@pytest.fixture
def internal_bus():
    return InternalBus()

@pytest.fixture
def data_aligner():
    return DataAligner()

@pytest.fixture
def message_bridge(mock_external_connector, internal_bus, data_aligner):
    return MessageBridge(mock_external_connector, internal_bus, data_aligner)

@pytest.mark.asyncio
async def test_message_bridge_external_to_internal(message_bridge, internal_bus):
    test_topic = "test/topic"
    test_message = '{"id": "123"}'
    callback = MagicMock()
    internal_bus.subscribe(f"hsp.external.{test_topic}", callback)

    await message_bridge.handle_external_message(test_topic, test_message)

    callback.assert_called_once_with({"id": "123"})

@pytest.mark.asyncio
async def test_message_bridge_internal_to_external(message_bridge, mock_external_connector):
    test_topic = "test/topic"
    test_message = {"id": "123"}

    message_bridge.handle_internal_message({"topic": test_topic, "payload": test_message})

    mock_external_connector.publish.assert_called_once_with(test_topic, test_message)
"""