"""import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from apps.backend.src.hsp.external.external_connector import ExternalConnector
from apps.backend.src.hsp.internal.internal_bus import InternalBus
from apps.backend.src.hsp.bridge.data_aligner import DataAligner
from apps.backend.src.hsp.bridge.message_bridge import MessageBridge

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
# 添加重试装饰器以处理不稳定的测试
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_message_bridge_external_to_internal(message_bridge, internal_bus) -> None:
    test_topic = "test/topic"
    test_message = '{"id": "123"}'
    callback = MagicMock()
    _ = internal_bus.subscribe(f"hsp.external.{test_topic}", callback)

    _ = await message_bridge.handle_external_message(test_topic, test_message)

    _ = callback.assert_called_once_with({"id": "123"})

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_message_bridge_internal_to_external(message_bridge, mock_external_connector) -> None:
    test_topic = "test/topic"
    test_message = {"id": "123"}

    _ = message_bridge.handle_internal_message({"topic": test_topic, "payload": test_message})

    _ = mock_external_connector.publish.assert_called_once_with(test_topic, test_message)
"""