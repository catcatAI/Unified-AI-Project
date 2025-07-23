import json
import uuid
import asyncio
import logging
import ssl

from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional, Literal
from unittest.mock import MagicMock
import gmqtt

from .types import (
    HSPMessageEnvelope, HSPFactPayload, HSPQoSParameters,
    HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload,
    HSPAcknowledgementPayload
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
    """Manages HSP communication over an MQTT transport for a single AI agent using gmqtt."""
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
                 reconnect_max_delay: int = 60,
                 mock_mode: bool = False,
                 tls_ca_certs: Optional[str] = None,
                 tls_certfile: Optional[str] = None,
                 tls_keyfile: Optional[str] = None,
                 tls_insecure: bool = False,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 broker_list: Optional[list] = None):
        """
        Initializes the HSPConnector.

        Args:
            ai_id (str): The unique identifier for this AI instance.
            broker_address (str): The address of the MQTT broker.
            broker_port (int): The port of the MQTT broker.
            broker_list (list, optional): A list of brokers to connect to.
            client_id_suffix (str): A suffix to append to the AI ID for a unique MQTT client ID.
            reconnect_min_delay (int): Minimum delay (seconds) before the first reconnect attempt.
            reconnect_max_delay (int): Maximum delay (seconds) between reconnect attempts.
                                       Paho uses exponential backoff up to this limit.
            mock_mode (bool): If True, the connector will not attempt to connect to the broker.
            tls_ca_certs (str, optional): Path to the CA certificate file.
            tls_certfile (str, optional): Path to the client certificate file.
            tls_keyfile (str, optional): Path to the client key file.
            username (str, optional): The username for authenticating with the MQTT broker.
            password (str, optional): The password for authenticating with the MQTT broker.
        """
        self.ai_id: str = ai_id
        self.broker_address: str = broker_address
        self.broker_port: int = broker_port
        self.broker_list: Optional[list] = broker_list
        self.reconnect_min_delay = reconnect_min_delay
        self.reconnect_max_delay = reconnect_max_delay
        self.tls_insecure = tls_insecure
        self.mock_mode = mock_mode

        # Ensure client_id is unique if multiple instances run for the same AI, though typically one per AI.
        self.mqtt_client_id: str = f"{self.ai_id}-{client_id_suffix}-{uuid.uuid4().hex[:8]}" # Shorter UUID hex

        self.is_connected: bool = False
        self._loop_task: Optional[asyncio.Task] = None
        if not self.mock_mode:
            self.mqtt_client = gmqtt.Client(self.mqtt_client_id)
            if username:
                self.mqtt_client.set_auth_credentials(username, password)
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.on_message = self.on_message

            if tls_ca_certs:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=tls_ca_certs)
                if tls_certfile and tls_keyfile:
                    ssl_context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)
                if self.tls_insecure:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                self.mqtt_client.set_ssl(ssl_context)
                logger.info(f"HSPConnector ({self.ai_id}): TLS configured.")

            if username and password:
                logger.info(f"HSPConnector ({self.ai_id}): Username and password configured.")
        else:
            self.mqtt_client = MagicMock()
            self.is_connected = True

        # Callbacks for different types of HSP messages
        self._on_generic_message_callback: Optional[Callable[[HSPMessageEnvelope, str], None]] = None
        self._on_fact_received_callback: Optional[Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]] = None
        self._on_capability_advertisement_callback: Optional[Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_request_callback: Optional[Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]] = None
        self._on_task_result_callback: Optional[Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]] = None
        self._external_on_connect_callback: Optional[Callable[[], None]] = None
        self._external_on_disconnect_callback: Optional[Callable[[], None]] = None
        # ... other specific payload callbacks can be added

        self.default_qos: int = 1 # MQTT QoS level for publishing

        # For managing subscriptions
        self.subscribed_topics: set[str] = set()
        self._was_unexpectedly_disconnected: bool = False
        self._heartbeat_task: Optional[asyncio.Task] = None

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

    async def on_connect(self, client, flags):
        """Callback for when the client receives a CONNACK response from the server."""
        self.is_connected = True
        if self._was_unexpectedly_disconnected:
            logger.info(f"HSPConnector ({self.ai_id}): Successfully reconnected to MQTT Broker")
            self._was_unexpectedly_disconnected = False
        else:
            logger.info(f"HSPConnector ({self.ai_id}): Successfully connected to MQTT Broker")

        # Resubscribe to topics upon successful reconnection
        if self.subscribed_topics:
            logger.info(f"HSPConnector ({self.ai_id}): Resubscribing to {len(self.subscribed_topics)} topics...")
            for topic in list(self.subscribed_topics):
                await self.subscribe(topic, self.default_qos)

        if self._external_on_connect_callback:
            try:
                await self._external_on_connect_callback()
            except Exception as e:
                logger.error(f"HSPConnector ({self.ai_id}): Error in external on_connect callback: {e}", exc_info=True)

    async def on_disconnect(self, client, packet, rc=None):
        """Callback for when the client disconnects from the broker."""
        self.is_connected = False
        if rc == 0:
            logger.info(f"HSPConnector ({self.ai_id}): Cleanly disconnected from MQTT Broker (reason code {rc})")
            self._was_unexpectedly_disconnected = False
        else:
            logger.warning(f"HSPConnector ({self.ai_id}): Unexpectedly disconnected from MQTT Broker (reason code {rc})")
            logger.info("Client will attempt to reconnect automatically")
            self._was_unexpectedly_disconnected = True

        if self._external_on_disconnect_callback:
            try:
                await self._external_on_disconnect_callback()
            except Exception as e:
                logger.error(f"HSPConnector ({self.ai_id}): Error in external on_disconnect callback: {e}", exc_info=True)
    async def on_message(self, client, topic, payload, qos, properties):
        """Callback for when a PUBLISH message is received from the server."""
        logger.debug(f"HSPConnector ({self.ai_id}): Received raw message on topic '{topic}'")
        try:
            # gmqtt payload is bytes, decode to string
            message_str = payload.decode("utf-8")

            if topic.startswith("hsp/acks/"):
                logger.info(f"HSPConnector ({self.ai_id}): Received acknowledgement on topic {topic}")
                # Potentially process the ACK, e.g., update a message status
                return

            # For all other topics, handle as a standard HSP message
            await self._handle_hsp_message_str(message_str, topic)

        except UnicodeDecodeError:
            logger.error(f"HSPConnector ({self.ai_id}): Could not decode message payload on topic '{topic}' as UTF-8.")
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error processing message on topic '{topic}': {e}", exc_info=True)

    async def connect(self) -> bool:
        """Establishes a connection to the MQTT broker(s)."""
        if self.mock_mode:
            # In mock mode, we still want to simulate the connection process
            # by calling the mock client's connect method
            try:
                await self.mqtt_client.connect(host=self.broker_address, port=self.broker_port)
                self.is_connected = True
                logger.info(f"HSPConnector ({self.ai_id}): Running in MOCK mode. Connection is simulated.")
                return True
            except Exception as e:
                logger.error(f"HSPConnector ({self.ai_id}): Mock connection failed: {e}")
                self.is_connected = False
                return False

        if self.is_connected:
            logger.info(f"HSPConnector ({self.ai_id}): Already connected.")
            return True

        brokers_to_try = self.broker_list or [{'address': self.broker_address, 'port': self.broker_port}]


        for broker_info in brokers_to_try:
            address = broker_info.get('address', self.broker_address)
            port = broker_info.get('port', self.broker_port)
            logger.info(f"HSPConnector ({self.ai_id}): Attempting to connect to {address}:{port}...")
            try:
                await self.mqtt_client.connect(host=address, port=port)
                # The on_connect callback will set is_connected to True
                # gmqtt handles the connection in the background, we just need to wait for the on_connect callback.
                # A short sleep can be useful, but a more robust solution would use an asyncio.Event
                await asyncio.sleep(1) # Give time for on_connect to fire
                if self.is_connected:
                    logger.info(f"HSPConnector ({self.ai_id}): Connection successful to {address}:{port}.")
                    return True
                else:
                    logger.warning(f"HSPConnector ({self.ai_id}): Connection attempt to {address}:{port} did not succeed within the expected time.")
            except Exception as e:
                logger.error(f"HSPConnector ({self.ai_id}): Error connecting to MQTT broker at {address}:{port}: {e}", exc_info=True)
                continue # Try next broker

        logger.error(f"HSPConnector ({self.ai_id}): Failed to connect to any of the provided MQTT brokers.")
        return False

    async def disconnect(self) -> None:
        """Disconnects from the MQTT broker."""
        if self.mock_mode:
            self.is_connected = False
            logger.info(f"HSPConnector ({self.ai_id}): MOCK mode disconnect.")
            return

        if self.mqtt_client.is_connected():
            logger.info(f"HSPConnector ({self.ai_id}): Disconnecting from MQTT broker.")
            await self.mqtt_client.disconnect()
        else:
            logger.info(f"HSPConnector ({self.ai_id}): Already disconnected.")

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

    async def _send_hsp_message(self, envelope: HSPMessageEnvelope, mqtt_topic: str, mqtt_qos: Optional[int] = None) -> bool:
        """Sends a pre-built HSP envelope over MQTT."""
        if self.mock_mode:
            return True
        if not self.is_connected:
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot send message to {mqtt_topic}.")
            return False

        message_str = json.dumps(envelope)
        effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos

        try:
            self.mqtt_client.publish(mqtt_topic, payload=message_str, qos=effective_mqtt_qos)
            logger.info(f"HSPConnector ({self.ai_id}): Message {envelope.get('message_id')} published to topic '{mqtt_topic}' (QoS: {effective_mqtt_qos}).")
            return True
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error sending MQTT message to topic '{mqtt_topic}': {e}", exc_info=True)
            return False

    async def publish_fact(self, fact_payload: HSPFactPayload, topic: str, fact_payload_version: str = "0.1") -> bool:
        """Publishes a Fact payload to a given HSP topic via MQTT."""
        message_type = f"HSP::Fact_v{fact_payload_version}"
        envelope = self._build_hsp_envelope(
            payload=dict(fact_payload),
            message_type=message_type,
            recipient_ai_id_or_topic=topic,
            communication_pattern="publish"
        )
        return await self._send_hsp_message(envelope, mqtt_topic=topic)

    async def subscribe(self, topic: str, mqtt_qos: Optional[int] = None) -> bool:
        """Subscribes to an MQTT topic to receive HSP messages."""
        if self.mock_mode:
            self.subscribed_topics.add(topic)
            return True
        if not self.is_connected:
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot subscribe to topic '{topic}'.")
            return False
        try:
            effective_mqtt_qos = mqtt_qos if mqtt_qos is not None else self.default_qos
            await self.mqtt_client.subscribe(topic, qos=effective_mqtt_qos)
            self.subscribed_topics.add(topic)
            logger.info(f"HSPConnector ({self.ai_id}): Successfully subscribed to topic '{topic}' with QoS {effective_mqtt_qos}")
            return True
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error subscribing to topic '{topic}': {e}", exc_info=True)
            return False

    async def unsubscribe(self, topic: str) -> bool:
        """Unsubscribes from an MQTT topic."""
        if self.mock_mode:
            if topic in self.subscribed_topics:
                self.subscribed_topics.remove(topic)
            return True
        if not self.is_connected:
            logger.warning(f"HSPConnector ({self.ai_id}): Not connected. Cannot unsubscribe from topic '{topic}'.")
            if topic in self.subscribed_topics:
                self.subscribed_topics.remove(topic)
            return False
        try:
            await self.mqtt_client.unsubscribe(topic)
            if topic in self.subscribed_topics:
                self.subscribed_topics.remove(topic)
            logger.info(f"HSPConnector ({self.ai_id}): Successfully unsubscribed from topic '{topic}'")
            return True
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Error unsubscribing from topic '{topic}': {e}", exc_info=True)
            return False

    async def _handle_hsp_message_str(self, message_str: str, received_on_topic: str):
        """Deserializes and processes an incoming HSP message string."""
        try:
            envelope: HSPMessageEnvelope = json.loads(message_str)
            if not all(k in envelope for k in ["message_id", "sender_ai_id", "message_type", "payload"]):
                logger.warning(f"HSPConnector ({self.ai_id}): Received message with missing core envelope fields from topic '{received_on_topic}'. Message snippet: {message_str[:200]}")
                return

            message_type = envelope.get("message_type", "UNKNOWN") # Ensure message_type is always set
            logger.info(f"HSPConnector ({self.ai_id}): Decoded HSP message {envelope['message_id']} from {envelope['sender_ai_id']} on topic '{received_on_topic}'. Type: {message_type}")

            if self._on_generic_message_callback:
                try:
                    self._on_generic_message_callback(envelope, received_on_topic)
                except Exception as e:
                    logger.error(f"HSPConnector ({self.ai_id}): Error in generic message callback for msg {envelope.get('message_id')}: {e}", exc_info=True)

            payload = envelope.get("payload")

            if message_type != "UNKNOWN" and payload is not None:
                specific_handler_error = None
                try:
                    if message_type.startswith("HSP::Fact") and self._on_fact_received_callback:
                        logger.debug(f"HSPConnector ({self.ai_id}): Dispatching Fact message.")
                        self._on_fact_received_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::CapabilityAdvertisement") and self._on_capability_advertisement_callback:
                        logger.debug(f"HSPConnector ({self.ai_id}): Dispatching CapabilityAdvertisement message.")
                        self._on_capability_advertisement_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::TaskRequest") and self._on_task_request_callback:
                        logger.debug(f"HSPConnector ({self.ai_id}): Dispatching TaskRequest message.")
                        self._on_task_request_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    elif message_type.startswith("HSP::TaskResult") and self._on_task_result_callback:
                        logger.debug(f"HSPConnector ({self.ai_id}): Dispatching TaskResult message.")
                        self._on_task_result_callback(payload, envelope["sender_ai_id"], envelope) # type: ignore
                    # Add other specific handlers here
                except Exception as e:
                    specific_handler_error = e
                    logger.error(f"HSPConnector ({self.ai_id}): Error in specific callback for {message_type} msg {envelope.get('message_id')}: {e}", exc_info=True)

            qos_params = envelope.get("qos_parameters", {})
            if isinstance(qos_params, dict) and qos_params.get("requires_ack"):
                await self._send_acknowledgement(
                    target_ai_id=envelope["sender_ai_id"],
                    acknowledged_message_id=envelope["message_id"],
                    status="received", # "processed" might be too strong if specific_handler_error occurred
                    ack_topic=f"hsp/acks/{envelope['sender_ai_id']}"
                )

        except json.JSONDecodeError:
            logger.error(f"HSPConnector ({self.ai_id}): Received invalid JSON on topic '{received_on_topic}': {message_str[:200]}...")
        except Exception as e:
            logger.error(f"HSPConnector ({self.ai_id}): Unhandled error processing HSP message from topic '{received_on_topic}': {e}", exc_info=True)

    async def _send_acknowledgement(self, target_ai_id: str, acknowledged_message_id: str, status: Literal["received", "processed"], ack_topic: str, version: str = "0.1"):
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
        if not await self._send_hsp_message(envelope, mqtt_topic=ack_topic):
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

    def register_on_connect_callback(self, callback: Callable[[], None]):
        """Registers an external callback to be called when the MQTT client connects."""
        self._external_on_connect_callback = callback

    def register_on_disconnect_callback(self, callback: Callable[[], None]):
        """Registers an external callback to be called when the MQTT client disconnects."""
        self._external_on_disconnect_callback = callback

    def get_broker_for_ai(self, ai_id: str, get_all: bool = False) -> any:
        """
        Returns the address of the MQTT broker that the AI should connect to.
        This is a simple load balancing mechanism that distributes the AI instances across multiple brokers.
        """
        if not self.broker_list:
            if get_all:
                return [{"address": self.broker_address, "type": "primary"}]
            return self.broker_address

        primary_brokers = [b for b in self.broker_list if b.get("type") == "primary"]
        backup_brokers = [b for b in self.broker_list if b.get("type") == "backup"]
        other_brokers = [b for b in self.broker_list if b.get("type") not in ["primary", "backup"]]

        all_brokers = primary_brokers + backup_brokers + other_brokers

        if get_all:
            return all_brokers

        # This is a simple example of a load balancing mechanism.
        # In a real-world application, you would want to use a more sophisticated mechanism,
        # such as a service discovery system.
        if not all_brokers:
            return None

        broker_index = hash(ai_id) % len(all_brokers)
        return all_brokers[broker_index]["address"]

    async def _send_heartbeat(self, interval: int):
        """Periodically sends a heartbeat message."""
        while self.is_connected:
            heartbeat_payload = {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
            envelope = self._build_hsp_envelope(
                payload=heartbeat_payload,
                message_type="HSP::Heartbeat_v0.1",
                recipient_ai_id_or_topic=f"hsp/heartbeats/{self.ai_id}",
                communication_pattern="publish"
            )
            self._send_hsp_message(envelope, mqtt_topic=f"hsp/heartbeats/{self.ai_id}")
            await asyncio.sleep(interval)

    def start_heartbeat(self, interval: int = 60):
        """Starts the heartbeat mechanism."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._send_heartbeat(interval))
            logger.info(f"HSPConnector ({self.ai_id}): Heartbeat started with interval {interval}s.")

    def stop_heartbeat(self):
        """Stops the heartbeat mechanism."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            logger.info(f"HSPConnector ({self.ai_id}): Heartbeat stopped.")

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

    # The connect method is now awaitable and handles connection logic.
    if await connector.connect():
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
        await connector.publish_fact(sample_fact_payload, topic=general_facts_topic)

        print("\nPublishing another sample fact to a specific weather subtopic...")
        specific_weather_fact: HSPFactPayload = { # Changed FactPayload to HSPFactPayload
          "id": f"fact_temp_{uuid.uuid4().hex[:6]}",  # Use hex for shorter UUID part
          "statement_type": "semantic_triple",
          "statement_structured": {"subject_uri": "hsp:env:city_A_temp", "predicate_uri": "hsp:property:hasValueCelsius", "object_literal": 25}, # type: ignore
          "timestamp_created": datetime.now(timezone.utc).isoformat(),
          "confidence_score": 0.99,
        }
        await connector.publish_fact(specific_weather_fact, topic="hsp/knowledge/facts/weather/city_A/temperature")

        print("\nExample running. Listening for messages for 20 seconds...")
        print("Try publishing messages to the subscribed topics using an MQTT client (e.g., MQTT Explorer or mosquitto_pub).")
        print(f"  mosquitto_pub -h localhost -t '{general_facts_topic}' -m '{{\"hsp_envelope_version\": \"0.1\", ...}}'")
        await asyncio.sleep(20)

        await connector.disconnect()
        print("HSP Connector example finished.")
    else:
        print("Failed to connect to MQTT broker for example.")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure you have an MQTT broker running (e.g., `docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto`)
    # 2. Install paho-mqtt: `pip install paho-mqtt`
    # 3. Uncomment the next line to run:
    # asyncio.run(example_hsp_usage())
    pass
