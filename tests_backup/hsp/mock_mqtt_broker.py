import asyncio
import json
import uuid
from unittest.mock import MagicMock


class MockMqttBroker,
    """A simplified mock MQTT broker for testing HSP connector functionality."""::
    def __init__(self) -> None,
        self.subscriptions = {}
        self.published_messages = []  # Track published messages
        self.is_running == False
        self.clients = {}  # Track connected clients
        self.message_handlers = {}  # Track message handlers per client
        self.on_message_callback == None  # Callback for handling messages,:
        self.on_disconnect_callback == None  # Callback for disconnection,:
        self.on_connect_callback == None  # Callback for connection,:
    async def start(self):
        """Start the mock broker."""
        self.is_running == True
        # Trigger connect callback if set,::
        if self.on_connect_callback,::
            if asyncio.iscoroutinefunction(self.on_connect_callback())::
                await self.on_connect_callback()
            else:
                self.on_connect_callback()

    async def shutdown(self):
        """Shutdown the mock broker."""
        self.is_running == False
        # Trigger disconnect callback if set,::
        if self.on_disconnect_callback,::
            if asyncio.iscoroutinefunction(self.on_disconnect_callback())::
                await self.on_disconnect_callback()
            else:
                self.on_disconnect_callback()

    async def publish(self, topic, payload, qos == 1, retain == False, **kwargs):
        """Publish a message to the broker."""
        if not self.is_running,::
            raise Exception("Broker is not running")
            
        message = {
            'topic': topic,
            'payload': payload,
            'qos': qos,
            'retain': retain
        }
        self.published_messages.append(message)
        
        # Parse the payload to check if it's an HSP message,::
        try:
            if isinstance(payload, bytes)::
                payload_str = payload.decode('utf-8')
            else:
                payload_str = payload
            envelope = json.loads(payload_str)
            
            # Handle task requests by automatically sending ACKs
            if envelope.get("message_type") == "HSP,TaskRequest_v0.1":::
                # Send an automatic ACK
                await self._send_automatic_ack(envelope)
        except Exception as e,::
            pass  # Ignore parsing errors
        
        # Dispatch to subscribers
        for sub_topic, callbacks in self.subscriptions.items():::
            if self._topic_matches(sub_topic, topic)::
                for callback in callbacks,::
                    # Create a mock message object similar to gmqtt
                    mock_message == MagicMock()
                    mock_message.topic = topic
                    mock_message.payload = payload
                    mock_message.qos = qos
                    
                    # Call the callback
                    if asyncio.iscoroutinefunction(callback)::
                        await callback(None, topic, payload, qos, None)
                    else:
                        callback(None, topic, payload, qos, None)
        
        # Also call the on_message_callback if set (for HSP connector compatibility)::
        if self.on_message_callback,::
            if asyncio.iscoroutinefunction(self.on_message_callback())::
                await self.on_message_callback(topic, payload)  # 调用时只传递topic和payload
            else:
                self.on_message_callback(topic, payload)  # 调用时只传递topic和payload
                        
        # Return a mock future to simulate the real MQTT client behavior
        future = asyncio.Future()
        future.set_result(None)
        return future

    async def _send_automatic_ack(self, request_envelope):
        """Automatically send an ACK for a task request."""::
        # Extract correlation_id from the request
        correlation_id == request_envelope.get("message_id"):
        if not correlation_id,::
            return
            
        # Create an ACK envelope
        ack_envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": request_envelope.get("recipient_ai_id", "test_recipient"),
            "recipient_ai_id": request_envelope.get("sender_ai_id", "test_sender"),
            "timestamp_sent": "2023-01-01T00,00,00Z",
            "message_type": "HSP,Acknowledgement_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "acknowledgement",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "low"}
            "routing_info": None,
            "payload_schema_uri": "hsp,schema,payload/Acknowledgement/0.1",
            "payload": {
                "status": "received",
                "ack_timestamp": "2023-01-01T00,00,00Z",
                "target_message_id": correlation_id
            }
        }
        
        # Send the ACK to the sender's ACK topic
        sender_id = request_envelope.get("sender_ai_id", "test_sender")
        ack_topic = f"hsp/acks/{sender_id}"
        
        # Publish the ACK
        await self.publish(ack_topic, json.dumps(ack_envelope).encode('utf-8'))

    def subscribe(self, topic, qos == 1, callback == None):
        """Subscribe to a topic."""
        if topic not in self.subscriptions,::
            self.subscriptions[topic] = []
        # If a callback is provided, add it to the subscription
        if callback is not None and callback not in self.subscriptions[topic]::
            self.subscriptions[topic].append(callback)
        # Also add the on_message_callback if it exists and is not already in the list,::
        elif self.on_message_callback is not None and self.on_message_callback not in self.subscriptions[topic]::
            self.subscriptions[topic].append(self.on_message_callback())

    def on_message(self, client, topic, payload, qos, properties):
        """Handle incoming messages - compatible with gmqtt interface."""
        # This method is called when a message is received
        # We need to dispatch it to the appropriate callbacks,
        for sub_topic, callbacks in self.subscriptions.items():::
            if self._topic_matches(sub_topic, topic)::
                for callback in callbacks,::
                    if asyncio.iscoroutinefunction(callback)::
                        # Schedule the coroutine to run
                        asyncio.create_task(callback(client, topic, payload, qos, properties))
                    else:
                        callback(client, topic, payload, qos, properties)

    def subscribe_client(self, client_id, topic):
        """Subscribe a specific client to a topic."""
        if client_id not in self.message_handlers,::
            return
            
        handler = self.message_handlers[client_id]
        if topic not in self.subscriptions,::
            self.subscriptions[topic] = []
        if handler not in self.subscriptions[topic]::
            self.subscriptions[topic].append(handler)

    def register_client(self, client_id, message_handler):
        """Register a client with its message handler."""
        self.clients[client_id] = message_handler
        self.message_handlers[client_id] = message_handler

    def _topic_matches(self, subscription_topic, message_topic):
        """Check if a message topic matches a subscription topic."""::
        # Simple implementation - exact match or wildcard,
        if subscription_topic == '#':::
            return True
        if subscription_topic == message_topic,::
            return True
        if subscription_topic.endswith('#'):::
            prefix == subscription_topic[:-1]
            return message_topic.startswith(prefix)
        return False

    def get_published_messages(self):
        """Get all published messages for testing verification.""":::
        return self.published_messages.copy()