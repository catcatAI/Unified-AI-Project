import json
import uuid
import asyncio
import logging # Added logging
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional, Literal, List
import paho.mqtt.client as mqtt # type: ignore

from .types import (
    HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters,
    HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload,
    HSPAcknowledgementPayload # Added for _send_acknowledgement
)

# Placeholder for other payload types to be defined in src/hsp/types.py
# e.g., HSPBeliefPayload, HSPEnvironmentalStatePayload etc.
# Note: HSPErrorDetails is used in example_hsp_usage, but not directly in HSPConnector class methods yet.
# If it were, it would also need to be imported.

# Initialize logger for this module
logger = logging.getLogger(__name__)
# You can also use a more specific name like logging.getLogger("HSPConnector")
# For basic setup that shows logs during testing with caplog, ensure the level is appropriate.
# Default level for root logger is WARNING. If tests need INFO, it should be configured.
# For now, we'll assume pytest's caplog might set a lower level or we can set it in tests.

class HSPConnector:
    """
    Manages communication with the HSP network using MQTT as the transport.
    Handles message serialization/deserialization, topic subscription, and publishing.

    Features:
    - Automatic reconnection: Utilizes Paho MQTT's built-in mechanism with
      configurable exponential backoff (min/max delays) to automatically
      re-establish connection if the broker becomes unavailable.
    - Automatic re-subscription: Upon successful reconnection, previously active
      subscriptions are automatically restored.
    - Callback system: Allows registration of handlers for generic HSP messages
      and specific message types (Fact, CapabilityAdvertisement, etc.).
    - Acknowledgement (ACK) Sending: Automatically sends an HSP "received"
      acknowledgement if an incoming message's QoS parameters indicate
      `requires_ack: true`. ACKs are sent to a conventional topic
      (e.g., `hsp/acks/{sender_ai_id}`).
    """
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883,
                 client_id_suffix: str = "hsp_connector",
                 reconnect_min_delay: int = 1,
                 reconnect_max_delay: int = 60):
        """
        Initializes the HSPConnector.

        Args:
            ai_id (str): The unique identifier for this AI instance.
            broker_address (str): The address of the MQTT broker.
            broker_port (int): The port of the MQTT broker.
            client_id_suffix (str): A suffix to append to the AI ID for a unique MQTT client ID.
            reconnect_min_delay (int): Minimum delay (seconds) before the first reconnect attempt.
            reconnect_max_delay (int): Maximum delay (seconds) between reconnect attempts.
                                       Paho uses exponential backoff up to this limit.
        """
        self.ai_id: str = ai_id
        self.broker_address: str = broker_address
        self.broker_port: int = broker_port
        self.reconnect_min_delay = reconnect_min_delay
        self.reconnect_max_delay = reconnect_max_delay

        # Ensure client_id is unique if multiple instances run for the same AI, though typically one per AI.
        self.mqtt_client_id: str = f"{self.ai_id}-{client_id_suffix}-{uuid.uuid4().hex[:8]}" # Shorter UUID hex

        self.is_connected: bool = False
        self.mqtt_client: mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.mqtt_client_id)

        # Configure Paho MQTT's automatic reconnection
        self.mqtt_client.reconnect_delay_set(min_delay=self.reconnect_min_delay, max_delay=self.reconnect_max_delay)
        logger.info(f"HSPConnector ({self.ai_id}): MQTT auto-reconnect configured with min_delay={self.reconnect_min_delay}s, max_delay={self.reconnect_max_delay}s.")

        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_message = self._on_mqtt_message

        # Callbacks for different types of HSP messages
        self._on_generic_message_callback: Optional[Callable[[HSPMessageEnvelope, str], None]] = None
        self._on_fact_received_callback: Optional[Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]] = None
        self._on_capability_advertisement_callback: Optional[Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_request_callback: Optional[Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_result_callbacks: List[Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]] = [] # Changed to a list
        # ... other specific payload callbacks can be added

        self.default_qos: int = 1 # MQTT QoS level for publishing

        # For managing subscriptions
        self.subscribed_topics: set[str] = set()
        self._was_unexpectedly_disconnected: bool = False

    @staticmethod
    def _generate_payload_schema_uri(message_type: str) -> Optional[str]:
        """
        Generates a conventional placeholder URI for the payload schema based on message type.

        The convention is `hsp:schema:payload/{TypeName}/{Version}`.
        Parses TypeName and Version from message_type string like "HSP::TypeName_vVersion".

        Args:
            message_type: The HSP message type string.

        Returns:
            A placeholder schema URI string, or None if parsing fails.
        """
        if not message_type:
            # logger.debug("Cannot generate schema URI for empty message_type.") # Use logger from class or module
            return None

        processed_type = message_type
        if processed_type.startswith("HSP::"):
            processed_type = processed_type[len("HSP::"):]

        parts = processed_type.rsplit("_v", 1)
        if len(parts) == 2:
            type_name = parts[0]
            version = parts[1]
            if type_name and version:  # Ensure neither part is empty
                return f"hsp:schema:payload/{type_name}/{version}"
            else:
                logger.warning(f"Parsed empty TypeName or Version from message_type '{message_type}' (processed: '{processed_type}'). No schema URI generated.")
                return None
        else:
            # Log this case as it's an unexpected format if we expect all types to be versioned this way.
            logger.warning(f"Could not parse TypeName and Version from message_type '{message_type}' (processed: '{processed_type}'). Expected format like 'TypeName_vVersion'. No schema URI generated.")
            return None

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            connection_type = "reconnected" if self._was_unexpectedly_disconnected else "connected"
            logger.info(f"HSPConnector ({self.ai_id}): Successfully {connection_type} to MQTT Broker at {self.broker_address}:{self.broker_port}")
            self.is_connected = True
            self._was_unexpectedly_disconnected = False # Reset flag
            # Resubscribe to any topics if it's a reconnect
            for topic in list(self.subscribed_topics): # Iterate over a copy
                self.subscribe(topic) # subscribe method already logs success/failure
        else:
            # This path means connection attempt failed, Paho will retry based on reconnect_delay_set
            logger.warning(f"HSPConnector ({self.ai_id}): Failed to connect to MQTT Broker (during connect/reconnect attempt), reason code {reason_code}. Paho client will continue to retry.")
            self.is_connected = False
            # Do not set _was_unexpectedly_disconnected here, as this is a failed *connect* attempt.

    def _on_mqtt_disconnect(self, client, userdata, reason_code, properties):
        self.is_connected = False
        if reason_code == 0:
            # MQTT_ERR_SUCCESS (0) usually means a clean disconnect initiated by client.disconnect()
            logger.info(f"HSPConnector ({self.ai_id}): Cleanly disconnected from MQTT Broker (reason code {reason_code}).")
            self._was_unexpectedly_disconnected = False # Reset on clean disconnect
        else:
            # Other reason codes indicate an unexpected disconnect (network issue, broker down, etc.)
            logger.warning(f"HSPConnector ({self.ai_id}): Unexpectedly disconnected from MQTT Broker (reason code {reason_code}).")
            logger.info(f"HSPConnector ({self.ai_id}): Paho client will attempt to reconnect automatically (min_delay={self.reconnect_min_delay}s, max_delay={self.reconnect_max_delay}s).")
            self._was_unexpectedly_disconnected = True # Set flag for unexpected disconnect
        # Paho's internal reconnect_delay_set handles the reconnection strategy.

    def _on_mqtt_message(self, client, userdata, msg):
        """Handles incoming MQTT messages and forwards them to HSP message handler."""
        logger.debug(f"HSPConnector ({self.ai_id}): Raw MQTT message received on topic '{msg.topic}'") # Changed to debug
        try:
            message_str = msg.payload.decode('utf-8')
            self._handle_hsp_message_str(message_str, msg.topic)
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error processing raw MQTT message on topic {msg.topic}: {e}", exc_info=True) # Added exc_info

    def connect(self) -> bool:
        """Connects to the MQTT broker."""
        if self.is_connected:
            logger.info(f"HSPConnector ({self.ai_id}): Already connected.")
            return True
        try:
            logger.info(f"HSPConnector ({self.ai_id}): Attempting to connect to MQTT Broker at {self.broker_address}:{self.broker_port}...")
            self.mqtt_client.connect(self.broker_address, self.broker_port, keepalive=60)
            self.mqtt_client.loop_start() # Starts a background thread for network operations, callbacks
            return True
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): MQTT connection error: {e}", exc_info=True)
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnects from the MQTT broker."""
        if self.mqtt_client and self.is_connected: # Ensure client exists before calling methods on it
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        logger.info(f"HSPConnector ({self.ai_id}): Disconnection process initiated.")

    def _build_hsp_envelope(self, payload: Dict[str, Any], message_type: str, recipient_ai_id_or_topic: str,
                            communication_pattern: Literal[
                                "publish", "request", "response",
                                "stream_data", "stream_ack",
                                "acknowledgement", "negative_acknowledgement"
                            ],
                            correlation_id: Optional[str] = None,
                            qos_params: Optional[HSPQoSParameters] = None,
                            protocol_version: str = "0.1") -> HSPMessageEnvelope:
        """
        Builds a standard HSP message envelope.

        This includes generating a placeholder URI for `payload_schema_uri`
        based on the `message_type` (e.g., "hsp:schema:payload/Fact/0.1").
        Actual schema URIs should be used when defined and available.
        """
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
            "payload_schema_uri": HSPConnector._generate_payload_schema_uri(message_type), # Call static method
            "payload": payload
        }
        return envelope

    def _send_hsp_message(self, envelope: HSPMessageEnvelope, mqtt_topic: str, mqtt_qos: Optional[int] = None) -> bool:
        """Sends a pre-built HSP envelope over MQTT."""
        if not self.is_connected:
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot send message to {mqtt_topic}.")
            return False

        message_str = json.dumps(envelope)
        effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos

        try:
            msg_info = self.mqtt_client.publish(mqtt_topic, payload=message_str, qos=effective_mqtt_qos)
            # msg_info.wait_for_publish(timeout=5) # This can block the calling thread.
            # For a library, it's often better to let Paho handle publish retries in its loop
            # or rely on on_publish callback if strict confirmation is needed without blocking.
            # For QoS 0, is_published() is often True immediately. For QoS 1/2, it updates after ACK.
            # Given loop_start() is used, Paho handles this in background.
            # Let's log based on initial rc from publish and assume Paho handles retries for QoS1/2.
            if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"HSPConnector ({self.ai_id}): Message {envelope.get('message_id')} published to topic '{mqtt_topic}' (MQTT MID: {msg_info.mid}, QoS: {effective_mqtt_qos}). Paho will handle delivery for QoS>0.")
                return True
            else:
                logger.error(f"HSPConnector ({self.ai_id}): Failed to publish message {envelope.get('message_id')} to topic '{mqtt_topic}'. MQTT rc: {msg_info.rc}")
                return False
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error sending MQTT message to topic '{mqtt_topic}': {e}", exc_info=True)
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
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot subscribe to topic '{topic}'.")
            return False
        try:
            effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos
            result, mid = self.mqtt_client.subscribe(topic, qos=effective_mqtt_qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                logger.info(f"HSPConnector ({self.ai_id}): Successfully subscribed to topic '{topic}' with QoS {effective_mqtt_qos} (MID: {mid})")
                return True
            else:
                logger.error(f"HSPConnector ({self.ai_id}): Failed to subscribe to topic '{topic}', error code {result}")
                return False
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error subscribing to topic '{topic}': {e}", exc_info=True)
            return False

    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribes from an MQTT topic."""
        if not self.is_connected:
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot unsubscribe from topic '{topic}'.")
            if topic in self.subscribed_topics: # Still remove from local tracking if desired
                self.subscribed_topics.remove(topic)
            return False
        try:
            result, mid = self.mqtt_client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscribed_topics:
                    self.subscribed_topics.remove(topic)
                logger.info(f"HSPConnector ({self.ai_id}): Successfully unsubscribed from topic '{topic}' (MID: {mid})")
                return True
            else:
                logger.error(f"HSPConnector ({self.ai_id}): Failed to unsubscribe from topic '{topic}', error code {result}")
                return False
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error unsubscribing from topic '{topic}': {e}", exc_info=True)
            return False

    def _handle_hsp_message_str(self, message_str: str, received_on_topic: str):
        """Deserializes and processes an incoming HSP message string."""
        try:
            envelope: HSPMessageEnvelope = json.loads(message_str)
            if not all(k in envelope for k in ["message_id", "sender_ai_id", "message_type", "payload"]):
                logger.warning(f"HSPConnector ({self.ai_id}): Received message with missing core envelope fields from topic '{received_on_topic}'. Message snippet: {message_str[:200]}")
                return

            logger.info(f"HSPConnector ({self.ai_id}): Decoded HSP message {envelope['message_id']} from {envelope['sender_ai_id']} on topic '{received_on_topic}'")

            if self._on_generic_message_callback:
                try:
                    self._on_generic_message_callback(envelope, received_on_topic)
                except Exception as e:
                    logger.error(f"HSPConnector ({self.ai_id}): Error in generic message callback for msg {envelope.get('message_id')}: {e}", exc_info=True)

            payload = envelope.get("payload")
            message_type = envelope.get("message_type")

            if message_type and payload is not None:
                specific_handler_error = None
                try:
                    if message_type.startswith("HSP::Fact") and self._on_fact_received_callback:
                        self._on_fact_received_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::CapabilityAdvertisement") and self._on_capability_advertisement_callback:
                        self._on_capability_advertisement_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::TaskRequest") and self._on_task_request_callback:
                        self._on_task_request_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::TaskResult") and self._on_task_result_callbacks:
                        for callback in self._on_task_result_callbacks:
                            try:
                                callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                            except Exception as cb_e:
                                logger.error(f"HSPConnector ({self.ai_id}): Error in a TaskResult callback for msg {envelope.get('message_id')}: {cb_e}", exc_info=True)
                                # Decide if this should set specific_handler_error. If one callback fails, others should still run.
                                # For now, we'll let specific_handler_error be set by the last error, or None if all succeed.
                                specific_handler_error = cb_e # This might capture only the last error.
                    # Add other specific handlers here
                except Exception as e:
                    specific_handler_error = e
                    logger.error(f"HSPConnector ({self.ai_id}): Error in specific callback for {message_type} msg {envelope.get('message_id')}: {e}", exc_info=True)

            qos_params = envelope.get("qos_parameters", {})
            if isinstance(qos_params, dict) and qos_params.get("requires_ack"):
                self._send_acknowledgement(
                    target_ai_id=envelope["sender_ai_id"],
                    acknowledged_message_id=envelope["message_id"],
                    status="received", # "processed" might be too strong if specific_handler_error occurred
                    ack_topic=f"hsp/acks/{envelope['sender_ai_id']}"
                )

        except json.JSONDecodeError:
            logger.error(f"HSPConnector ({self.ai_id}): Received invalid JSON on topic '{received_on_topic}': {message_str[:200]}...")
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Unhandled error processing HSP message from topic '{received_on_topic}': {e}", exc_info=True)

    def _send_acknowledgement(self, target_ai_id: str, acknowledged_message_id: str, status: Literal["received", "processed"], ack_topic: str, version: str = "0.1"):
        """Helper method to construct and send an HSP Acknowledgement message."""
        ack_payload: HSPAcknowledgementPayload = {
            "status": status,
            "ack_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_message_id": acknowledged_message_id
        }
        ack_message_type = f"HSP::Acknowledgement_v{version}"

        envelope = self._build_hsp_envelope(
            payload=ack_payload, # TypedDict is compatible with Dict[str, Any]
            message_type=ack_message_type,
            recipient_ai_id_or_topic=ack_topic,
            communication_pattern="acknowledgement",
            correlation_id=acknowledged_message_id
        )
        logger.info(f"HSPConnector ({self.ai_id}): Sending ACK for message '{acknowledged_message_id}' to '{target_ai_id}' on topic '{ack_topic}'. Status: {status}")
        if not self._send_hsp_message(envelope, mqtt_topic=ack_topic):
            logger.warning(f"HSPConnector ({self.ai_id}): Failed to send ACK for message '{acknowledged_message_id}'.")


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
        """Registers a callback for HSP TaskResult messages. Multiple callbacks can be registered."""
        if callback not in self._on_task_result_callbacks:
            self._on_task_result_callbacks.append(callback)

    def unregister_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]):
        """Unregisters a previously registered callback for HSP TaskResult messages."""
        try:
            self._on_task_result_callbacks.remove(callback)
        except ValueError:
            logger.warning(f"HSPConnector ({self.ai_id}): Attempted to unregister a task result callback that was not registered.")

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
            sample_fact_payload: HSPFactPayload = { # Changed FactPayload to HSPFactPayload
              "id": f"fact_weather_{uuid.uuid4().hex[:6]}", # Use hex for shorter UUID part
              "statement_type": "natural_language",
              "statement_nl": "The forecast for tomorrow is partly cloudy.",
              "source_ai_id": my_ai_id, # Explicitly set for clarity, though _build_hsp_envelope uses self.ai_id
              "timestamp_created": datetime.now(timezone.utc).isoformat(),
              "confidence_score": 0.80,
              "tags": ["weather", "forecast"] # Added tags
            } # type: ignore # Added type: ignore for potentially missing optional fields if HSPFactPayload is strict
            connector.publish_fact(sample_fact_payload, topic=general_facts_topic)

            print("\nPublishing another sample fact to a specific weather subtopic...")
            specific_weather_fact: HSPFactPayload = { # Changed FactPayload to HSPFactPayload
              "id": f"fact_temp_{uuid.uuid4().hex[:6]}",  # Use hex for shorter UUID part
              "statement_type": "semantic_triple",
              "statement_structured": {"subject_uri": "hsp:env:city_A_temp", "predicate_uri": "hsp:property:hasValueCelsius", "object_literal": 25}, # type: ignore
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
