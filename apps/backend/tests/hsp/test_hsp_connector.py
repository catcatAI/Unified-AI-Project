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

    # Verify that the primary publish method was called
    mock_mqtt_client.publish.assert_awaited_once_with(topic, json.dumps(envelope).encode('utf-8'), qos=1)

    # Setup mock callbacks
    mock_fact_callback = AsyncMock()
    mock_capability_callback = AsyncMock()
    mock_task_request_callback = AsyncMock()
    mock_task_result_callback = AsyncMock()

    hsp_connector_instance.register_on_fact_callback(mock_fact_callback)
    hsp_connector_instance.register_on_capability_advertisement_callback(mock_capability_callback)
    hsp_connector_instance.register_on_task_request_callback(mock_task_request_callback)
    hsp_connector_instance.register_on_task_result_callback(mock_task_result_callback)

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
    # Use a more robust waiting mechanism if needed, for now, a small sleep is sufficient for mock callbacks
    # In a real scenario, you might wait for a specific event or a mock's call_count to increase
    await asyncio.sleep(0.01) # Allow async tasks to complete
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
    # Use a more robust waiting mechanism if needed, for now, a small sleep is sufficient for mock callbacks
    await asyncio.sleep(0.01) # Allow async tasks to complete
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
    # Use a more robust waiting mechanism if needed, for now, a small sleep is sufficient for mock callbacks
    await asyncio.sleep(0.01) # Allow async tasks to complete
    mock_task_result_callback.assert_called_once_with(task_res_payload, task_res_envelope["sender_ai_id"], task_res_envelope)
    mock_fact_callback.assert_not_called()
    mock_capability_callback.assert_not_called()
    mock_task_request_callback.assert_not_called()
