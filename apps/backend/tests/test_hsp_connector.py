import asyncio
import logging
import json
from unittest.mock import AsyncMock, MagicMock
from apps.backend.src.hsp.connector import HSPConnector
from apps.backend.src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters
import pytest

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_mqtt_client():
    """Fixture to provide a MagicMock for gmqtt.Client."""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.subscribe = AsyncMock()
    mock.publish = AsyncMock()
    # 确保publish方法返回一个模拟的结果
    mock.publish.return_value = MagicMock()
    return mock

@pytest.fixture
def hsp_connector_instance(mock_mqtt_client):
    """Fixture to provide an HSPConnector instance in mock mode."""
    connector = HSPConnector(
        ai_id="test_ai",
        broker_address="localhost",
        broker_port=1883,
        mock_mode=True # Enable mock mode for testing without a real broker
    )
    # Manually set the mock client if not in mock_mode, or ensure it's used if in mock_mode
    # In mock mode, HSPConnector.__init__ already sets self.mqtt_client to MagicMock
    # We can replace it with our specific mock_mqtt_client if we need to control its behavior
    connector.mqtt_client = mock_mqtt_client
    # 确保外部连接器也使用相同的mock客户端，并设置subscribe和publish方法
    connector.external_connector.mqtt_client = mock_mqtt_client
    connector.external_connector.subscribe = mock_mqtt_client.subscribe
    connector.external_connector.publish = mock_mqtt_client.publish
    return connector

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_init(hsp_connector_instance):
    """Test basic initialization of the HSPConnector."""
    assert hsp_connector_instance.ai_id == "test_ai"
    assert hsp_connector_instance.broker_address == "localhost"
    assert hsp_connector_instance.broker_port == 1883
    assert hsp_connector_instance.mock_mode is True
    assert hsp_connector_instance.is_connected is True # In mock mode, it's considered connected
    assert hsp_connector_instance.mqtt_client is not None

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_connect_disconnect_mock_mode(hsp_connector_instance, mock_mqtt_client):
    """Test connect and disconnect in mock mode."""
    await hsp_connector_instance.connect()
    mock_mqtt_client.connect.assert_not_called() # Should not call connect in mock mode
    assert hsp_connector_instance.is_connected is True

    await hsp_connector_instance.disconnect()
    mock_mqtt_client.disconnect.assert_not_called() # Should not call disconnect in mock mode
    assert hsp_connector_instance.is_connected is False

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_publish_message(hsp_connector_instance, mock_mqtt_client):
    """Test publishing a generic HSP message."""
    topic = "hsp/test/topic"
    payload: HSPFactPayload = {
        "id": "fact123",
        "statement_type": "natural_language",
        "statement_nl": "The sky is blue.",
        "source_ai_id": "test_ai",
        "timestamp_created": "2024-07-05T12:00:00Z",
        "confidence_score": 0.9
    }
    envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1",
        "message_id": "msg123",
        "correlation_id": None,
        "sender_ai_id": "test_ai",
        "recipient_ai_id": "any_ai",
        "timestamp_sent": "2024-07-05T12:00:00Z",
        "message_type": "HSP::Fact_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "publish",
        "security_parameters": None,
        "qos_parameters": None,
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
        "payload": payload
    }

    await hsp_connector_instance.publish_message(topic, envelope)

    mock_mqtt_client.publish.assert_called_once()
    call_args, call_kwargs = mock_mqtt_client.publish.call_args
    assert call_args[0] == topic
    # Check if the payload is a JSON string representation of the envelope
    published_payload = json.loads(call_args[1])
    assert published_payload == envelope
    assert call_kwargs['qos'] == hsp_connector_instance.default_qos

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_subscribe_and_receive(hsp_connector_instance, mock_mqtt_client):
    """Test subscribing to a topic and simulating message reception."""
    topic = "hsp/test/subscription"
    received_messages = []

    def mock_callback(payload, sender_ai_id, envelope):
        received_messages.append((payload, sender_ai_id, envelope))

    hsp_connector_instance.on_fact_received(mock_callback)

    await hsp_connector_instance.subscribe(topic)
    mock_mqtt_client.subscribe.assert_called_once_with(topic, hsp_connector_instance.default_qos)
    assert topic in hsp_connector_instance.subscribed_topics

    # Simulate an incoming MQTT message
    test_payload: HSPFactPayload = {
        "id": "fact456",
        "statement_type": "natural_language",
        "statement_nl": "It is sunny.",
        "source_ai_id": "another_ai",
        "timestamp_created": "2024-07-05T13:00:00Z",
        "confidence_score": 0.8
    }
    test_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1",
        "message_id": "msg456",
        "correlation_id": None,
        "sender_ai_id": "another_ai",
        "recipient_ai_id": "test_ai",
        "timestamp_sent": "2024-07-05T13:00:00Z",
        "message_type": "HSP::Fact_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "publish",
        "security_parameters": None,
        "qos_parameters": None,
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
        "payload": test_payload
    }

    # Call the on_message handler directly to simulate MQTT client receiving a message
    # The on_message expects client, topic, payload, qos, properties
    # We only care about topic and payload for this test
    mock_mqtt_message = MagicMock()
    mock_mqtt_message.topic = topic.encode('utf-8')
    mock_mqtt_message.payload = json.dumps(test_envelope).encode('utf-8')
    mock_mqtt_message.qos = hsp_connector_instance.default_qos
    mock_mqtt_message.properties = MagicMock()

    await hsp_connector_instance.on_message(
        mock_mqtt_client,
        mock_mqtt_message.topic,
        mock_mqtt_message.payload,
        mock_mqtt_message.qos,
        mock_mqtt_message.properties
    )

    assert len(received_messages) == 1
    received_payload, received_sender, received_envelope = received_messages[0]
    assert received_payload == test_payload
    assert received_sender == test_envelope["sender_ai_id"]
    assert received_envelope == test_envelope

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_ack_sending(hsp_connector_instance, mock_mqtt_client):
    """Test automatic ACK sending for messages requiring acknowledgement."""
    topic = "hsp/test/ack_required"
    test_payload: HSPFactPayload = {
        "id": "fact789",
        "statement_type": "natural_language",
        "statement_nl": "ACK me.",
        "source_ai_id": "requester_ai",
        "timestamp_created": "2024-07-05T14:00:00Z",
        "confidence_score": 0.7
    }
    test_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1",
        "message_id": "msg789",
        "correlation_id": None,
        "sender_ai_id": "requester_ai",
        "recipient_ai_id": "test_ai",
        "timestamp_sent": "2024-07-05T14:00:00Z",
        "message_type": "HSP::Fact_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "publish",
        "security_parameters": None,
        "qos_parameters": {"requires_ack": True, "priority": "medium"},
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
        "payload": test_payload
    }

    # Simulate an incoming MQTT message that requires ACK
    mock_mqtt_message = MagicMock()
    mock_mqtt_message.topic = topic.encode('utf-8')
    mock_mqtt_message.payload = json.dumps(test_envelope).encode('utf-8')
    mock_mqtt_message.qos = hsp_connector_instance.default_qos
    mock_mqtt_message.properties = MagicMock()

    await hsp_connector_instance.on_message(
        mock_mqtt_client,
        mock_mqtt_message.topic,
        mock_mqtt_message.payload,
        mock_mqtt_message.qos,
        mock_mqtt_message.properties
    )

    # Assert that publish was called to send the ACK
    mock_mqtt_client.publish.assert_called_once()
    ack_call_args, ack_call_kwargs = mock_mqtt_client.publish.call_args
    ack_topic = ack_call_args[0]
    ack_payload = json.loads(ack_call_args[1])

    assert ack_topic.startswith("hsp/acks/")
    assert ack_payload["message_type"] == "HSP::Acknowledgement_v0.1"
    assert ack_payload["correlation_id"] == test_envelope["message_id"]
    assert ack_call_kwargs['qos'] == 1 # ACKs use default QoS 1

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_on_connect_callback(hsp_connector_instance):
    """Test that the on_connect callback is properly registered and called."""
    mock_callback = AsyncMock()
    hsp_connector_instance.on_connect_callback(mock_callback)

    # Simulate on_connect being called by the MQTT client
    await hsp_connector_instance.on_connect(None, None, 0, None)
    mock_callback.assert_called_once()

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_on_disconnect_callback(hsp_connector_instance):
    """Test that the on_disconnect callback is properly registered and called."""
    mock_callback = AsyncMock()
    hsp_connector_instance.on_disconnect_callback(mock_callback)

    # Simulate on_disconnect being called by the MQTT client
    await hsp_connector_instance.on_disconnect(None, None, None)
    mock_callback.assert_called_once()

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_hsp_connector_register_specific_callbacks(hsp_connector_instance):
    """Test registering and calling specific message type callbacks."""
    fact_callback = AsyncMock()
    command_callback = AsyncMock()

    hsp_connector_instance.on_fact_received(fact_callback)
    hsp_connector_instance.on_command_received(command_callback)

    # Simulate a fact message
    fact_payload: HSPFactPayload = {
        "id": "fact999",
        "statement_type": "natural_language",
        "statement_nl": "This is a fact.",
        "source_ai_id": "source_ai",
        "timestamp_created": "2024-07-05T15:00:00Z",
        "confidence_score": 0.95
    }
    fact_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1",
        "message_id": "msg999",
        "correlation_id": None,
        "sender_ai_id": "source_ai",
        "recipient_ai_id": "test_ai",
        "timestamp_sent": "2024-07-05T15:00:00Z",
        "message_type": "HSP::Fact_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "publish",
        "security_parameters": None,
        "qos_parameters": None,
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
        "payload": fact_payload
    }

    mock_mqtt_message_fact = MagicMock()
    mock_mqtt_message_fact.topic = "hsp/fact/test".encode('utf-8')
    mock_mqtt_message_fact.payload = json.dumps(fact_envelope).encode('utf-8')
    mock_mqtt_message_fact.qos = 0
    mock_mqtt_message_fact.properties = MagicMock()

    await hsp_connector_instance.on_message(
        MagicMock(),
        mock_mqtt_message_fact.topic,
        mock_mqtt_message_fact.payload,
        mock_mqtt_message_fact.qos,
        mock_mqtt_message_fact.properties
    )
    fact_callback.assert_called_once_with(fact_payload, fact_envelope["sender_ai_id"], fact_envelope)
    command_callback.assert_not_called()

    # Simulate a command message
    command_payload = {
        "command": "do_something",
        "parameters": {"param1": "value1"}
    }