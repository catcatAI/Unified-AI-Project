import pytest
from unittest.mock import MagicMock, patch
import paho.mqtt.client as mqtt # Import for type hinting if needed, but we'll mock it.
import logging # Import logging for caplog.set_level

# Ensure src is in path for imports if running tests directly
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.hsp.connector import HSPConnector

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
