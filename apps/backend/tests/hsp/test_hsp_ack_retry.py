import pytest
import asyncio
import logging
import json
from unittest.mock import MagicMock, AsyncMock
from src.hsp.connector import HSPConnector
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters, HSPAcknowledgementPayload
from datetime import datetime, timezone
import uuid

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
def mock_fallback_manager():
    """Fixture to provide a MagicMock for FallbackManager."""
    mock = MagicMock()
    mock.send_message = AsyncMock(return_value=True)
    mock.initialize = AsyncMock(return_value=True)
    mock.start = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.get_status = MagicMock(return_value={"active_protocol": "mock_protocol"})
    return mock

@pytest.fixture
def hsp_connector_instance(mock_mqtt_client, mock_fallback_manager):
    """Fixture to provide an HSPConnector instance in mock mode."""
    connector = HSPConnector(
        ai_id="test_ai",
        broker_address="localhost",
        broker_port=1883,
        mock_mode=True, # Enable mock mode for testing without a real broker
        mock_mqtt_client=mock_mqtt_client,
        enable_fallback=True # Ensure fallback is enabled for testing
    )
    # Manually set the mock fallback manager
    connector.fallback_manager = mock_fallback_manager
    connector.fallback_initialized = True # Assume it's initialized for tests
    
    # Force enable fallback for tests (override mock mode disable)
    connector.enable_fallback = True

    # Ensure the mock publish is used
    connector.external_connector.publish = mock_mqtt_client.publish
    return connector

# Helper to create a message envelope that requires ACK
def create_ack_required_envelope(message_id: str, correlation_id: str) -> HSPMessageEnvelope:
    return { #type: ignore
        "hsp_envelope_version": "0.1",
        "message_id": message_id,
        "correlation_id": correlation_id,
        "sender_ai_id": "test_ai",
        "recipient_ai_id": "target_ai",
        "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::Test_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "request",
        "security_parameters": None,
        "qos_parameters": {"requires_ack": True, "priority": "high"},
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Test/0.1",
        "payload": {"test_data": "some_value"}
    }

# Helper to simulate an incoming ACK message
async def simulate_incoming_ack(connector: HSPConnector, target_message_id: str, correlation_id: str, sender_ai_id: str = "target_ai"):
    ack_payload: HSPAcknowledgementPayload = {
        "status": "received",
        "ack_timestamp": datetime.now(timezone.utc).isoformat(),
        "target_message_id": target_message_id
    }
    ack_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1",
        "message_id": str(uuid.uuid4()),
        "correlation_id": correlation_id,
        "sender_ai_id": sender_ai_id,
        "recipient_ai_id": connector.ai_id,
        "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::Acknowledgement_v0.1",
        "protocol_version": "0.1",
        "communication_pattern": "acknowledgement",
        "security_parameters": None,
        "qos_parameters": {"requires_ack": False, "priority": "low"},
        "routing_info": None,
        "payload_schema_uri": "hsp:schema:payload/Acknowledgement/0.1",
        "payload": ack_payload
    }
    # Call the internal dispatch method directly
    await connector._dispatch_acknowledgement_to_callbacks(ack_envelope)

@pytest.mark.asyncio
async def test_scenario_1_successful_ack(hsp_connector_instance, mock_mqtt_client):
    logger.info("\n--- Test Scenario 1: Successful ACK (Happy Path) ---")
    connector = hsp_connector_instance
    msg_id = "msg1"
    corr_id = "corr1"
    envelope = create_ack_required_envelope(msg_id, corr_id)

    # Simulate immediate ACK after publish
    async def mock_publish_side_effect(*args, **kwargs):
        # Allow the publish to proceed, then schedule ACK to be sent shortly after
        asyncio.create_task(simulate_incoming_ack(connector, msg_id, corr_id))
        return True
    mock_mqtt_client.publish.side_effect = mock_publish_side_effect

    result = await connector.publish_message("hsp/test", envelope)

    assert result is True
    mock_mqtt_client.publish.assert_called_once()
    assert connector._message_retry_counts.get(corr_id) is None # Should be cleared

@pytest.mark.asyncio
async def test_scenario_2_delayed_ack(hsp_connector_instance, mock_mqtt_client):
    logger.info("\n--- Test Scenario 2: Delayed ACK ---")
    connector = hsp_connector_instance
    connector.ack_timeout_sec = 0.5 # Short timeout for testing
    msg_id = "msg2"
    corr_id = "corr2"
    envelope = create_ack_required_envelope(msg_id, corr_id)

    # Simulate ACK after first retry
    # In mock mode, we need to schedule the ACK to arrive after the timeout
    # but before the retry loop completes
    async def delayed_ack():
        await asyncio.sleep(0.6)  # Wait for timeout + a bit more
        await simulate_incoming_ack(connector, msg_id, corr_id)
    
    # Start the delayed ACK task
    ack_task = asyncio.create_task(delayed_ack())
    
    try:
        result = await connector.publish_message("hsp/test", envelope)
        
        # The ACK should arrive during retry, so the result should be True
        assert result is True
        # In mock mode, publish is called once initially, then during retries
        assert mock_mqtt_client.publish.call_count >= 2  # Initial + at least one retry
        assert connector._message_retry_counts.get(corr_id) is None  # Should be cleared
    finally:
        # Cancel the ACK task if it's still running
        if not ack_task.done():
            ack_task.cancel()
            try:
                await ack_task
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_scenario_3_no_ack_max_retries(hsp_connector_instance, mock_mqtt_client):
    logger.info("\n--- Test Scenario 3: No ACK (Max Retries Exceeded) ---")
    connector = hsp_connector_instance
    connector.ack_timeout_sec = 0.5 # Short timeout
    connector.max_ack_retries = 2 # Max 2 retries for testing
    
    # Disable fallback for this test to test pure ACK retry failure
    connector.enable_fallback = False
    
    msg_id = "msg3"
    corr_id = "corr3"
    envelope = create_ack_required_envelope(msg_id, corr_id)

    # Simulate no ACK ever
    mock_mqtt_client.publish.return_value = True # Publish always succeeds, but no ACK comes

    result = await connector.publish_message("hsp/test", envelope)

    assert result is False
    assert mock_mqtt_client.publish.call_count == (connector.max_ack_retries + 1) # Initial + retries
    assert connector._message_retry_counts.get(corr_id) is None # Should be cleared

@pytest.mark.asyncio
async def test_scenario_4_hsp_unavailable_fallback_success(hsp_connector_instance, mock_mqtt_client, mock_fallback_manager):
    logger.info("\n--- Test Scenario 4: HSP Unavailable, Fallback Success ---")
    connector = hsp_connector_instance
    msg_id = "msg4"
    corr_id = "corr4"
    envelope = create_ack_required_envelope(msg_id, corr_id) # ACK required for full test

    # Simulate HSP publish failure
    mock_mqtt_client.publish.side_effect = Exception("HSP connection error")
    connector.hsp_available = True # Start as available, but it will fail

    # Fallback manager succeeds
    mock_fallback_manager.send_message.return_value = True

    result = await connector.publish_message("hsp/test", envelope)

    assert result is True
    mock_mqtt_client.publish.assert_called_once() # Only one attempt via HSP
    mock_fallback_manager.send_message.assert_called_once()
    assert connector._message_retry_counts.get(corr_id) is None # Should be cleared

@pytest.mark.asyncio
async def test_scenario_5_hsp_unavailable_fallback_failure(hsp_connector_instance, mock_mqtt_client, mock_fallback_manager):
    logger.info("\n--- Test Scenario 5: HSP Unavailable, Fallback Failure ---")
    connector = hsp_connector_instance
    connector.max_ack_retries = 1 # Short retries for testing
    msg_id = "msg5"
    corr_id = "corr5"
    envelope = create_ack_required_envelope(msg_id, corr_id)

    # Simulate HSP publish failure
    mock_mqtt_client.publish.side_effect = Exception("HSP connection error")
    connector.hsp_available = True

    # Fallback manager also fails
    mock_fallback_manager.send_message.return_value = False

    result = await connector.publish_message("hsp/test", envelope)

    assert result is False
    # When HSP publish fails, we try fallback once immediately
    assert mock_mqtt_client.publish.call_count == 1 # Only one attempt via HSP
    assert mock_fallback_manager.send_message.call_count == 1 # One fallback attempt
    assert connector._message_retry_counts.get(corr_id) is None # Should be cleared