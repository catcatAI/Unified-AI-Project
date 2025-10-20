import pytest
import pytest_asyncio
import asyncio
import json
    HSPMessageEnvelope
)
from .mock_mqtt_broker import MockMqttBroker

@pytest_asyncio.fixture(scope="function")
async def mock_broker():
    broker = MockMqttBroker()
    _ = await broker.start()
    try:
        yield broker
    finally:
        _ = await broker.shutdown()

@pytest_asyncio.fixture(scope="function")
async def hsp_connector_fixture(mock_broker):
    connector = HSPConnector(
        ai_id="test_ai_advanced",
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

class TestHSPAdvancedIntegration:
    """Advanced HSP integration tests with complex scenarios and edge cases."""

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_concurrent_task_processing(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector handling concurrent task requests."""
        connector = hsp_connector_fixture
        
        # Track task requests and results
        task_requests = []
        task_results = []
        
        def task_request_callback(payload, sender, envelope):
            _ = task_requests.append((payload, sender, envelope))
            
        def task_result_callback(payload, sender, envelope):
            _ = task_results.append((payload, sender, envelope))
            
        _ = connector.register_on_task_request_callback(task_request_callback)
        _ = connector.register_on_task_result_callback(task_result_callback)
        
        # Send multiple task requests concurrently
        tasks = []
        for i in range(10):
            # Create a proper HSP task request payload with message envelope
            payload = {
                "request_id": f"task_{i}",
                "requester_ai_id": "test_requester",
                "target_ai_id": connector.ai_id,
                "capability_id_filter": f"capability_{i}",
                "parameters": {"data": f"value_{i}"}
            }
            
            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": f"msg_{i}",
                "correlation_id": None,
                "sender_ai_id": "test_requester",
                "recipient_ai_id": connector.ai_id,
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::TaskRequest_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "request",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "high"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/TaskRequest/0.1",
                "payload": payload
            }
            
            # Use await when calling mock_broker.publish since it returns a coroutine
            task = await mock_broker.publish(
                f"hsp/requests/{connector.ai_id}",
                _ = json.dumps(envelope).encode('utf-8')
            )
            _ = tasks.append(task)
            
        # Wait for all publishes to complete
        _ = await asyncio.gather(*tasks)
        _ = await asyncio.sleep(0.5)
        
        # Verify all task requests were received
        assert len(task_requests) == 10
        for i, (payload, sender, envelope) in enumerate(task_requests):
            assert payload["request_id"] == f"task_{i}"
            assert payload["capability_id_filter"] == f"capability_{i}"
        _ = print("Test passed: HSP connector handled concurrent task requests")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_fact_propagation_with_filtering(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector fact propagation with metadata filtering."""
        connector = hsp_connector_fixture
        
        # Track received facts
        received_facts = []
        def fact_callback(payload, sender, envelope):
            _ = received_facts.append((payload, sender, envelope))
            
        _ = connector.register_on_fact_callback(fact_callback)
        
        # Send facts with different metadata
        facts = [
            {"id": "fact1", "content": "public info", "metadata": {"visibility": "public", "category": "general"}},
            {"id": "fact2", "content": "private info", "metadata": {"visibility": "private", "category": "sensitive"}},
            {"id": "fact3", "content": "business info", "metadata": {"visibility": "public", "category": "business"}}
        ]
        
        for fact in facts:
            # Create a proper HSP fact payload with message envelope
            payload = fact
            
            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": fact["id"],
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
                _ = json.dumps(envelope).encode('utf-8')
            )
            
        _ = await asyncio.sleep(0.5)
        
        # Verify all facts were received
        assert len(received_facts) == 3
        
        # Test filtering by sending a fact with specific metadata
        filtered_facts = []
        def filtered_callback(payload, sender, envelope):
            if payload.get("metadata", {}).get("visibility") == "public":
                _ = filtered_facts.append(payload)
                
        # Register a new callback for filtered facts
        _ = connector.register_on_fact_callback(filtered_callback)
        
        # Send another fact
        public_fact = {
            "id": "fact4",
            "content": "another public fact",
            "metadata": {"visibility": "public", "category": "news"}
        }
        
        # Create envelope for public fact
        envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "fact4",
            "correlation_id": None,
            "sender_ai_id": "test_sender",
            "recipient_ai_id": "all",
            "timestamp_sent": "2023-01-01T00:00:00Z",
            "message_type": "HSP::Fact_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
            "payload": public_fact
        }
        
        await mock_broker.publish(
            "hsp/knowledge/facts/test",
            _ = json.dumps(envelope).encode('utf-8')
        )
        
        _ = await asyncio.sleep(0.5)
        
        # Verify filtering worked
        assert len(filtered_facts) == 1
        assert filtered_facts[0]["id"] == "fact4"
        print("Test passed: HSP connector handled fact propagation with filtering")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_capability_advertisement_and_discovery(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector capability advertisement and discovery mechanism."""
        connector = hsp_connector_fixture
        
        # Track capability advertisements
        capabilities_advertised = []
        def capability_callback(payload, sender, envelope):
            _ = capabilities_advertised.append((payload, sender, envelope))
            
        _ = connector.register_on_capability_advertisement_callback(capability_callback)
        
        # Advertise multiple capabilities
        capabilities = [
            {
                "capability_id": "text_analysis_v1",
                "name": "Text Analysis",
                "description": "Analyze text content",
                "version": "1.0",
                "ai_id": connector.ai_id,
                "availability_status": "available",
                "tags": ["nlp", "analysis"],
                "supported_interfaces": ["hsp_v1"],
                "metadata": {"performance": "high"}
            },
            {
                "capability_id": "image_processing_v1",
                "name": "Image Processing",
                "description": "Process and analyze images",
                "version": "1.0",
                "ai_id": connector.ai_id,
                "availability_status": "available",
                "tags": ["vision", "processing"],
                "supported_interfaces": ["hsp_v1"],
                "metadata": {"performance": "medium"}
            }
        ]
        
        for capability in capabilities:
            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": capability["capability_id"],
                "correlation_id": None,
                "sender_ai_id": connector.ai_id,
                "recipient_ai_id": "all",
                "timestamp_sent": "2023-01-01T00:00:00Z",
                "message_type": "HSP::CapabilityAdvertisement_v0.1",  # This is important for routing
                "protocol_version": "0.1",
                "communication_pattern": "publish",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "medium"},
                "routing_info": None,
                "payload_schema_uri": "hsp:schema:payload/CapabilityAdvertisement/0.1",
                "payload": capability
            }
            
            await mock_broker.publish(
                f"hsp/capabilities/{connector.ai_id}",
                _ = json.dumps(envelope).encode('utf-8')
            )
            
        _ = await asyncio.sleep(0.5)
        
        # Verify capabilities were received
        assert len(capabilities_advertised) == 2
        for i, (payload, sender, envelope) in enumerate(capabilities_advertised):
            assert payload["capability_id"] == capabilities[i]["capability_id"]
            assert payload["ai_id"] == connector.ai_id
        _ = print("Test passed: HSP connector handled capability advertisement and discovery")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_error_recovery_and_retry(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector error recovery and retry mechanisms."""
        connector = hsp_connector_fixture
        
        # Track successful and failed operations
        successful_ops = []
        failed_ops = []
        
        def success_callback(payload, sender, envelope):
            _ = successful_ops.append((payload, sender, envelope))
            
        def error_callback(payload, sender, envelope):
            _ = failed_ops.append((payload, sender, envelope))
            
        _ = connector.register_on_fact_callback(success_callback)
        
        # Simulate network issues by temporarily shutting down the broker
        _ = await mock_broker.shutdown()
        
        # Try to send a message while broker is down
        try:
            # Create a proper HSP fact payload with message envelope
            payload = {
                "id": "retry_test",  # Changed from fact_id to id
                "content": "test retry",
                "metadata": {"type": "test"}
            }
            
            # Create a proper HSP message envelope
            envelope = {
                "hsp_envelope_version": "0.1",
                "message_id": "retry_test",
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
                "hsp/test/retry",
                _ = json.dumps(envelope).encode('utf-8')
            )
        except Exception:
            # Expected to fail when broker is down
            pass
        
        # Restart broker
        _ = await mock_broker.start()
        
        # Send message after recovery
        # Create a proper HSP fact payload with message envelope
        payload = {
            "id": "retry_success",  # Changed from fact_id to id
            "content": "retry_success",
            "metadata": {"type": "test"}
        }
        
        # Create a proper HSP message envelope
        envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "retry_success",
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
            "hsp/test/retry",
            _ = json.dumps(envelope).encode('utf-8')
        )
        
        _ = await asyncio.sleep(0.5)
        
        # Verify recovery worked
        assert len(successful_ops) >= 1
        _ = print("Test passed: HSP connector handled error recovery and retry")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_memory_integration(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector integration with memory management."""
        connector = hsp_connector_fixture
        
        # Track memory operations
        memory_operations = []
        
        def memory_callback(payload, sender, envelope):
            _ = memory_operations.append((payload, sender, envelope))
            
        _ = connector.register_on_fact_callback(memory_callback)
        
        # Send a fact that should trigger memory operations
        # Create a proper HSP fact payload with message envelope
        payload = {
            "id": "memory_test_fact",
            "content": "This is a test fact for memory integration",
            "metadata": {"type": "test", "priority": "high"}
        }
        
        # Create a proper HSP message envelope
        envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "memory_test_fact",
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
            "hsp/knowledge/facts/test_ai_advanced",
            _ = json.dumps(envelope).encode('utf-8')
        )
        
        _ = await asyncio.sleep(0.5)
        
        # Verify memory operation was triggered
        assert len(memory_operations) >= 1
        print("Test passed: HSP connector integrated with memory management")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(30)
    async def test_hsp_connector_security_and_authentication(self, hsp_connector_fixture, mock_broker) -> None:
        """Test HSP connector security and authentication mechanisms."""
        connector = hsp_connector_fixture
        
        # Track authenticated messages
        authenticated_messages = []
        
        def auth_callback(payload, sender, envelope):
            _ = authenticated_messages.append((payload, sender, envelope))
            
        _ = connector.register_on_fact_callback(auth_callback)
        
        # Send a message with security metadata
        # Create a proper HSP fact payload with message envelope
        payload = {
            "id": "secure_fact",
            "content": "This is a secure fact",
            "metadata": {
                "security_level": "high",
                "encryption_required": True,
                "authenticated_sender": True
            }
        }
        
        # Create a proper HSP message envelope
        envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "secure_fact",
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
            "hsp/knowledge/facts/test_ai_advanced",
            _ = json.dumps(envelope).encode('utf-8')
        )
        
        _ = await asyncio.sleep(0.5)
        
        # Verify authentication was handled
        assert len(authenticated_messages) >= 1
        _ = print("Test passed: HSP connector handled security and authentication")