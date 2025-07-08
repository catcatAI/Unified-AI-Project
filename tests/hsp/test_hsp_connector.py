import pytest
from unittest.mock import MagicMock, patch
import paho.mqtt.client as mqtt # Import for type hinting if needed, but we'll mock it.
import logging # Import logging for caplog.set_level
import json
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, Dict, Any # For type hint in test_ack_payload_and_envelope_construction

# Ensure src is in path for imports if running tests directly
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.hsp.connector import HSPConnector
# Assuming HSPMessageEnvelope and other types are accessible or not strictly needed for these mocks
# If type checking sent_envelope against HSPMessageEnvelope is desired, it should be imported
from src.hsp.types import HSPMessageEnvelope

TEST_AI_ID = "test_ai_connector_001"
TEST_BROKER_ADDRESS = "localhost"
TEST_BROKER_PORT = 1883

@pytest.fixture
def mock_paho_client():
    """Fixture to create a MagicMock for the paho.mqtt.client.Client."""
    mock_client = MagicMock(spec=mqtt.Client)
    # Set default return values for methods that might be called indirectly
    mock_client.reconnect_delay_set.return_value = None
    mock_client.connect.return_value = 0 # Simulate success
    mock_client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 1)
    mock_client.unsubscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 2)
    mock_client.publish.return_value = MagicMock(rc=mqtt.MQTT_ERR_SUCCESS, mid=1)
    mock_client.publish.return_value.wait_for_publish.return_value = None # For QoS > 0 publish
    mock_client.publish.return_value.is_published.return_value = True
    mock_client.disconnect.return_value = 0
    mock_client.loop_start.return_value = None
    mock_client.loop_stop.return_value = None
    return mock_client

@pytest.fixture
def connector_with_mock_client(mock_paho_client: MagicMock):
    """Fixture to create an HSPConnector instance with a mocked paho.mqtt.client.Client."""
    with patch('paho.mqtt.client.Client', return_value=mock_paho_client):
        connector = HSPConnector(
            ai_id=TEST_AI_ID,
            broker_address=TEST_BROKER_ADDRESS,
            broker_port=TEST_BROKER_PORT,
            reconnect_min_delay=1,
            reconnect_max_delay=5
        )
        # Assign the mock client directly for easier access in tests if needed,
        # though HSPConnector already stores it as self.mqtt_client
        connector.mqtt_client = mock_paho_client
        return connector

class TestHSPConnectorConnectionLogic:

    def test_initial_connection_logging(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector") # Ensure INFO logs are captured for this logger
        connector = connector_with_mock_client
        assert not connector._was_unexpectedly_disconnected

        # Simulate Paho calling _on_mqtt_connect after a successful physical connection
        # Args for on_connect: client, userdata, flags, reason_code, properties
        connector._on_mqtt_connect(mock_paho_client, None, {'session present': 0}, mqtt.MQTT_ERR_SUCCESS, None)

        assert connector.is_connected
        assert not connector._was_unexpectedly_disconnected
        assert f"HSPConnector ({TEST_AI_ID}): Successfully connected to MQTT Broker" in caplog.text
        assert "reconnected" not in caplog.text # Ensure it says "connected", not "reconnected"

    def test_unexpected_disconnection_flag_and_logging(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector") # Capture INFO and WARNING (default for warning is already on)
        connector = connector_with_mock_client
        connector.is_connected = True # Assume it was connected
        connector._was_unexpectedly_disconnected = False

        # Simulate Paho calling _on_mqtt_disconnect due to an error
        # Args for on_disconnect: client, userdata, reason_code, properties (v2) / rc (v1)
        # Let's use a reason code that indicates an error
        error_reason_code = mqtt.MQTT_ERR_CONN_LOST
        connector._on_mqtt_disconnect(mock_paho_client, None, error_reason_code, None) # For V2 callback

        assert not connector.is_connected
        assert connector._was_unexpectedly_disconnected
        assert f"HSPConnector ({TEST_AI_ID}): Unexpectedly disconnected from MQTT Broker (reason code {error_reason_code})" in caplog.text
        assert "Paho client will attempt to reconnect automatically" in caplog.text

    def test_clean_disconnection_flag_reset_and_logging(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector")
        connector = connector_with_mock_client
        connector.is_connected = True
        connector._was_unexpectedly_disconnected = True # Simulate previous unexpected disconnect

        # Simulate Paho calling _on_mqtt_disconnect for a clean disconnect (e.g., client called disconnect())
        connector._on_mqtt_disconnect(mock_paho_client, None, mqtt.MQTT_ERR_SUCCESS, None) # MQTT_ERR_SUCCESS = 0

        assert not connector.is_connected
        assert not connector._was_unexpectedly_disconnected # Should be reset
        assert f"HSPConnector ({TEST_AI_ID}): Cleanly disconnected from MQTT Broker (reason code {mqtt.MQTT_ERR_SUCCESS})" in caplog.text

    def test_reconnection_logging_and_flag_reset(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock, caplog):
        caplog.set_level(logging.INFO, logger="src.hsp.connector")
        connector = connector_with_mock_client
        connector.is_connected = False # Simulate it's currently disconnected
        connector._was_unexpectedly_disconnected = True # Simulate it was due to an unexpected event

        # Simulate Paho calling _on_mqtt_connect after a successful physical RE-connection
        connector._on_mqtt_connect(mock_paho_client, None, {'session present': 0}, mqtt.MQTT_ERR_SUCCESS, None)

        assert connector.is_connected
        assert not connector._was_unexpectedly_disconnected # Should be reset
        assert f"HSPConnector ({TEST_AI_ID}): Successfully reconnected to MQTT Broker" in caplog.text

    def test_failed_connection_attempt_logging(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock, caplog):
        connector = connector_with_mock_client
        connector.is_connected = False
        initial_unexpected_flag_state = True # Say it was previously disconnected unexpectedly
        connector._was_unexpectedly_disconnected = initial_unexpected_flag_state

        fail_reason_code = mqtt.MQTT_ERR_NO_CONN
        # Simulate Paho calling _on_mqtt_connect but the connection attempt failed
        connector._on_mqtt_connect(mock_paho_client, None, {'session present': 0}, fail_reason_code, None)

        assert not connector.is_connected
        # Flag should not change because this is a failed *connect* attempt, not a new *disconnect* event
        assert connector._was_unexpectedly_disconnected == initial_unexpected_flag_state
        assert f"HSPConnector ({TEST_AI_ID}): Failed to connect to MQTT Broker (during connect/reconnect attempt), reason code {fail_reason_code}" in caplog.text
        assert "Paho client will continue to retry" in caplog.text

    def test_resubscription_on_connect(self, connector_with_mock_client: HSPConnector, mock_paho_client: MagicMock):
        connector = connector_with_mock_client

        topics_to_subscribe = ["test/topic/1", "another/test/topic", "hsp/general"]
        for topic in topics_to_subscribe:
            # Manually add to subscribed_topics, as .subscribe() would call the mock client's subscribe
            # which we want to check after _on_mqtt_connect is called.
            # In a real scenario, connector.subscribe(topic) would be called by user code.
            # Here, we're testing _on_mqtt_connect's behavior given that self.subscribed_topics is populated.
            connector.subscribed_topics.add(topic)

        # Reset call count for the specific mock we are interested in
        mock_paho_client.subscribe.reset_mock()

        # Simulate Paho calling _on_mqtt_connect after a successful physical connection
        connector._on_mqtt_connect(mock_paho_client, None, {'session present': 0}, mqtt.MQTT_ERR_SUCCESS, None)

        assert connector.is_connected
        assert mock_paho_client.subscribe.call_count == len(topics_to_subscribe)

        # Verify that subscribe was called for each topic
        # The actual call to connector.subscribe() inside _on_mqtt_connect then calls mock_paho_client.subscribe()
        # So we check the calls to the paho client's subscribe method.
        called_topics = set()
        for call_args in mock_paho_client.subscribe.call_args_list:
            args, kwargs = call_args
            called_topics.add(args[0]) # topic is the first positional argument
            assert kwargs.get('qos') == connector.default_qos # Check if default QoS was used

        assert called_topics == set(topics_to_subscribe)

    def test_constructor_configures_paho_reconnect_delay(self, mock_paho_client: MagicMock):
        # This test doesn't use the connector_with_mock_client fixture directly,
        # because we want to assert on the call to reconnect_delay_set during __init__.
        min_delay, max_delay = 2, 120
        with patch('paho.mqtt.client.Client', return_value=mock_paho_client) as PatchedClient:
            HSPConnector(
                ai_id=TEST_AI_ID,
                broker_address=TEST_BROKER_ADDRESS,
                broker_port=TEST_BROKER_PORT,
                reconnect_min_delay=min_delay,
                reconnect_max_delay=max_delay
            )
            PatchedClient.assert_called_once() # Ensure our mock was used
            mock_paho_client.reconnect_delay_set.assert_called_once_with(min_delay=min_delay, max_delay=max_delay)

# Placeholder for potential integration-style tests if environment allows
# For now, focusing on unit tests for the callback logic.
# async def test_integration_reconnection_stops_broker(self):
#     pass
# async def test_integration_reconnection_network_glitch(self):
#     pass


class TestHSPConnectorACKLogic:

    def test_ack_sent_if_required(self, connector_with_mock_client: HSPConnector, caplog):
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
            connector._handle_hsp_message_str(message_str, "test/topic/ack_required")
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
    def test_ack_not_sent_if_not_required_or_missing(self, connector_with_mock_client: HSPConnector, qos_params, caplog):
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
            connector._handle_hsp_message_str(message_str, "test/topic/no_ack_required")
            mock_send_ack.assert_not_called()

    def test_ack_payload_and_envelope_construction(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client

        target_ai_id = "did:hsp:receiver_of_ack_003"
        acknowledged_message_id = f"msg_{uuid.uuid4().hex}"
        status_to_send: Literal["received", "processed"] = "received"
        ack_topic_to_use = f"hsp/acks/{target_ai_id}"

        # Mock _send_hsp_message to inspect the envelope it receives
        with patch.object(connector, '_send_hsp_message', autospec=True) as mock_internal_send:
            connector._send_acknowledgement(
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


class TestHSPConnectorTaskResultCallbacks:

    def _create_task_result_message_str(self, sender_ai_id: str, recipient_ai_id: str, payload: Optional[Dict[str, Any]] = None) -> str:
        """Helper to create a JSON string for a task result message envelope."""
        if payload is None:
            payload = {"result_id": "res_123", "request_id": "req_abc", "executing_ai_id": sender_ai_id, "status": "success", "payload": {"info": "done"}}

        envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": f"msg_{uuid.uuid4().hex}",
            "sender_ai_id": sender_ai_id,
            "recipient_ai_id": recipient_ai_id,
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1", # Corrected message type
            "protocol_version": "0.1",
            "communication_pattern": "response", # Typically 'response' for results
            "qos_parameters": {"requires_ack": False}, # Example
            "payload": payload
        }
        return json.dumps(envelope)

    def test_register_single_task_result_callback(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client
        mock_callback = MagicMock()
        connector.register_on_task_result_callback(mock_callback)

        test_payload = {"status": "success", "data": "single_cb_test"}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_single_cb",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        # Simulate message arrival
        connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")

        mock_callback.assert_called_once()
        args, _ = mock_callback.call_args
        assert args[0] == test_payload # payload
        assert args[1] == "sender_single_cb"  # sender_ai_id
        assert isinstance(args[2], dict) # full_envelope
        assert args[2]['message_type'] == "HSP::TaskResult_v0.1"

    def test_register_multiple_task_result_callbacks(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client
        mock_callback1 = MagicMock(name="cb1")
        mock_callback2 = MagicMock(name="cb2")

        connector.register_on_task_result_callback(mock_callback1)
        connector.register_on_task_result_callback(mock_callback2)

        test_payload = {"status": "progress", "percentage": 50}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_multi_cb",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")

        mock_callback1.assert_called_once()
        args1, _ = mock_callback1.call_args
        assert args1[0] == test_payload
        assert args1[1] == "sender_multi_cb"

        mock_callback2.assert_called_once()
        args2, _ = mock_callback2.call_args
        assert args2[0] == test_payload
        assert args2[1] == "sender_multi_cb"

    def test_unregister_task_result_callback(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client
        mock_callback_kept = MagicMock(name="kept_cb")
        mock_callback_removed = MagicMock(name="removed_cb")

        connector.register_on_task_result_callback(mock_callback_kept)
        connector.register_on_task_result_callback(mock_callback_removed)

        connector.unregister_on_task_result_callback(mock_callback_removed)

        test_payload = {"status": "cancelled"}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_unregister_cb",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")

        mock_callback_kept.assert_called_once()
        mock_callback_removed.assert_not_called()

    def test_unregister_non_existent_task_result_callback(self, connector_with_mock_client: HSPConnector, caplog):
        connector = connector_with_mock_client
        mock_callback_never_registered = MagicMock()
        caplog.set_level(logging.WARNING, logger="src.hsp.connector")

        connector.unregister_on_task_result_callback(mock_callback_never_registered)

        assert f"HSPConnector ({connector.ai_id}): Attempted to unregister a task result callback that was not registered." in caplog.text

    def test_task_result_callback_error_handling(self, connector_with_mock_client: HSPConnector, caplog):
        connector = connector_with_mock_client
        caplog.set_level(logging.ERROR, logger="src.hsp.connector")

        mock_callback_failing = MagicMock(name="failing_cb", side_effect=ValueError("Callback failed!"))
        mock_callback_working = MagicMock(name="working_cb")

        connector.register_on_task_result_callback(mock_callback_failing)
        connector.register_on_task_result_callback(mock_callback_working)

        test_payload = {"status": "error_in_cb_test"}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_cb_error",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")

        mock_callback_failing.assert_called_once()
        mock_callback_working.assert_called_once() # Ensure subsequent callbacks are still called

        assert "Error in a TaskResult callback" in caplog.text
        assert "ValueError: Callback failed!" in caplog.text # Check for the specific error

    def test_no_task_result_callbacks_registered(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client
        # No callbacks registered

        test_payload = {"status": "no_cb_test"}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_no_cb",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        try:
            connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")
        except Exception as e:
            pytest.fail(f"Processing task result message with no callbacks registered raised an exception: {e}")
        # If it reaches here without error, the test passes.

    def test_duplicate_callback_registration_is_ignored(self, connector_with_mock_client: HSPConnector):
        connector = connector_with_mock_client
        mock_callback = MagicMock()

        connector.register_on_task_result_callback(mock_callback)
        connector.register_on_task_result_callback(mock_callback) # Register same instance again

        assert len(connector._on_task_result_callbacks) == 1 # Should only be one instance

        test_payload = {"status": "duplicate_reg_test"}
        message_str = self._create_task_result_message_str(
            sender_ai_id="sender_dup_reg",
            recipient_ai_id=connector.ai_id,
            payload=test_payload
        )
        connector._handle_hsp_message_str(message_str, "hsp/results/test_ai_connector_001")

        mock_callback.assert_called_once() # Called only once
