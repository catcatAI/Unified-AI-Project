import pytest
import pytest_asyncio
import asyncio
import json
import time
    HSPMessageEnvelope
)

@pytest_asyncio.fixture(scope="function")
async def mock_broker()
    broker = MockMqttBroker()
    _ = await broker.start()
    try:

    yield broker
    finally:
    _ = await broker.shutdown()

@pytest_asyncio.fixture(scope="function")
async def hsp_connector_fixture(mock_broker)
    connector = HSPConnector(
    ai_id="test_ai_enhanced",
    broker_address="localhost",
    broker_port=1883,
    mock_mode=True,
    mock_mqtt_client=mock_broker
    )
    _ = await connector.connect()
    try:

    yield connector
    finally:
    _ = await connector.disconnect()

class TestHSPEnhancedIntegration:
    """Enhanced HSP integration tests with additional scenarios and boundary conditions."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_message_queue_overflow(self, hsp_connector_fixture, mock_broker) -> None:
    """Test HSP connector handling message queue overflow."""
    connector = hsp_connector_fixture

    # Track received messages
    received_messages = []
        def message_callback(payload, sender, envelope)
    received_messages.append((payload, sender, envelope))

    connector.register_on_fact_callback(message_callback)

    # Send a large number of messages quickly to test queue handling
    tasks = []
        for i in range(50)  # Send 50 messages
            # Create a proper HSP fact payload with message envelope
    payload = {
                "id": f"fact_{i}",
                "content": f"Test message {i}",
                "metadata": {"test": "queue_overflow"}
            }

            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": f"fact_{i}",
                "correlation_id": None,
                "sender_ai_id": "test_sender",
                "recipient_ai_id": "all",
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::Fact_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "publish",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "medium"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
                "payload": payload
            }

            task = mock_broker.publish(
                "hsp/knowledge/facts/test",
                json.dumps(envelope).encode('utf-8')
            )
            tasks.append(task)

        # Wait for all publishes to complete
    _ = await asyncio.gather(*tasks)
        await asyncio.sleep(1.0)  # Give more time for processing

    # Verify messages were received (may not be all due to overflow handling)
    assert len(received_messages) > 0
    print(f"Test passed: HSP connector handled message queue overflow, received {len(received_messages)} messages")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_network_disconnect_recovery(self, hsp_connector_fixture, mock_broker) -> None:
    """Test HSP connector recovery from network disconnection."""
    connector = hsp_connector_fixture

    # Track connection status changes
    connection_events = []
        def connect_callback(envelope=None)
    connection_events.append(("connected", time.time()))

        def disconnect_callback(envelope=None)
    connection_events.append(("disconnected", time.time()))

    connector.register_on_connect_callback(connect_callback)
    connector.register_on_disconnect_callback(disconnect_callback)

    # Simulate network disconnection
    _ = await mock_broker.shutdown()
    _ = await asyncio.sleep(0.5)

    # Restart broker
    _ = await mock_broker.start()
        await asyncio.sleep(1.0)  # Give time for reconnection

    # Verify reconnection occurred
    assert len(connection_events) >= 2  # At least initial connect and reconnect
    print("Test passed: HSP connector recovered from network disconnection")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_large_message_handling(self, hsp_connector_fixture, mock_broker) -> None:
    """Test HSP connector handling large messages."""
    connector = hsp_connector_fixture

    # Track received messages
    received_messages = []
        def message_callback(payload, sender, envelope)
    received_messages.append((payload, sender, envelope))

    connector.register_on_fact_callback(message_callback)

    # Create a large message payload
    large_content = "A" * 10000  # 10KB of data
    # Create a proper HSP fact payload with message envelope
    payload = {
            "id": "large_fact",
            "content": large_content,
            "metadata": {"test": "large_message", "size": len(large_content)}
    }

    # Create a proper HSP message envelope
    envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "large_fact",
            "correlation_id": None,
            "sender_ai_id": "test_sender",
            "recipient_ai_id": "all",
            "timestamp_sent": "2023-01-01T00:00:00Z",
            "message_type": "HSP::Fact_v0.1",  # This is important for routing
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
            "payload": payload
    }

    await mock_broker.publish(
            "hsp/knowledge/facts/test",
            json.dumps(envelope).encode('utf-8')
    )

    _ = await asyncio.sleep(0.5)

    # Verify large message was received
    assert len(received_messages) == 1
    assert len(received_messages[0][0]["content"]) == 10000
    print("Test passed: HSP connector handled large message")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_concurrent_subscriptions(self, hsp_connector_fixture, mock_broker) -> None:
    """Test HSP connector handling concurrent subscriptions."""
    connector = hsp_connector_fixture

    # Track facts and opinions separately
    received_facts = []
    received_opinions = []

        def fact_callback(payload, sender, envelope)
    received_facts.append((payload, sender, envelope))

        def opinion_callback(payload, sender, envelope)
    received_opinions.append((payload, sender, envelope))

    connector.register_on_fact_callback(fact_callback)
    connector.register_on_opinion_callback(opinion_callback)

    # Send facts and opinions concurrently
    tasks = []

    # Send facts
        for i in range(5)
            # Create a proper HSP fact payload with message envelope
    payload = {
                "id": f"fact_{i}",
                "content": f"Fact {i}",
                "metadata": {"type": "fact"}
            }

            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": f"fact_{i}",
                "correlation_id": None,
                "sender_ai_id": "test_sender",
                "recipient_ai_id": "all",
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::Fact_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "publish",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "medium"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
                "payload": payload
            }

            task = mock_broker.publish(
                "hsp/knowledge/facts/test",
                json.dumps(envelope).encode('utf-8')
            )
            tasks.append(task)

    # Send opinions
        for i in range(5)
            # Create a proper HSP opinion payload with message envelope
    payload = {
                "id": f"opinion_{i}",
                "content": f"Opinion {i}",
                "confidence": 0.8,
                "metadata": {"type": "opinion"}
            }

            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": f"opinion_{i}",
                "correlation_id": None,
                "sender_ai_id": "test_sender",
                "recipient_ai_id": "all",
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::Opinion_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "publish",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "medium"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/Opinion/0.1",
                "payload": payload
            }

            task = mock_broker.publish(
                "hsp/knowledge/opinions/test",
                json.dumps(envelope).encode('utf-8')
            )
            tasks.append(task)

        # Wait for all publishes to complete
    _ = await asyncio.gather(*tasks)
    _ = await asyncio.sleep(0.5)

    # Verify both facts and opinions were received
    assert len(received_facts) == 5
    assert len(received_opinions) == 5
    print("Test passed: HSP connector handled concurrent subscriptions")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_message_ordering(self, hsp_connector_fixture, mock_broker) -> None:
    """Test HSP connector message ordering preservation."""
    connector = hsp_connector_fixture

    # Track received messages with timestamps
    received_messages = []
        def message_callback(payload, sender, envelope)
    received_messages.append((payload, sender, envelope))

    connector.register_on_fact_callback(message_callback)

    # Send messages in sequence with small delays
    message_ids = []
        for i in range(10)

    payload = {
                "id": f"ordered_fact_{i}",
                "content": f"Ordered message {i}",
                "metadata": {"sequence": i}
            }

            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": f"ordered_fact_{i}",
                "correlation_id": None,
                "sender_ai_id": "test_sender",
                "recipient_ai_id": "all",
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::Fact_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "publish",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "medium"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
                "payload": payload
            }

            message_ids.append(f"ordered_fact_{i}")
            await mock_broker.publish(
                "hsp/knowledge/facts/test",
                json.dumps(envelope).encode('utf-8')
            )
            _ = await asyncio.sleep(0.1)  # Small delay between messages

    _ = await asyncio.sleep(0.5)

    # Verify messages were received in order
    assert len(received_messages) == 10
        for i, (payload, sender, envelope) in enumerate(received_messages)

    assert payload["id"] == f"ordered_fact_{i}"
    print("Test passed: HSP connector preserved message ordering")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_hsp_connector_error_handling(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector error handling for malformed messages.""":
    connector = hsp_connector_fixture

    # Track received messages
    received_messages = []
    error_messages = []

        def fact_callback(payload, sender, envelope)
    received_messages.append((payload, sender, envelope))

        def error_callback(error)
    error_messages.append(error)

    connector.register_on_fact_callback(fact_callback)

    # Send a malformed message
    malformed_payload = b'{"invalid": json}'  # Invalid JSON
    await mock_broker.publish(
            "hsp/knowledge/facts/test",
            malformed_payload
    )

    # Send a valid message
    # Create a proper HSP fact payload with message envelope
    payload = {
            "id": "valid_fact",
            "content": "Valid fact",
            "metadata": {"test": "error_handling"}
    }

    # Create a proper HSP message envelope
    envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "valid_fact",
            "correlation_id": None,
            "sender_ai_id": "test_sender",
            "recipient_ai_id": "all",
            "timestamp_sent": "2023-01-01T00:00:00Z",
            "message_type": "HSP::Fact_v0.1",  # This is important for routing
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
            "payload": payload
    }

    await mock_broker.publish(
            "hsp/knowledge/facts/test",
            json.dumps(envelope).encode('utf-8')
    )

    _ = await asyncio.sleep(0.5)

    # Verify valid message was received (malformed message should be handled gracefully)
    assert len(received_messages) == 1
    assert received_messages[0][0]["id"] == "valid_fact"
    print("Test passed: HSP connector handled error gracefully")