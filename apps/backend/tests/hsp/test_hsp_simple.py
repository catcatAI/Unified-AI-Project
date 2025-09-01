import pytest
import asyncio
pytest_plugins = ('pytest_asyncio',)
import json
from apps.backend.src.hsp.connector import HSPConnector
from .test_hsp_integration import MockMqttBroker # Import MockMqttBroker
from apps.backend.src.hsp.bridge.message_bridge import MessageBridge
from apps.backend.src.hsp.internal.internal_bus import InternalBus
from apps.backend.src.hsp.bridge.data_aligner import DataAligner
from unittest.mock import AsyncMock, patch # Import patch

@pytest.fixture
async def broker():
    mock_broker = MockMqttBroker()
    await mock_broker.start()
    yield mock_broker
    await mock_broker.shutdown()

@pytest.fixture
async def message_bridge(broker, internal_bus, data_aligner):
    # This DummyExternalConnector is not the problem, it's the one used by MessageBridge
    # The problem is how HSPConnector's internal external_connector interacts with MockMqttBroker
    class DummyExternalConnector:
        def __init__(self, mqtt_client):
            self.mqtt_client = mqtt_client
            self.on_message_callback = None

        async def connect(self): pass
        async def disconnect(self): pass
        async def publish(self, topic, payload, qos):
            await self.mqtt_client.publish(topic, payload, qos)

    dummy_external_connector = DummyExternalConnector(broker)
    bridge = MessageBridge(dummy_external_connector, internal_bus, data_aligner)
    return bridge

@pytest.fixture
def internal_bus():
    return InternalBus()

@pytest.fixture
def data_aligner():
    return DataAligner()

@pytest.fixture
async def hsp_connector(broker: MockMqttBroker, internal_bus: InternalBus, data_aligner: DataAligner):
    # Create the HSPConnector in mock mode
    connector = HSPConnector(
        "test_ai",
        "localhost",
        1883,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the real broker to the connector's mock_mqtt_client
        message_bridge=None # Let HSPConnector create its own message bridge
    )

    # Ensure the broker knows about this client and its message handler
    # The on_message_callback of the broker expects (client, userdata, message)
    # The message_bridge.handle_external_message expects (topic, message_bytes)
    # So we need a wrapper.
    async def broker_on_message_wrapper(client, userdata, message):
        await connector.message_bridge.handle_external_message(message.topic, message.payload)
    broker.register_client(connector.ai_id, broker_on_message_wrapper)

    # Patch the external_connector's subscribe method to register with the MockMqttBroker
    async def mock_subscribe_side_effect(topic, callback):
        broker.subscribe_client(connector.ai_id, topic)

    connector.external_connector.subscribe.side_effect = mock_subscribe_side_effect

    await connector.connect()
    yield connector
    await connector.disconnect()

from apps.backend.src.hsp.types import HSPFactPayload
import uuid
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_hsp_connector_init(hsp_connector: HSPConnector):
    assert hsp_connector is not None

@pytest.mark.asyncio
async def test_publish_fact(hsp_connector: HSPConnector, broker: MockMqttBroker, internal_bus: InternalBus):
    received_facts = []
    received_event = asyncio.Event()

    async def fact_handler(message):
        print(f"Fact handler called with: {message}")
        received_facts.append(message['payload'])
        received_event.set()

    # Subscribe to the internal bus topic
    internal_bus.subscribe("hsp.internal.fact", fact_handler)

    fact_payload = HSPFactPayload(
        id=f"fact_{uuid.uuid4().hex}",
        statement_type="natural_language",
        statement_nl="Test fact",
        source_ai_id="test_ai",
        timestamp_created=datetime.now(timezone.utc).isoformat(),
        confidence_score=1.0,
        tags=["test"]
    )

    # Publish the fact using the hsp_connector
    result = await hsp_connector.publish_fact(fact_payload, "hsp/knowledge/facts/test")
    print(f"Publish result: {result}")
    
    # 添加更多调试信息
    print(f"Internal bus subscriptions: {internal_bus.subscriptions}")
    print(f"Internal bus has subscriptions attribute: {hasattr(internal_bus, 'subscriptions')}")
    print(f"Registered callbacks: {hsp_connector._fact_callbacks}")
    
    # 添加发布结果的调试信息
    print(f"Published messages in broker: {broker.get_published_messages()}")

    # Wait until the fact is received or timeout instead of a fixed sleep
    try:
        await asyncio.wait_for(received_event.wait(), timeout=15.0) # 进一步增加超时时间
    except asyncio.TimeoutError:
        print(f"Timeout waiting for fact. Received facts so far: {received_facts}")
        print(f"Published messages in broker: {broker.get_published_messages()}")
        # 添加更多调试信息
        print(f"Internal bus subscriptions at timeout: {internal_bus.subscriptions}")
        print(f"Internal bus has subscriptions attribute at timeout: {hasattr(internal_bus, 'subscriptions')}")
        print(f"Registered callbacks at timeout: {hsp_connector._fact_callbacks}")
        raise

    assert len(received_facts) > 0, "No facts were received"
    assert received_facts[0]["id"] == fact_payload["id"]
