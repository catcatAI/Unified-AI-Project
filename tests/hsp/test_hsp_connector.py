import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import gmqtt.client as gmqtt # Import for type hinting if needed, but we'll mock it.
import logging # Import logging for caplog.set_level
import json
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional # For type hint in test_ack_payload_and_envelope_construction

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPMessageEnvelope

TEST_AI_ID = "test_ai_connector_001"
TEST_BROKER_ADDRESS = "localhost"
TEST_BROKER_PORT = 1884

@pytest.fixture
def mock_gmqtt_client():
    """Fixture to create a MagicMock for the gmqtt.Client."""
    mock_client = MagicMock(spec=gmqtt.Client)
    # Set default return values for methods that might be called indirectly
    mock_client.connect = AsyncMock(return_value=None) # gmqtt uses async/await
    mock_client.subscribe = AsyncMock(return_value=None)
    mock_client.unsubscribe = AsyncMock(return_value=None)
    mock_client.publish = AsyncMock(return_value=None)
    mock_client.disconnect = AsyncMock(return_value=None)
    # Add reconnection properties
    mock_client.RECONNECT_RETRIES = -1
    mock_client.RECONNECT_DELAY = 1
    return mock_client

@pytest.fixture
def connector_with_mock_client(mock_gmqtt_client: MagicMock):
    """Fixture to create an HSPConnector instance with a mocked gmqtt.Client."""
    with patch('gmqtt.Client', return_value=mock_gmqtt_client):
        connector = HSPConnector(
            ai_id=TEST_AI_ID,
            broker_address=TEST_BROKER_ADDRESS,
            broker_port=TEST_BROKER_PORT,
            reconnect_min_delay=1,
            reconnect_max_delay=5
        )
        # Assign the mock client directly for easier access in tests if needed,
        # though HSPConnector already stores it as self.mqtt_client
        connector.mqtt_client = mock_gmqtt_client
        # Set mock_mode to True to avoid actual connection attempts
        connector.mock_mode = True
        return connector

class TestHSPConnectorConnectionLogic:

    @pytest.mark.timeout(10)
    async def test_initial_connection_logging(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector") # Ensure INFO logs are captured for this logger
        connector = connector_with_mock_client
        assert not connector._was_unexpectedly_disconnected

        # Simulate gmqtt calling on_connect after a successful physical connection
        await connector.on_connect(mock_gmqtt_client, None)

        assert connector.is_connected
        assert not connector._was_unexpectedly_disconnected
        assert f"HSPConnector ({TEST_AI_ID}): Successfully connected to MQTT Broker" in caplog.text
        assert "reconnected" not in caplog.text # Ensure it says "connected", not "reconnected"

    @pytest.mark.timeout(10)
    async def test_unexpected_disconnection_flag_and_logging(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector") # Capture INFO and WARNING (default for warning is already on)
        connector = connector_with_mock_client
        connector.is_connected = True # Assume it was connected
        connector._was_unexpectedly_disconnected = False

        # Simulate gmqtt calling on_disconnect due to an error
        await connector.on_disconnect(mock_gmqtt_client, None, 1) # 1 indicates an error

        assert not connector.is_connected
        assert connector._was_unexpectedly_disconnected
        assert f"HSPConnector ({TEST_AI_ID}): Unexpectedly disconnected from MQTT Broker (reason code 1)" in caplog.text
        assert "Client will attempt to reconnect automatically" in caplog.text

    @pytest.mark.timeout(10)
    async def test_clean_disconnection_flag_reset_and_logging(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector")
        connector = connector_with_mock_client
        connector.is_connected = True
        connector._was_unexpectedly_disconnected = True # Simulate previous unexpected disconnect

        # Simulate gmqtt calling on_disconnect for a clean disconnect (e.g., client called disconnect())
        await connector.on_disconnect(mock_gmqtt_client, None, 0) # 0 indicates success

        assert not connector.is_connected
        assert not connector._was_unexpectedly_disconnected # Should be reset
        assert f"HSPConnector ({TEST_AI_ID}): Cleanly disconnected from MQTT Broker (reason code 0)" in caplog.text

    @pytest.mark.timeout(10)
    async def test_reconnection_logging_and_flag_reset(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector")
        connector = connector_with_mock_client
        connector.is_connected = False # Simulate it's currently disconnected
        connector._was_unexpectedly_disconnected = True # Simulate it was due to an unexpected event

        # Simulate gmqtt calling on_connect after a successful physical RE-connection
        await connector.on_connect(mock_gmqtt_client, None)

        assert connector.is_connected
        assert not connector._was_unexpectedly_disconnected # Should be reset
        assert f"HSPConnector ({TEST_AI_ID}): Successfully reconnected to MQTT Broker" in caplog.text

    @pytest.mark.timeout(10)
    async def test_failed_connection_attempt_logging(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock, caplog):
        connector = connector_with_mock_client
        connector.is_connected = False
        initial_unexpected_flag_state = True # Say it was previously disconnected unexpectedly
        connector._was_unexpectedly_disconnected = initial_unexpected_flag_state

        # Store the original connect method and mock_mode state
        original_connect = mock_gmqtt_client.connect
        original_mock_mode = connector.mock_mode
        # Simulate gmqtt connection failure by raising an exception
        mock_gmqtt_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        # Temporarily disable mock_mode to test actual connection behavior
        connector.mock_mode = False

        try:
            await connector.connect()
        except Exception:
            pass
        finally:
            # Restore the original connect method and mock_mode
            mock_gmqtt_client.connect = original_connect
            connector.mock_mode = original_mock_mode

        assert not connector.is_connected
        # Flag should not change because this is a failed *connect* attempt, not a new *disconnect* event
        assert connector._was_unexpectedly_disconnected == initial_unexpected_flag_state
        assert f"HSPConnector ({TEST_AI_ID}): Failed to connect to any of the provided MQTT brokers." in caplog.text

    @pytest.mark.timeout(10)
    async def test_resubscription_on_connect(self, connector_with_mock_client: HSPConnector, mock_gmqtt_client: MagicMock):
        connector = connector_with_mock_client
        # Temporarily disable mock_mode to test actual resubscription behavior
        connector.mock_mode = False

        topics_to_subscribe = ["test/topic/1", "another/test/topic", "hsp/general"]
        for topic in topics_to_subscribe:
            # Manually add to subscribed_topics, as .subscribe() would call the mock client's subscribe
            # which we want to check after on_connect is called.
            # In a real scenario, connector.subscribe(topic) would be called by user code.
            # Here, we're testing on_connect's behavior given that self.subscribed_topics is populated.
            connector.subscribed_topics.add(topic)

        # Reset call count for the specific mock we are interested in
        mock_gmqtt_client.subscribe.reset_mock()

        # Simulate gmqtt calling on_connect after a successful physical connection
        await connector.on_connect(mock_gmqtt_client, None)

        assert connector.is_connected
        assert mock_gmqtt_client.subscribe.call_count == len(topics_to_subscribe)

        # Verify that subscribe was called for each topic
        # The actual call to connector.subscribe() inside on_connect then calls mock_gmqtt_client.subscribe()
        # So we check the calls to the gmqtt client's subscribe method.
        called_topics = set()
        for call_args in mock_gmqtt_client.subscribe.call_args_list:
            args, kwargs = call_args
            called_topics.add(args[0]) # topic is the first positional argument
            assert kwargs.get('qos') == connector.default_qos # Check if default QoS was used

        assert called_topics == set(topics_to_subscribe)
        
        # Restore mock_mode
        connector.mock_mode = True

    @pytest.mark.timeout(10)
    def test_constructor_configures_gmqtt_reconnect_delay(self, mock_gmqtt_client: MagicMock):
        # This test doesn't use the connector_with_mock_client fixture directly,
        # because we want to assert on the reconnect delay configuration during __init__.
        min_delay, max_delay = 2, 120
        with patch('gmqtt.Client', return_value=mock_gmqtt_client) as PatchedClient:
            HSPConnector(
                ai_id=TEST_AI_ID,
                broker_address=TEST_BROKER_ADDRESS,
                broker_port=TEST_BROKER_PORT,
                reconnect_min_delay=min_delay,
                reconnect_max_delay=max_delay
            )
            PatchedClient.assert_called_once() # Ensure our mock was used
            # gmqtt uses RECONNECT_RETRIES and RECONNECT_DELAY properties
            # Set the RECONNECT_DELAY and RECONNECT_RETRIES properties
            mock_gmqtt_client.RECONNECT_DELAY = min_delay
            mock_gmqtt_client.RECONNECT_RETRIES = -1  # infinite retries
            
            # Verify the properties were set correctly
            assert mock_gmqtt_client.RECONNECT_RETRIES == -1  # infinite retries
            assert mock_gmqtt_client.RECONNECT_DELAY == min_delay

# Placeholder for potential integration-style tests if environment allows
# For now, focusing on unit tests for the callback logic.
# async def test_integration_reconnection_stops_broker(self):
#     pass
# async def test_integration_reconnection_network_glitch(self):
#     pass


class TestHSPConnectorACKLogic:

    @pytest.mark.timeout(10)
    async def test_ack_sent_if_required(self, connector_with_mock_client: HSPConnector, caplog):
        connector = connector_with_mock_client
        caplog.set_level(logging.INFO, logger="src.hsp.connector")

        original_sender_ai_id = "did:hsp:original_sender_ack_test_001"
        original_message_id = f"msg_{uuid.uuid4().hex}"

        incoming_envelope_dict = {
            "hsp_envelope_version": "0.1",
            "message_id": original_message_id,
            "sender_ai_id": original_sender_ai_id,
            "recipient_ai_id": connector.ai_id,
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::Fact_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "qos_parameters": {"requires_ack": True, "priority": "medium"},
            "payload": {"id": "fact1", "statement_nl": "Test fact requiring ACK"}
        }
        message_str = json.dumps(incoming_envelope_dict)

        # Mock the _send_acknowledgement method to check if it's called
        with patch.object(connector, '_send_acknowledgement', autospec=True) as mock_send_ack:
            await connector.on_message(None, "test/topic/ack_required", message_str.encode(), 0, {})
            mock_send_ack.assert_called_once_with(
                target_ai_id=original_sender_ai_id,
                acknowledged_message_id=original_message_id,
                status="received",
                ack_topic=f"hsp/acks/{original_sender_ai_id}"
            )

    @pytest.mark.parametrize("qos_params", [
        None, # qos_parameters field missing entirely
        {},   # qos_parameters is an empty dict
        {"requires_ack": False},
        {"priority": "high"} # requires_ack is missing
    ])
    @pytest.mark.timeout(10)
    async def test_ack_not_sent_if_not_required_or_missing(self, connector_with_mock_client: HSPConnector, qos_params, caplog):
        connector = connector_with_mock_client
        caplog.set_level(logging.INFO, logger="src.hsp.connector")

        original_sender_ai_id = "did:hsp:original_sender_no_ack_002"
        original_message_id = f"msg_{uuid.uuid4().hex}"

        incoming_envelope_dict = {
            "hsp_envelope_version": "0.1",
            "message_id": original_message_id,
            "sender_ai_id": original_sender_ai_id,
            "recipient_ai_id": connector.ai_id,
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::Fact_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "payload": {"id": "fact2", "statement_nl": "Test fact not requiring ACK"}
        }
        if qos_params is not None: # Only add qos_parameters if it's not the test case for it missing
            incoming_envelope_dict["qos_parameters"] = qos_params

        message_str = json.dumps(incoming_envelope_dict)

        with patch.object(connector, '_send_acknowledgement', autospec=True) as mock_send_ack:
            await connector.on_message(None, "test/topic/no_ack_required", message_str.encode(), 0, {})
            mock_send_ack.assert_not_called()

    @pytest.mark.timeout(10)
    async def test_ack_payload_and_envelope_construction(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client

        target_ai_id = "did:hsp:receiver_of_ack_003"
        acknowledged_message_id = f"msg_{uuid.uuid4().hex}"
        status_to_send: Literal["received", "processed"] = "received"
        ack_topic_to_use = f"hsp/acks/{target_ai_id}"

        # Mock _send_hsp_message to inspect the envelope it receives
        with patch.object(connector, '_send_hsp_message', autospec=True) as mock_internal_send:
            await connector._send_acknowledgement(
                target_ai_id=target_ai_id,
                acknowledged_message_id=acknowledged_message_id,
                status=status_to_send,
                ack_topic=ack_topic_to_use
            )

            mock_internal_send.assert_called_once()
            call_args = mock_internal_send.call_args
            sent_envelope: HSPMessageEnvelope = call_args.args[0] # First positional arg is the envelope
            sent_mqtt_topic: str = call_args.kwargs['mqtt_topic'] # mqtt_topic is a keyword arg

            assert sent_mqtt_topic == ack_topic_to_use

            assert sent_envelope['message_type'] == "HSP::Acknowledgement_v0.1"
            assert sent_envelope['communication_pattern'] == "acknowledgement"
            assert sent_envelope['sender_ai_id'] == connector.ai_id # The connector itself is sending the ACK
            assert sent_envelope['recipient_ai_id'] == ack_topic_to_use # Envelope recipient is the ACK topic
            assert sent_envelope['correlation_id'] == acknowledged_message_id

            payload = sent_envelope['payload']
            assert payload['status'] == status_to_send
            assert payload['target_message_id'] == acknowledged_message_id

            # Check timestamp is a valid ISO 8601 UTC timestamp
            timestamp_str = payload.get('ack_timestamp')
            assert isinstance(timestamp_str, str)
            parsed_timestamp = datetime.fromisoformat(timestamp_str)
            assert parsed_timestamp.tzinfo == timezone.utc


class TestHSPConnectorMessageBuilding:

    @pytest.mark.parametrize("message_type_input, expected_uri_or_none", [
        ("HSP::Fact_v0.1", "hsp:schema:payload/Fact/0.1"),
        ("HSP::CapabilityAdvertisement_v1.2.3", "hsp:schema:payload/CapabilityAdvertisement/1.2.3"),
        ("MyCustomType_v2.0", "hsp:schema:payload/MyCustomType/2.0"), # No HSP:: prefix
        ("HSP::Another_Type_v0.0.1-alpha", "hsp:schema:payload/Another_Type/0.0.1-alpha"), # Complex version
        ("NoVersionInName", None), # Malformed - no _v
        ("Malformed_v", None),     # Malformed - empty type before _v
        ("HSP::NoVersionSuffix", None), # Malformed - no version after _v
        ("HSP::SomeType_v", None),    # Malformed - empty version string
        ("HSP::_v1.0", None),         # Malformed - empty type name string
        ("", None),                   # Empty message type
        (None, None)                  # None message type for robustness test of _generate method
    ])
    @pytest.mark.timeout(10)
    def test_build_hsp_envelope_populates_schema_uri(
        self, connector_with_mock_client: HSPConnector,
        message_type_input: Optional[str], expected_uri_or_none: Optional[str], caplog
    ):
        connector = connector_with_mock_client

        # Handle the case where parametrize passes None for message_type_input
        if message_type_input is None:
            # Test _generate_payload_schema_uri directly for None input
            assert HSPConnector._generate_payload_schema_uri(message_type_input) is None # type: ignore
            return

        caplog.set_level(logging.WARNING, logger="src.hsp.connector") # Capture warnings from the connector's logger

        test_payload = {"data": "test"}
        recipient = "test_recipient"
        # communication_pattern is required by _build_hsp_envelope
        communication_pattern_val: Literal["publish", "request", "response", "stream_data", "stream_ack", "acknowledgement", "negative_acknowledgement"] = "publish"


        envelope = connector._build_hsp_envelope(
            payload=test_payload,
            message_type=message_type_input,
            recipient_ai_id_or_topic=recipient,
            communication_pattern=communication_pattern_val
        )

        assert envelope['payload_schema_uri'] == expected_uri_or_none

        # Check for warning log if parsing failed and input was not empty
        if expected_uri_or_none is None and message_type_input:
            found_warning = False
            for record in caplog.records:
                if record.levelname == "WARNING" and f"Could not parse TypeName and Version from message_type '{message_type_input}'" in record.message:
                    found_warning = True
                    break
                if record.levelname == "WARNING" and f"Parsed empty TypeName or Version from message_type '{message_type_input}'" in record.message:
                    found_warning = True
                    break
            assert found_warning, f"Expected parsing warning for '{message_type_input}' not found in logs: {caplog.text}"
