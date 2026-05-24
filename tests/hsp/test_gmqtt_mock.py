from unittest.mock import AsyncMock

import pytest


class MockGmqttClient:
    def __init__(self) -> None:
        self.publish = AsyncMock()
async def test_gmqtt_publish_mock() -> None:
    client = MockGmqttClient()
    topic = "test/topic"
    payload = b"test_payload"
    qos = 1

    await client.publish(topic, payload, qos=qos)
    client.publish.assert_called_once_with(topic, payload, qos=qos)
