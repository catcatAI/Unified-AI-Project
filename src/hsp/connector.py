import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional, Literal # Added Optional, Literal, Dict, Any, Callable
import paho.mqtt.client as mqtt # type: ignore # Using type: ignore as paho-mqtt might not have perfect type hints

from .types import HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters # Using .types for relative import, added HSPQoSParameters

from .types import HSPMessageEnvelope, HSPFactPayload, \
    HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload # Added new types

# Placeholder for other payload types to be defined in src/hsp/types.py
# e.g., HSPBeliefPayload, HSPEnvironmentalStatePayload etc.


class HSPConnector:
    """
    Manages communication with the HSP network.
    Handles message serialization/deserialization and transport interactions.
    Initial version uses MQTT as the transport.
    """
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883, client_id_suffix: str = "hsp_connector"):
        self.ai_id: str = ai_id
        self.broker_address: str = broker_address
        self.broker_port: int = broker_port
        # Ensure client_id is unique if multiple instances run for the same AI, though typically one per AI.
        self.mqtt_client_id: str = f"{self.ai_id}-{client_id_suffix}-{uuid.uuid4()}" # Unique client ID for MQTT

        self.is_connected: bool = False
        self.mqtt_client: mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.mqtt_client_id)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_message = self._on_mqtt_message

        # Callbacks for different types of HSP messages
        self._on_generic_message_callback: Optional[Callable[[HSPMessageEnvelope, str], None]] = None
        self._on_fact_received_callback: Optional[Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]] = None
        self._on_capability_advertisement_callback: Optional[Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_request_callback: Optional[Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_result_callback: Optional[Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]] = None
        # ... other specific payload callbacks can be added

        self.default_qos: int = 1 # MQTT QoS level for publishing

        # For managing subscriptions
        self.subscribed_topics: set[str] = set()

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"HSPConnector ({self.ai_id}): Successfully connected to MQTT Broker at {self.broker_address}:{self.broker_port}")
            self.is_connected = True
            # Resubscribe to any topics if it's a reconnect
            for topic in list(self.subscribed_topics): # Iterate over a copy
                self.subscribe(topic)
        else:
            print(f"HSPConnector ({self.ai_id}): Failed to connect to MQTT Broker, reason code {reason_code}")
            self.is_connected = False

    def _on_mqtt_disconnect(self, client, userdata, reason_code, properties):
        self.is_connected = False
        print(f"HSPConnector ({self.ai_id}): Disconnected from MQTT Broker, reason code {reason_code}")
        # TODO: Implement reconnection strategy

    def _on_mqtt_message(self, client, userdata, msg):
        """Handles incoming MQTT messages and forwards them to HSP message handler."""
        print(f"HSPConnector ({self.ai_id}): Raw MQTT message received on topic '{msg.topic}'")
        try:
            message_str = msg.payload.decode('utf-8')
            self._handle_hsp_message_str(message_str, msg.topic)
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): Error processing raw MQTT message: {e}")

    def connect(self) -> bool:
        """Connects to the MQTT broker."""
        if self.is_connected:
            print(f"HSPConnector ({self.ai_id}): Already connected.")
            return True
        try:
            print(f"HSPConnector ({self.ai_id}): Attempting to connect to MQTT Broker at {self.broker_address}:{self.broker_port}...")
            self.mqtt_client.connect(self.broker_address, self.broker_port, keepalive=60)
            self.mqtt_client.loop_start() # Starts a background thread for network operations, callbacks
            # Connection status will be updated by _on_mqtt_connect callback
            # For initial check, we can assume it will connect or fail quickly for this simple version.
            # A more robust version would await the on_connect callback.
            # For now, we'll return True and let the callback update is_connected.
            # This is a simplification for non-async paho-mqtt in an async conceptual flow.
            return True
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): MQTT connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnects from the MQTT broker."""
        if self.mqtt_client and self.is_connected:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            # is_connected will be set to False by _on_mqtt_disconnect
        print(f"HSPConnector ({self.ai_id}): Disconnection process initiated.")

    def _build_hsp_envelope(self, payload: Dict[str, Any], message_type: str, recipient_ai_id_or_topic: str,
                            communication_pattern: Literal[
                                "publish", "request", "response",
                                "stream_data", "stream_ack",
                                "acknowledgement", "negative_acknowledgement"
                            ],
                            correlation_id: Optional[str] = None,
                            qos_params: Optional[HSPQoSParameters] = None,
                            protocol_version: str = "0.1") -> HSPMessageEnvelope:
        """Builds a standard HSP message envelope."""
        effective_correlation_id = correlation_id if correlation_id else str(uuid.uuid4())

        # Constructing a dictionary that conforms to the HSPMessageEnvelope TypedDict
        envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": effective_correlation_id,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": recipient_ai_id_or_topic, # Topic for publish, specific AI ID for request/response
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": message_type,
            "protocol_version": protocol_version,
            "communication_pattern": communication_pattern,
            "security_parameters": {"signature_algorithm": None, "signature": None, "encryption_details": None}, # Basic for v0.1
            "qos_parameters": qos_params if qos_params else {"priority": "medium", "requires_ack": False}, # HSP QoS, not MQTT QoS
            "routing_info": {},
            "payload_schema_uri": None, # TODO: Add schema URIs when defined
            "payload": payload
        }
        return envelope

    def _send_hsp_message(self, envelope: HSPMessageEnvelope, mqtt_topic: str, mqtt_qos: Optional[int] = None) -> bool:
        """Sends a pre-built HSP envelope over MQTT."""
        if not self.is_connected:
            print(f"HSPConnector ({self.ai_id}): Not connected. Cannot send message.")
            return False

        message_str = json.dumps(envelope)
        effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos

        try:
            msg_info = self.mqtt_client.publish(mqtt_topic, payload=message_str, qos=effective_mqtt_qos)
            msg_info.wait_for_publish(timeout=5) # Wait for publish confirmation (for QoS > 0)
            if msg_info.is_published():
                print(f"HSPConnector ({self.ai_id}): Successfully published message {envelope.get('message_id')} to topic '{mqtt_topic}' (MQTT MID: {msg_info.mid})")
                return True
            else:
                print(f"HSPConnector ({self.ai_id}): Failed to publish message {envelope.get('message_id')} to topic '{mqtt_topic}' (MQTT MID: {msg_info.mid}) - not confirmed.")
                return False
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): Error sending MQTT message to topic '{mqtt_topic}': {e}")
            return False

    def publish_fact(self, fact_payload: HSPFactPayload, topic: str, fact_payload_version: str = "0.1") -> bool:
        """Publishes a Fact payload to a given HSP topic via MQTT."""
        message_type = f"HSP::Fact_v{fact_payload_version}"
        # TypedDict is structurally compatible with Dict[str, Any] for the payload argument
        envelope = self._build_h_sp_envelope(
            payload=dict(fact_payload), # Ensure payload is a dict if fact_payload is a TypedDict
            message_type=message_type,
            recipient_ai_id_or_topic=topic, # For Pub/Sub, recipient_ai_id in envelope is the topic
            communication_pattern="publish"
        )
        # For MQTT, the topic in the envelope is also the MQTT topic.
        return self._send_hsp_message(envelope, mqtt_topic=topic)

    def subscribe(self, topic: str, mqtt_qos: Optional[int] = None) -> bool:
        """Subscribes to an MQTT topic to receive HSP messages."""
        if not self.is_connected:
            print(f"HSPConnector ({self.ai_id}): Not connected. Cannot subscribe to topic '{topic}'.")
            return False
        try:
            effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos
            result, mid = self.mqtt_client.subscribe(topic, qos=effective_mqtt_qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                print(f"HSPConnector ({self.ai_id}): Successfully subscribed to topic '{topic}' with QoS {effective_mqtt_qos} (MID: {mid})")
                return True
            else:
                print(f"HSPConnector ({self.ai_id}): Failed to subscribe to topic '{topic}', error code {result}")
                return False
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): Error subscribing to topic '{topic}': {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribes from an MQTT topic."""
        if not self.is_connected:
            print(f"HSPConnector ({self.ai_id}): Not connected. Cannot unsubscribe from topic '{topic}'.")
            # Still remove from local tracking if desired
            if topic in self.subscribed_topics:
                self.subscribed_topics.remove(topic)
            return False
        try:
            result, mid = self.mqtt_client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscribed_topics:
                    self.subscribed_topics.remove(topic)
                print(f"HSPConnector ({self.ai_id}): Successfully unsubscribed from topic '{topic}' (MID: {mid})")
                return True
            else:
                print(f"HSPConnector ({self.ai_id}): Failed to unsubscribe from topic '{topic}', error code {result}")
                return False
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): Error unsubscribing from topic '{topic}': {e}")
            return False

    def _handle_hsp_message_str(self, message_str: str, received_on_topic: str):
        """Deserializes and processes an incoming HSP message string."""
        try:
            envelope: HSPMessageEnvelope = json.loads(message_str)
            # Basic validation of envelope structure (more robust with TypedDict/Pydantic)
            if not all(k in envelope for k in ["message_id", "sender_ai_id", "message_type", "payload"]):
                print(f"HSPConnector ({self.ai_id}): Received message with missing core envelope fields from topic '{received_on_topic}'.")
                return

            print(f"HSPConnector ({self.ai_id}): Decoded HSP message {envelope['message_id']} from {envelope['sender_ai_id']} on topic '{received_on_topic}'")

            # Invoke generic callback if registered
            if self._on_generic_message_callback:
                try:
                    self._on_generic_message_callback(envelope, received_on_topic)
                except Exception as e:
                    print(f"HSPConnector ({self.ai_id}): Error in generic message callback: {e}")

            # Invoke specific callbacks based on message_type
            payload = envelope.get("payload")
            message_type = envelope.get("message_type")

            if message_type and payload is not None: # Ensure payload is not None
                # Dispatch to specific handlers first
                if message_type.startswith("HSP::Fact") and self._on_fact_received_callback:
                    try:
                        self._on_fact_received_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    except Exception as e:
                        print(f"HSPConnector ({self.ai_id}): Error in Fact callback: {e}")
                elif message_type.startswith("HSP::CapabilityAdvertisement") and self._on_capability_advertisement_callback:
                    try:
                        self._on_capability_advertisement_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    except Exception as e:
                        print(f"HSPConnector ({self.ai_id}): Error in CapabilityAdvertisement callback: {e}")
                elif message_type.startswith("HSP::TaskRequest") and self._on_task_request_callback:
                    try:
                        self._on_task_request_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    except Exception as e:
                        print(f"HSPConnector ({self.ai_id}): Error in TaskRequest callback: {e}")
                elif message_type.startswith("HSP::TaskResult") and self._on_task_result_callback:
                    try:
                        self._on_task_result_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    except Exception as e:
                        print(f"HSPConnector ({self.ai_id}): Error in TaskResult callback: {e}")
                # Add elif for other specific message types (Belief, EnvironmentalState, Ack, Nack etc.) here

                # The generic callback is called AFTER specific ones (if any matched), or if no specific one matched.
                # However, the current generic callback is called before this block.
                # Decision: Generic callback should be for *all* messages. Specific ones are for convenience.
                    # The current structure calls generic first, then tries specific. This is acceptable.

            # TODO: Implement logic for sending ACKs if the received message's qos_parameters.requires_ack is true.
            # This would involve crafting an HSP::Acknowledgement_v0.1 message and sending it back,
            # likely to a reply-to topic or a direct topic for the sender_ai_id.

        except json.JSONDecodeError:
            print(f"HSPConnector ({self.ai_id}): Received invalid JSON on topic '{received_on_topic}': {message_str[:200]}...") # Log snippet
        except Exception as e:
            print(f"HSPConnector ({self.ai_id}): Unhandled error processing HSP message from topic '{received_on_topic}': {e}")

    # Registration methods for callbacks
    def register_on_generic_message_callback(self, callback: Callable[[HSPMessageEnvelope, str], None]):
        """Registers a callback for all successfully decoded HSP messages.
        Callback signature: func(envelope: HSPMessageEnvelope, received_on_topic: str) -> None
        """
        self._on_generic_message_callback = callback

    def register_on_fact_callback(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]):
        """Registers a callback for HSP Fact messages.
        Callback signature: func(fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None
        """
        self._on_fact_received_callback = callback

    def register_on_capability_advertisement_callback(self, callback: Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]):
        """Registers a callback for HSP CapabilityAdvertisement messages."""
        self._on_capability_advertisement_callback = callback

    def register_on_task_request_callback(self, callback: Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]):
        """Registers a callback for HSP TaskRequest messages."""
        self._on_task_request_callback = callback

    def register_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]):
        """Registers a callback for HSP TaskResult messages."""
        self._on_task_result_callback = callback

    # --- New methods for publishing/sending Tasking and Capabilities ---
    def publish_capability_advertisement(self, payload: HSPCapabilityAdvertisementPayload, topic: str, version: str = "0.1") -> bool:
        """Publishes a CapabilityAdvertisement payload."""
        message_type = f"HSP::CapabilityAdvertisement_v{version}"
        envelope = self._build_hsp_envelope(
            payload=dict(payload), # Ensure it's a dict
            message_type=message_type,
            recipient_ai_id_or_topic=topic,
            communication_pattern="publish"
        )
        return self._send_hsp_message(envelope, mqtt_topic=topic)

    def send_task_request(self, payload: HSPTaskRequestPayload, target_ai_id_or_topic: str, version: str = "0.1") -> Optional[str]:
        """Sends a TaskRequest payload and returns the correlation_id used."""
        message_type = f"HSP::TaskRequest_v{version}"
        # Task requests should have a unique correlation_id for tracking responses.
        # _build_hsp_envelope generates one if not provided; let's use that.
        envelope = self._build_hsp_envelope(
            payload=dict(payload), # Ensure it's a dict
            message_type=message_type,
            recipient_ai_id_or_topic=target_ai_id_or_topic,
            communication_pattern="request"
            # correlation_id will be auto-generated by _build_hsp_envelope
        )
        if self._send_hsp_message(envelope, mqtt_topic=target_ai_id_or_topic): # Topic could be specific to target AI or a general task request topic
            return envelope.get("correlation_id")
        return None

    def send_task_result(self, payload: HSPTaskResultPayload, reply_to_address: str, correlation_id: str, version: str = "0.1") -> bool:
        """Sends a TaskResult payload in response to a TaskRequest."""
        message_type = f"HSP::TaskResult_v{version}"
        envelope = self._build_hsp_envelope(
            payload=dict(payload), # Ensure it's a dict
            message_type=message_type,
            recipient_ai_id_or_topic=reply_to_address, # Send to the callback address or original requester's topic
            communication_pattern="response",
            correlation_id=correlation_id # Crucial to link to the request
        )
        return self._send_hsp_message(envelope, mqtt_topic=reply_to_address)

    def set_default_mqtt_qos(self, qos: int):
        """Sets the default MQTT QoS level for publishing messages (0, 1, or 2)."""
        if qos in [0, 1, 2]:
            self.default_qos = qos
        else:
            print(f"HSPConnector ({self.ai_id}): Invalid MQTT QoS value {qos}. Must be 0, 1, or 2.")

# Example of how this might be used (conceptual, would be in main application logic)
async def example_hsp_usage():
    print("Starting HSP Connector example...")
    my_ai_id = "did:hsp:ai_example_123"
    # Ensure an MQTT broker (like Mosquitto) is running at this address
    connector = HSPConnector(ai_id=my_ai_id, broker_address="localhost", broker_port=1883)

    # Define callback functions
    def generic_hsp_message_handler(envelope: HSPMessageEnvelope, topic: str) -> None:
        print(f"\n[Generic Handler] Received on topic '{topic}':")
        print(f"  Message ID  : {envelope.get('message_id')}")
        print(f"  Sender AI ID: {envelope.get('sender_ai_id')}")
        print(f"  Message Type: {envelope.get('message_type')}")
        print(f"  Payload     : {json.dumps(envelope.get('payload'), indent=2)}")

    def fact_message_handler(fact_payload: HSPFactPayload, sender_id: str, envelope_context: HSPMessageEnvelope) -> None:
        print(f"\n[Fact Handler] Fact from {sender_id}:")
        # Accessing HSPFactPayload fields - ensuring they exist or using .get()
        statement_nl = fact_payload.get('statement_nl')
        statement_structured = fact_payload.get('statement_structured')
        statement_to_print = statement_nl if statement_nl else statement_structured
        print(f"  Statement: {statement_to_print}")
        print(f"  Confidence: {fact_payload.get('confidence_score')}")
        print(f"  Full Envelope Msg ID: {envelope_context.get('message_id')}")


    connector.register_on_generic_message_callback(generic_hsp_message_handler)
    connector.register_on_fact_callback(fact_message_handler)

    if connector.connect(): # This starts the MQTT loop in a thread
        print("Connector initiated connection sequence.")
        # Wait a bit for connection to establish (in real app, use more robust check or awaitable connect)
        await asyncio.sleep(2)

        if connector.is_connected:
            print("Connector is connected. Subscribing to topics...")
            general_facts_topic = "hsp/knowledge/facts/general"
            weather_topic = "hsp/knowledge/facts/weather/#" # Subscribe to all weather subtopics

            connector.subscribe(general_facts_topic)
            connector.subscribe(weather_topic)

            await asyncio.sleep(1) # Allow subscriptions to complete

            print("\nPublishing a sample fact...")
            sample_fact_payload: FactPayload = {
              "id": f"fact_weather_{uuid.uuid4()}",
              "statement_type": "natural_language",
              "statement_nl": "The forecast for tomorrow is partly cloudy.",
              # source_ai_id is added by _build_hsp_envelope using self.ai_id
              "timestamp_created": datetime.now(timezone.utc).isoformat(),
              "confidence_score": 0.80,
              "context": {"location_generic": "local_area"}
            }
            connector.publish_fact(sample_fact_payload, topic=general_facts_topic)

            print("\nPublishing another sample fact to a specific weather subtopic...")
            specific_weather_fact: FactPayload = {
              "id": f"fact_temp_{uuid.uuid4()}",
              "statement_type": "semantic_triple",
              "statement_structured": {"subject_uri": "hsp:env:city_A_temp", "predicate_uri": "hsp:property:hasValueCelsius", "object_literal": 25},
              "timestamp_created": datetime.now(timezone.utc).isoformat(),
              "confidence_score": 0.99,
            }
            connector.publish_fact(specific_weather_fact, topic="hsp/knowledge/facts/weather/city_A/temperature")

            print("\nExample running. Listening for messages for 20 seconds...")
            print("Try publishing messages to the subscribed topics using an MQTT client (e.g., MQTT Explorer or mosquitto_pub).")
            print(f"  mosquitto_pub -h localhost -t '{general_facts_topic}' -m '{{\"hsp_envelope_version\": \"0.1\", ...}}'")
            await asyncio.sleep(20)
        else:
            print("Failed to connect to MQTT broker for example.")

        connector.disconnect()
        print("HSP Connector example finished.")
    else:
        print("Initial connection call failed.")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure you have an MQTT broker running (e.g., `docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto`)
    # 2. Install paho-mqtt: `pip install paho-mqtt`
    # 3. Uncomment the next line to run:
    # asyncio.run(example_hsp_usage())
    pass
