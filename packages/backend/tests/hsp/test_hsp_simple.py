import pytest
import asyncio
pytest_plugins = ('pytest_asyncio',)
import json
from src.hsp.connector import HSPConnector
from tests.hsp.test_hsp_integration import MockMqttBroker
from src.hsp.bridge.message_bridge import MessageBridge
from src.hsp.internal.internal_bus import InternalBus
from src.hsp.bridge.data_aligner import DataAligner

@pytest.fixture
async def broker():
    mock_broker = MockMqttBroker()
    await mock_broker.start()
    yield mock_broker
    await mock_broker.shutdown()

@pytest.fixture
async def message_bridge(broker, internal_bus, data_aligner):
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
async def hsp_connector(broker, internal_bus, data_aligner):
    class DummyExternalConnector:
        def __init__(self, mqtt_client):
            self.mqtt_client = mqtt_client
            self.on_message_callback = None

        async def connect(self): pass
        async def disconnect(self): pass
        async def publish(self, topic, payload, qos):
            await self.mqtt_client.publish(topic, payload, qos)

    dummy_external_connector = DummyExternalConnector(broker)
    message_bridge = MessageBridge(dummy_external_connector, internal_bus, data_aligner)
    connector = HSPConnector(
        "test_ai",
        "localhost",
        1883,
        mock_mode=True,
        mock_mqtt_client=broker,
        
        message_bridge=message_bridge
    )
    await connector.connect()
    yield connector
    await connector.disconnect()

from src.hsp.types import HSPFactPayload
import uuid
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_hsp_connector_init(hsp_connector: HSPConnector):
    assert hsp_connector is not None

@pytest.mark.asyncio
async def test_publish_fact(hsp_connector: HSPConnector, broker: MockMqttBroker, internal_bus: InternalBus):
    received_facts = []

    async def fact_handler(message):
        print(f"Fact handler called with: {message}")
        received_facts.append(message['payload'])

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
    await hsp_connector.publish_fact(fact_payload, "hsp/knowledge/facts/test")

    await asyncio.sleep(0.2)

    assert len(received_facts) > 0, "No facts were received"
    assert received_facts[0]["id"] == fact_payload["id"]
