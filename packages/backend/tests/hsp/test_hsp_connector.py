import pytest
import asyncio
import logging
import json
from unittest.mock import MagicMock, AsyncMock
from src.hsp.connector import HSPConnector
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters

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
    return mock

@pytest.fixture
def hsp_connector_instance(mock_mqtt_client):
    """Fixture to provide an HSPConnector instance in mock mode."""
    connector = HSPConnector(
        ai_id="test_ai",
        broker_address="localhost",
        broker_port=1883,
        mock_mode=True, # Enable mock mode for testing without a real broker
        mock_mqtt_client=mock_mqtt_client
    )
    connector.external_connector.publish = mock_mqtt_client.publish
    return connector

@pytest.mark.asyncio
async def test_hsp_connector_init(hsp_connector_instance):
    """Test basic initialization of the HSPConnector."""
    assert hsp_connector_instance.ai_id == "test_ai"
    assert hsp_connector_instance.broker_address == "localhost"
    assert hsp_connector_instance.broker_port == 1883
    assert hsp_connector_instance.mock_mode is True
    assert hsp_connector_instance.is_connected is True # In mock mode, it's considered connected
    

@pytest.mark.asyncio
async def test_hsp_connector_connect_disconnect_mock_mode(hsp_connector_instance, mock_mqtt_client):
    """Test connect and disconnect in mock mode."""
    await hsp_connector_instance.connect()
    mock_mqtt_client.connect.assert_not_called() # Should not call connect in mock mode
    assert hsp_connector_instance.is_connected is True

    await hsp_connector_instance.disconnect()
    mock_mqtt_client.disconnect.assert_not_called() # Should not call disconnect in mock mode
    assert hsp_connector_instance.is_connected is False

@pytest.mark.asyncio
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

    hsp_connector_instance.external_connector.mqtt_client.publish.assert_called_with(topic, json.dumps(envelope).encode('utf-8'), qos=1)

@pytest.mark.asyncio
async def test_hsp_connector_subscribe_and_receive(hsp_connector_instance, mock_mqtt_client):
    """Test subscribing to a topic and simulating message reception."""
    topic = "hsp/test/subscription"
    received_messages = []

    async def mock_callback(payload, sender_ai_id, envelope):
        received_messages.append((payload, sender_ai_id, envelope))

    hsp_connector_instance.register_on_fact_callback(mock_callback)

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

    await hsp_connector_instance.external_connector.on_message_callback(
        mock_mqtt_message.topic.decode('utf-8'),
        mock_mqtt_message.payload.decode('utf-8')
    )
    await asyncio.sleep(0.5) # Allow async tasks to complete

    assert len(received_messages) == 1
    received_payload, received_sender_ai_id, received_envelope = received_messages[0]
    assert received_payload == test_payload
    assert received_sender_ai_id == test_envelope["sender_ai_id"]
    assert received_envelope == test_envelope

@pytest.mark.asyncio
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

    await hsp_connector_instance.external_connector.on_message_callback(
        mock_mqtt_message.topic.decode('utf-8'),
        mock_mqtt_message.payload.decode('utf-8')
    )
    await asyncio.sleep(0.5) # Allow async tasks to complete

    # Assert that an ACK message was published via the external connector's mqtt_client.publish
    hsp_connector_instance.external_connector.mqtt_client.publish.assert_called_once()
    publish_call_args, publish_call_kwargs = hsp_connector_instance.external_connector.mqtt_client.publish.call_args

    # Check ACK topic convention
    expected_ack_topic = f"hsp/acks/{test_envelope['sender_ai_id']}"
    assert publish_call_args[0] == expected_ack_topic

    # Check ACK payload content
    ack_payload = json.loads(publish_call_args[1].decode('utf-8')) # Decode bytes payload
    assert ack_payload['payload']['status'] == "received"
    assert ack_payload['payload']['ack_timestamp'] is not None
    assert ack_payload['payload']['target_message_id'] == test_envelope['message_id']
    assert ack_payload['message_type'] == "HSP::Acknowledgement_v0.1"
    assert ack_payload['sender_ai_id'] == hsp_connector_instance.ai_id
    assert ack_payload['recipient_ai_id'] == test_envelope['sender_ai_id']
    assert publish_call_kwargs['qos'] == 1 # Default QoS for ACKs

@pytest.mark.asyncio
async def test_hsp_connector_on_connect_callback(hsp_connector_instance, mock_mqtt_client):
    """Test that external on_connect callback is called."""
    mock_external_callback = AsyncMock()
    hsp_connector_instance.register_on_connect_callback(mock_external_callback)

    # Simulate on_connect being called by gmqtt client
    await hsp_connector_instance.connect()
    await asyncio.sleep(0.1) # Give a moment for the task to run

    mock_external_callback.assert_called_once()

@pytest.mark.asyncio
async def test_hsp_connector_on_disconnect_callback(hsp_connector_instance, mock_mqtt_client):
    """Test that external on_disconnect callback is called."""
    mock_external_callback = AsyncMock()
    hsp_connector_instance.register_on_disconnect_callback(mock_external_callback)

    # Simulate on_disconnect being called by gmqtt client
    await hsp_connector_instance.disconnect()
    await asyncio.sleep(0.1) # Give a moment for the task to run

    mock_external_callback.assert_called_once()

@pytest.mark.asyncio
async def test_hsp_connector_register_specific_callbacks(hsp_connector_instance):
    """Test registering and triggering specific message type callbacks."""
    mock_fact_callback = AsyncMock()
    mock_capability_callback = AsyncMock()
    mock_task_request_callback = AsyncMock()
    mock_task_result_callback = AsyncMock()

    hsp_connector_instance.register_on_fact_callback(mock_fact_callback)
    hsp_connector_instance.register_on_capability_advertisement_callback(mock_capability_callback)
    hsp_connector_instance.register_on_task_request_callback(mock_task_request_callback)
    hsp_connector_instance.register_on_task_result_callback(mock_task_result_callback)

    # Simulate a Fact message
    fact_payload: HSPFactPayload = {
        "id": "fact_test", "statement_type": "natural_language",
        "statement_nl": "Test fact.", "source_ai_id": "ai_x",
        "timestamp_created": "2024-07-05T15:00:00Z", "confidence_score": 1.0
    }
    fact_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg_fact",
        "correlation_id": None, "sender_ai_id": "ai_x",
        "recipient_ai_id": "test_ai", "timestamp_sent": "2024-07-05T15:00:00Z",
        "message_type": "HSP::Fact_v0.1", "protocol_version": "0.1",
        "communication_pattern": "publish", "security_parameters": None,
        "qos_parameters": None, "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Fact/0.1", "payload": fact_payload
    }
    mock_mqtt_message_fact = MagicMock()
    mock_mqtt_message_fact.topic = b"hsp/facts"
    mock_mqtt_message_fact.payload = json.dumps(fact_envelope).encode('utf-8')
    mock_mqtt_message_fact.qos = 1
    mock_mqtt_message_fact.properties = MagicMock()

    await hsp_connector_instance.external_connector.on_message_callback(mock_mqtt_message_fact.topic.decode('utf-8'), mock_mqtt_message_fact.payload.decode('utf-8'))
    await asyncio.sleep(0.5) # Allow async tasks to complete
    mock_fact_callback.assert_called_once_with(fact_payload, fact_envelope["sender_ai_id"], fact_envelope)
    mock_capability_callback.assert_not_called()
    mock_task_request_callback.assert_not_called()
    mock_task_result_callback.assert_not_called()

@pytest.mark.asyncio
async def test_hsp_connector_fallback_mechanism(hsp_connector_instance, mock_mqtt_client):
    """
    Tests that the HSPConnector correctly uses the fallback mechanism when
    the primary MQTT publish fails.
    """
    # Arrange
    connector = hsp_connector_instance
    topic = "hsp/test/fallback"
    envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg_fallback", "sender_ai_id": "test_ai",
        "recipient_ai_id": "any_ai", "timestamp_sent": "2024-07-05T19:00:00Z",
        "message_type": "HSP::Fact_v0.1", "protocol_version": "0.1",
        "communication_pattern": "publish", "payload": {"id": "fact_fallback"},
        "correlation_id": None, "security_parameters": None, "qos_parameters": None,
        "routing_info": None, "payload_schema_uri": None
    }

    # Simulate a failure in the primary publish method
    connector.external_connector.publish = AsyncMock(side_effect=Exception("MQTT Broker is down"))

    # Mock the fallback manager and its send method
    mock_fallback_manager = MagicMock()
    mock_fallback_manager.send_message = AsyncMock(return_value=True)
    connector.fallback_manager = mock_fallback_manager
    connector.enable_fallback = True

    # Act
    success = await connector.publish_message(topic, envelope)

    # Assert
    assert success is True

    # Verify that the primary publish method was called
    connector.external_connector.publish.assert_awaited_once_with(topic, json.dumps(envelope).encode('utf-8'), qos=1)

    # Verify that the fallback manager's send_message was called as a result of the failure
    mock_fallback_manager.send_message.assert_awaited_once()

    # Check the details of the message passed to the fallback manager
    fallback_call_args = mock_fallback_manager.send_message.call_args[0]
    fallback_message = fallback_call_args[3] # The payload is the 4th argument
    assert fallback_message['topic'] == topic
    assert fallback_message['envelope'] == envelope

    # Reset mocks for next test
    mock_fact_callback.reset_mock()

    # Simulate a CapabilityAdvertisement message
    cap_payload = {
        "capability_id": "cap_test", "ai_id": "ai_y", "name": "Test Cap",
        "description": "Desc", "version": "1.0", "availability_status": "online"
    }
    cap_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg_cap",
        "correlation_id": None, "sender_ai_id": "ai_y",
        "recipient_ai_id": "test_ai", "timestamp_sent": "2024-07-05T16:00:00Z",
        "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1",
        "communication_pattern": "publish", "security_parameters": None,
        "qos_parameters": None, "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/CapabilityAdvertisement/0.1", "payload": cap_payload
    }
    mock_mqtt_message_cap = MagicMock()
    mock_mqtt_message_cap.topic = b"hsp/capabilities"
    mock_mqtt_message_cap.payload = json.dumps(cap_envelope).encode('utf-8')
    mock_mqtt_message_cap.qos = 1
    mock_mqtt_message_cap.properties = MagicMock()

    await hsp_connector_instance.external_connector.on_message_callback(mock_mqtt_message_cap.topic.decode('utf-8'), mock_mqtt_message_cap.payload.decode('utf-8'))
    await asyncio.sleep(0.5) # Allow async tasks to complete
    mock_capability_callback.assert_called_once_with(cap_payload, cap_envelope["sender_ai_id"], cap_envelope)
    mock_fact_callback.assert_not_called()
    mock_task_request_callback.assert_not_called()
    mock_task_result_callback.assert_not_called()

    # Reset mocks for next test
    mock_capability_callback.reset_mock()

    # Simulate a TaskRequest message
    task_req_payload = {
        "request_id": "req_test", "requester_ai_id": "ai_z",
        "parameters": {"input": "data"}
    }
    task_req_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg_req",
        "correlation_id": None, "sender_ai_id": "ai_z",
        "recipient_ai_id": "test_ai", "timestamp_sent": "2024-07-05T17:00:00Z",
        "message_type": "HSP::TaskRequest_v0.1", "protocol_version": "0.1",
        "communication_pattern": "request", "security_parameters": None,
        "qos_parameters": None, "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/TaskRequest/0.1", "payload": task_req_payload
    }
    mock_mqtt_message_req = MagicMock()
    mock_mqtt_message_req.topic = b"hsp/tasks/requests"
    mock_mqtt_message_req.payload = json.dumps(task_req_envelope).encode('utf-8')
    mock_mqtt_message_req.qos = 1
    mock_mqtt_message_req.properties = MagicMock()

    await hsp_connector_instance.external_connector.on_message_callback(mock_mqtt_message_req.topic.decode('utf-8'), mock_mqtt_message_req.payload.decode('utf-8'))
    await asyncio.sleep(0.5) # Allow async tasks to complete
    mock_task_request_callback.assert_called_once_with(task_req_payload, task_req_envelope["sender_ai_id"], task_req_envelope)
    mock_fact_callback.assert_not_called()
    mock_capability_callback.assert_not_called()
    mock_task_result_callback.assert_not_called()

    # Reset mocks for next test
    mock_task_request_callback.reset_mock()

    # Simulate a TaskResult message
    task_res_payload = {
        "result_id": "res_test", "request_id": "req_test",
        "executing_ai_id": "ai_alpha", "status": "success",
        "payload": {"output": "result"}
    }
    task_res_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg_res",
        "correlation_id": "req_test", "sender_ai_id": "ai_alpha",
        "recipient_ai_id": "test_ai", "timestamp_sent": "2024-07-05T18:00:00Z",
        "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1",
        "communication_pattern": "response", "security_parameters": None,
        "qos_parameters": None, "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/TaskResult/0.1", "payload": task_res_payload
    }
    mock_mqtt_message_res = MagicMock()
    mock_mqtt_message_res.topic = b"hsp/tasks/results"
    mock_mqtt_message_res.payload = json.dumps(task_res_envelope).encode('utf-8')
    mock_mqtt_message_res.qos = 1
    mock_mqtt_message_res.properties = MagicMock()

    await hsp_connector_instance.external_connector.on_message_callback(mock_mqtt_message_res.topic.decode('utf-8'), mock_mqtt_message_res.payload.decode('utf-8'))
    await asyncio.sleep(0.5) # Allow async tasks to complete
    mock_task_result_callback.assert_called_once_with(task_res_payload, task_res_envelope["sender_ai_id"], task_res_envelope)
    mock_fact_callback.assert_not_called()
    mock_capability_callback.assert_not_called()
    mock_task_request_callback.assert_not_called()
