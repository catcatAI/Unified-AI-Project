import json # Added for JSON serialization
from typing import Callable, Dict, Any, Optional, List # Added Optional, List
from .external.external_connector import ExternalConnector
from .internal.internal_bus import InternalBus
from .bridge.data_aligner import DataAligner
from .bridge.message_bridge import MessageBridge
from unittest.mock import MagicMock, AsyncMock # Added for mock_mode
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPAcknowledgementPayload
import uuid # Added for UUID generation
from datetime import datetime, timezone # Added for timestamp generation
import asyncio # Added for asyncio.iscoroutinefunction
import logging
import time
from src.shared.error import HSPConnectionError # Added for unified error handling
from src.shared.network_resilience import RetryPolicy, CircuitBreaker, NetworkError, ProtocolError, CircuitBreakerOpenError # New imports for resilience
from .fallback.fallback_protocols import get_fallback_manager, FallbackMessage, MessagePriority, initialize_fallback_protocols
from .utils.fallback_config_loader import get_config_loader
from pathlib import Path
import os # Added this import

# Define the base path for schemas, ensuring cross-platform compatibility
SCHEMA_BASE_PATH = Path(__file__).resolve().parent.parent.parent / "schemas"

def get_schema_uri(schema_name: str) -> str:
    """Constructs a file URI for a given schema name."""
    schema_path = SCHEMA_BASE_PATH / schema_name
    if not schema_path.is_file():
        # Fallback for when running in a different environment (like tests)
        # This makes the path relative to the current working directory
        # In a real-world scenario, a more robust solution might be needed
        # like using an environment variable or a configuration setting.
        project_root = Path.cwd()
        schema_path = project_root / "apps" / "backend" / "schemas" / schema_name
        if not schema_path.is_file():
             # As a last resort, return a placeholder if the file isn't found
             # This prevents crashes but signals a configuration issue.
             logging.warning(f"Schema file not found: {schema_name}. Path was: {schema_path}")
             return f"file:///{schema_name}_not_found"
    return schema_path.as_uri()

class HSPConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int, mock_mode: bool = False, mock_mqtt_client: Optional[MagicMock] = None, internal_bus: Optional[InternalBus] = None, message_bridge: Optional[MessageBridge] = None, enable_fallback: bool = True, **kwargs):
        self.ai_id = ai_id
        self.mock_mode = mock_mode
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.enable_fallback = enable_fallback
        self.fallback_manager = None
        self.fallback_initialized = False
        self.logger = logging.getLogger(__name__)
        self.hsp_available = False  # Track HSP availability

        if self.mock_mode:
            self.logger.info("HSPConnector: Initializing in mock mode.")
            self.logger.debug(f"HSPConnector.__init__ - ai_id: {ai_id}, mock_mode: {mock_mode}")
            self.external_connector = MagicMock(spec=ExternalConnector)
            self.external_connector.ai_id = ai_id # Ensure mock has ai_id
            self.external_connector.connect.return_value = True
            self.external_connector.disconnect.return_value = True
            self.external_connector.subscribe.return_value = True
            self.external_connector.unsubscribe.return_value = True
            self.external_connector.publish = AsyncMock(return_value=True) # Explicitly set return value for publish
            # Explicitly mock mqtt_client and its publish method
            if mock_mqtt_client:
                self.external_connector.mqtt_client = mock_mqtt_client
            else:
                mock_mqtt_client_instance = MagicMock()
                mock_mqtt_client_instance.publish = AsyncMock(return_value=True)
                self.external_connector.mqtt_client = mock_mqtt_client_instance
            
            self.is_connected = True # Considered connected in mock mode
            self.hsp_available = True  # Mock mode considers HSP available
        else:
            self.external_connector = ExternalConnector(
                ai_id=ai_id,
                broker_address=broker_address,
                broker_port=broker_port,
                )
            self.is_connected = False # Actual connection status
            self.hsp_available = False

        if internal_bus is None:
            self.internal_bus = InternalBus()
        else:
            self.internal_bus = internal_bus

        self.data_aligner = DataAligner() # DataAligner can be unique per connector

        if message_bridge is None:
            self.message_bridge = MessageBridge(
                self.external_connector,
                self.internal_bus,
                self.data_aligner
            )
        else:
            self.message_bridge = message_bridge

        # Callbacks for different message types
        self._fact_callbacks = []
        self._capability_advertisement_callbacks = []
        self._task_request_callbacks = []
        self._task_result_callbacks = []
        self._acknowledgement_callbacks = [] # New: for incoming ACKs
        self._connect_callbacks = []
        self._disconnect_callbacks = []

        self._pending_acks: Dict[str, asyncio.Future] = {} # New: To track messages awaiting ACK
        self._message_retry_counts: Dict[str, int] = {} # New: To track retry counts for messages
        self.ack_timeout_sec = 10 # New: Default timeout for ACK
        self.max_ack_retries = 3 # New: Max retries for messages requiring ACK
        self.retry_policy = RetryPolicy(max_attempts=self.max_ack_retries, backoff_factor=2, max_delay=60) # Initialize retry policy
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300) # Initialize circuit breaker
        self._capability_provider_callback: Optional[Callable[[], List[HSPCapabilityAdvertisementPayload]]] = None # New: Callback to get capabilities
        
        # Initialize fallback protocols if enabled
        # Moved to connect() method to ensure event loop is running

        # Register internal message bridge handler for external messages
        self.external_connector.on_message_callback = self.message_bridge.handle_external_message

        # Subscribe to internal bus messages that need to go external
        self.internal_bus.subscribe("hsp.internal.message", self.message_bridge.handle_internal_message)

        # Subscribe to internal bus messages that are results from external
        self.internal_bus.subscribe("hsp.external.fact", self._dispatch_fact_to_callbacks)
        self.internal_bus.subscribe("hsp.external.capability_advertisement", self._dispatch_capability_advertisement_to_callbacks)
        self.internal_bus.subscribe("hsp.external.task_request", self._dispatch_task_request_to_callbacks)
        self.internal_bus.subscribe("hsp.external.task_result", self._dispatch_task_result_to_callbacks)
        self.internal_bus.subscribe("hsp.external.acknowledgement", self._dispatch_acknowledgement_to_callbacks) # New subscription

    # --- Test compatibility properties ---
    @property
    def default_qos(self):
        """Default QoS level for test compatibility."""
        return 1
    
    @property
    def mqtt_client(self):
        """Provides access to the underlying MQTT client for test compatibility."""
        return self.external_connector.mqtt_client
    
    @mqtt_client.setter
    def mqtt_client(self, value):
        """Allows tests to set the mock MQTT client."""
        self.external_connector.mqtt_client = value
    
    @property
    def subscribed_topics(self):
        """Provides access to subscribed topics for test compatibility."""
        return getattr(self.external_connector, 'subscribed_topics', set())
    
    @property
    def on_message(self):
        """Provides message callback for test compatibility."""
        # Tests expect signature: on_message(client, topic, payload, qos, properties)
        # MessageBridge.handle_external_message expects: handle_external_message(topic, message)
        async def test_compatible_on_message(client, topic, payload, qos, properties):
            topic_str = topic.decode() if isinstance(topic, (bytes, bytearray)) else topic
            payload_str = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
            await self.external_connector.on_message_callback(topic_str, payload_str)
        return test_compatible_on_message

    @on_message.setter  
    def on_message(self, callback):
        """Allows setting message callback for test compatibility."""
        # Wrap a test-provided callback (client, topic, payload, qos, properties)
        async def wrapper(topic, message):
            await callback(None, topic, message, 1, None)
        self.external_connector.on_message_callback = wrapper
    
    # --- Backward compatibility methods ---
    def on_fact_received(self, callback):
        """Backward compatibility method for registering fact callbacks."""
        self.register_on_fact_callback(callback)
        
    def on_command_received(self, callback):
        """Backward compatibility method for registering command callbacks (maps to task_request)."""
        self.register_on_task_request_callback(callback)
        
    def on_connect_callback(self, callback):
        """Backward compatibility method for registering connect callbacks.""" 
        self.register_on_connect_callback(callback)
        
    def on_disconnect_callback(self, callback):
        """Backward compatibility method for registering disconnect callbacks."""
        self.register_on_disconnect_callback(callback)

    async def mqtt_subscribe(self, topic: str, qos: int = 1):
        """Direct MQTT subscription for test compatibility."""
        if self.mock_mode:
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector, 'subscribed_topics'):
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            await self.external_connector.subscribe(topic, qos)
        else:
            if hasattr(self.external_connector, 'subscribe'):
                await self.external_connector.subscribe(topic, qos)

    # Test compatibility methods for direct MQTT callback simulation
    async def on_connect(self, client, userdata, flags, rc):
        """MQTT client on_connect callback for test compatibility."""
        for callback in self._connect_callbacks:
            await callback()

    async def on_disconnect(self, client, userdata, rc):
        """MQTT client on_disconnect callback for test compatibility."""
        for callback in self._disconnect_callbacks:
            try:
                await callback()
            except Exception as e:
                self.logger.warning(f"Disconnect callback error: {e}")

    async def connect(self):
        if self.mock_mode:
            self.logger.info("HSPConnector: Mock connect successful.")
            self.is_connected = True
            self.hsp_available = True
            if self.enable_fallback:
                await self._initialize_fallback_protocols()
            # In mock mode, explicitly subscribe to relevant topics on the mock MQTT client
            await self.external_connector.subscribe("hsp/knowledge/facts/#", self.external_connector.on_message_callback)
            await self.external_connector.subscribe("hsp/capabilities/advertisements/#", self.external_connector.on_message_callback)
            await self.external_connector.subscribe(f"hsp/requests/{self.ai_id}", self.external_connector.on_message_callback)
            await self.external_connector.subscribe(f"hsp/results/{self.ai_id}", self.external_connector.on_message_callback)
        else:
            for attempt in range(3):
                try:
                    self.logger.info(f"Attempting to connect to HSP... (Attempt {attempt + 1}/3)")
                    await self.external_connector.connect()
                    self.is_connected = self.external_connector.is_connected
                    self.hsp_available = self.is_connected
                    if self.is_connected:
                        self.logger.info("HSP connection successful.")
                        if self.enable_fallback:
                            await self._initialize_fallback_protocols()
                        break  # Exit loop on successful connection
                except Exception as e:
                    self.logger.error(f"HSP connection attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        await self._handle_hsp_connection_error(e, attempt + 1)
                    else:
                        self.logger.warning(f"HSP connection attempt {attempt + 1} failed: {e}. Retrying...")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # If still not connected after retries, ensure fallback is initialized
            if not self.is_connected and self.enable_fallback:
                 await self._initialize_fallback_protocols()
        
        for callback in self._connect_callbacks:
            await callback()

        # New: Perform post-connection synchronization
        await self._post_connect_synchronization()

    async def disconnect(self):
        if self.mock_mode:
            self.logger.info("HSPConnector: Mock disconnect successful.")
            self.is_connected = False
        else:
            try:
                await self.external_connector.disconnect()
            except Exception as e:
                self.logger.warning(f"HSPConnector: external disconnect raised (likely already closed): {e}")
            finally:
                # Reflect underlying state or force false
                try:
                    self.is_connected = bool(getattr(self.external_connector, 'is_connected', False))
                except Exception:
                    self.is_connected = False

        if self.fallback_manager and self.fallback_initialized:
            try:
                await self.fallback_manager.shutdown()
            except Exception as e:
                self.logger.warning(f"HSPConnector: fallback shutdown error: {e}")
            finally:
                self.fallback_initialized = False

        for callback in self._disconnect_callbacks:
            try:
                await callback()
            except Exception as e:
                self.logger.warning(f"HSPConnector: disconnect callback error: {e}")

    async def publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        logging.info(f"HSPConnector: publish_message called. self.external_connector.publish is {type(self.external_connector.publish)}")
        
        message_id = envelope.get("message_id")
        correlation_id = envelope.get("correlation_id") or message_id # Use message_id if correlation_id is not set
        qos_params = envelope.get("qos_parameters") or {}
        requires_ack = qos_params.get("requires_ack", False)
        
        # Initialize retry count for this message if it's new - still needed for fallback retry
        if correlation_id not in self._message_retry_counts:
            self._message_retry_counts[correlation_id] = 0

        # Apply Circuit Breaker and Retry Policy to the raw publish attempt
        # This ensures that external_connector.publish attempts are resilient
        try:
            # The decorated function will handle retries and circuit breaking for the direct publish
            await self.circuit_breaker(self.retry_policy(self._raw_publish_message))(topic, envelope, qos)
            self.logger.debug(f"Message {correlation_id} published via HSP (decorated).")

            if requires_ack:
                ack_future = asyncio.Future()
                self._pending_acks[correlation_id] = ack_future
                try:
                    await asyncio.wait_for(ack_future, timeout=self.ack_timeout_sec)
                    self.logger.info(f"ACK received for message {correlation_id}.")
                    del self._message_retry_counts[correlation_id] # Clear retry count on success
                    return True
                except asyncio.TimeoutError:
                    self.logger.warning(f"ACK timeout for message {correlation_id}. Trying fallback if enabled.")
                    # No retry here, as retry policy already handled the raw publish. Now try fallback.
                    if self.enable_fallback and self.fallback_manager:
                        fallback_success = await self._send_via_fallback(topic, envelope, qos)
                        if fallback_success:
                            self.logger.info(f"Message {correlation_id} sent via fallback after ACK timeout.")
                            del self._message_retry_counts[correlation_id]
                            return True
                        else:
                            self.logger.error(f"Fallback also failed for message {correlation_id} after ACK timeout.")
                            return False
                    else:
                        self.logger.error(f"No fallback or fallback disabled for message {correlation_id} after ACK timeout.")
                        return False
                finally:
                    # Ensure future is removed even if cancelled or exception
                    if correlation_id in self._pending_acks:
                        del self._pending_acks[correlation_id]
            else:
                self.logger.debug(f"Message {correlation_id} does not require ACK.")
                del self._message_retry_counts[correlation_id] # Clear retry count
                return True

        except (NetworkError, CircuitBreakerOpenError) as e:
            self.logger.error(f"HSP publish failed for {correlation_id} due to network resilience policy: {e}. Trying fallback.")
            if self.enable_fallback and self.fallback_manager:
                fallback_success = await self._send_via_fallback(topic, envelope, qos)
                if fallback_success:
                    self.logger.info(f"Message {correlation_id} sent via fallback after HSP resilience failure.")
                    del self._message_retry_counts[correlation_id]
                    return True
                else:
                    self.logger.error(f"Fallback also failed for message {correlation_id} after HSP resilience failure.")
                    return False
            else:
                self.logger.error(f"HSP not available and fallback disabled/failed for {correlation_id}.")
                return False
        except Exception as e:
            self.logger.critical(f"Unhandled critical error during message publish for {correlation_id}: {e}")
            # For any other unexpected errors, clean up and fail.
            if correlation_id in self._message_retry_counts:
                del self._message_retry_counts[correlation_id]
            raise # Re-raise unexpected errors


    async def _raw_publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        """Internal method for raw message publishing prioritizing mqtt_client.publish for tests, with fallback to external_connector.publish."""
        try:
            payload_bytes = json.dumps(envelope).encode('utf-8')
            # Access mqtt_client correctly via property which handles external_connector access
            mqtt_client = self.mqtt_client
            if mqtt_client and hasattr(mqtt_client, 'publish'):
                await mqtt_client.publish(topic, payload_bytes, qos=qos)
            elif hasattr(self.external_connector, 'publish'):
                await self.external_connector.publish(topic, payload_bytes, qos=qos)
            else:
                raise NetworkError("No available publish method on MQTT client or external connector")
            self.logger.debug(f"Raw message {envelope.get('message_id')} published via HSP.")
            return True
        except Exception as e:
            self.logger.error(f"Raw HSP publish failed for {envelope.get('message_id')}: {e}")
            # This is where NetworkError or ProtocolError would be raised by the external_connector
            # For now, re-raise as a generic exception, or as a specific NetworkError if needed.
            raise NetworkError(f"Failed to publish message: {e}") from e

    async def publish_fact(self, fact_payload: HSPFactPayload, topic: str, qos: int = 1):
        # Construct a minimal envelope for the fact
        envelope: HSPMessageEnvelope = { #type: ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all", # Facts are often broadcast
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::Fact_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"}, # Facts usually don't require ACK
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_Fact_v0.1.schema.json"),
            "payload": fact_payload
        }
        # New: also echo to internal bus for in-process consumers/tests
        await self.internal_bus.publish_async("hsp.internal.fact", envelope)
        return await self.publish_message(topic, envelope, qos)

    async def send_task_request(self, payload: HSPTaskRequestPayload, target_ai_id_or_topic: str, qos: int = 1) -> Optional[str]:
        correlation_id = str(uuid.uuid4())
        envelope: HSPMessageEnvelope = { #type: ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": payload.get("target_ai_id", target_ai_id_or_topic),
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskRequest_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "request",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": True, "priority": "high"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskRequest_v0.1.schema.json"),
            "payload": payload
        }
        # The topic for task requests is usually hsp/requests/{recipient_ai_id}
        # If target_ai_id_or_topic is a topic, use it directly.
        # Otherwise, construct the topic.
        mqtt_topic = target_ai_id_or_topic if "/" in target_ai_id_or_topic else f"hsp/requests/{target_ai_id_or_topic}"
        
        success = await self.publish_message(mqtt_topic, envelope, qos)
        return correlation_id if success else None

    async def send_task_result(self, payload: HSPTaskResultPayload, target_ai_id_or_topic: str, correlation_id: str, qos: int = 1) -> bool:
        envelope: HSPMessageEnvelope = { #type: ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": payload.get("requester_ai_id", target_ai_id_or_topic),
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "response",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "high"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskResult_v0.1.schema.json"),
            "payload": payload
        }
        mqtt_topic = target_ai_id_or_topic if "/" in target_ai_id_or_topic else f"hsp/results/{target_ai_id_or_topic}"
        return await self.publish_message(mqtt_topic, envelope, qos)

    async def publish_capability_advertisement(self, cap_payload: HSPCapabilityAdvertisementPayload, qos: int = 1):
        topic = f"hsp/capabilities/advertisements/{self.ai_id}" # Specific topic for this AI's capabilities
        envelope: HSPMessageEnvelope = { #type: ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::CapabilityAdvertisement_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_CapabilityAdvertisement_v0.1.schema.json"),
            "payload": cap_payload
        }
        return await self.publish_message(topic, envelope, qos)

    async def subscribe(self, topic: str, callback: Optional[Callable] = None):
        """
        Subscribe to a topic.
        - If callback is provided: subscribe on internal bus for bridged messages.
        - If no callback: perform direct MQTT subscription for test compatibility.
        """
        if callback is None:
            # Direct MQTT subscription path (tests expect this)
            if self.mock_mode:
                if not hasattr(self.external_connector, 'subscribed_topics'):
                    self.external_connector.subscribed_topics = set()
                self.external_connector.subscribed_topics.add(topic)
            # Prefer calling underlying MQTT client's subscribe so tests can assert it
            mqtt_client = getattr(self, 'mqtt_client', None)
            if mqtt_client and hasattr(mqtt_client, 'subscribe'):
                await mqtt_client.subscribe(topic, self.default_qos)
            elif hasattr(self.external_connector, 'subscribe'):
                await self.external_connector.subscribe(topic, self.default_qos)
        else:
            # Internal bus subscription path
            self.internal_bus.subscribe(f"hsp.external.{topic}", callback)

    def unsubscribe(self, topic: str, callback: Optional[Callable] = None):
        if callback is None:
            # Direct MQTT unsubscribe compatibility (best-effort in mock)
            if self.mock_mode and hasattr(self.external_connector, 'subscribed_topics'):
                self.external_connector.subscribed_topics.discard(topic)
            # If external connector has unsubscribe, call it
            if hasattr(self.external_connector, 'unsubscribe'):
                try:
                    self.external_connector.unsubscribe(topic)
                except Exception:
                    pass
        else:
            self.internal_bus.unsubscribe(f"hsp.external.{topic}", callback)

    # --- Registration methods for external modules to receive specific message types ---
    def register_on_fact_callback(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]):
        self.logger.debug(f"Registering on_fact_callback: {callback}")
        self._fact_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback: Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]):
        self.logger.debug(f"Registering on_capability_advertisement_callback: {callback}")
        self._capability_advertisement_callbacks.append(callback)

    def register_on_task_request_callback(self, callback: Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]):
        self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]):
        self._task_result_callbacks.append(callback)

    def register_on_connect_callback(self, callback: Callable[[], None]):
        self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback: Callable[[], None]):
        self._disconnect_callbacks.append(callback)

    def register_on_acknowledgement_callback(self, callback: Callable[[HSPAcknowledgementPayload, str, HSPMessageEnvelope], None]):
        self._acknowledgement_callbacks.append(callback)

    def register_capability_provider(self, callback: Callable[[], List[HSPCapabilityAdvertisementPayload]]):
        """Registers a callback function that provides the AI's current capabilities."""
        self._capability_provider_callback = callback

    async def advertise_capability(self, capability: HSPCapabilityAdvertisementPayload):
        """Publishes a capability advertisement."""
        await self.publish_capability_advertisement(capability)

    # --- Internal dispatch methods ---
    async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any]):
        # message here is the full envelope from the internal bus
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching fact to {len(self._fact_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:
            fact_payload = HSPFactPayload(**payload)
            for callback in self._fact_callbacks:
                self.logger.debug(f"Calling on_fact_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(fact_payload, sender_ai_id, message)
                else:
                    callback(fact_payload, sender_ai_id, message)

            # Check if ACK is required and send it
            qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):
                ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching capability advertisement to {len(self._capability_advertisement_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:
            cap_payload = HSPCapabilityAdvertisementPayload(**payload)
            for callback in self._capability_advertisement_callbacks:
                self.logger.debug(f"Calling on_capability_advertisement_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(cap_payload, sender_ai_id, message)
                else:
                    callback(cap_payload, sender_ai_id, message)

            # Check if ACK is required and send it
            qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):
                ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching task request to {len(self._task_request_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:
            task_payload = HSPTaskRequestPayload(**payload)
            for callback in self._task_request_callbacks:
                self.logger.debug(f"Calling on_task_request_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_payload, sender_ai_id, message)
                else:
                    callback(task_payload, sender_ai_id, message)

            # Check if ACK is required and send it
            qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):
                ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching task result to {len(self._task_result_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:
            result_payload = HSPTaskResultPayload(**payload)
            for callback in self._task_result_callbacks:
                self.logger.debug(f"Calling on_task_result_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(result_payload, sender_ai_id, message)
                else:
                    callback(result_payload, sender_ai_id, message)

            # Check if ACK is required and send it
            qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):
                ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_acknowledgement_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching acknowledgement to {len(self._acknowledgement_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:
            ack_payload = HSPAcknowledgementPayload(**payload)
            target_message_id = ack_payload.get("target_message_id")
            correlation_id = message.get("correlation_id")

            # Resolve pending ACK if any
            if correlation_id and correlation_id in self._pending_acks:
                future = self._pending_acks.pop(correlation_id)
                if not future.done():
                    future.set_result(ack_payload) # Signal that ACK was received
                    self.logger.debug(f"Resolved pending ACK for correlation_id: {correlation_id}")
            elif target_message_id and target_message_id in self._pending_acks: # Fallback to target_message_id if correlation_id not used for ACK tracking
                future = self._pending_acks.pop(target_message_id)
                if not future.done():
                    future.set_result(ack_payload)
                    self.logger.debug(f"Resolved pending ACK for target_message_id: {target_message_id}")

            for callback in self._acknowledgement_callbacks:
                self.logger.debug(f"Calling on_acknowledgement_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(ack_payload, sender_ai_id, message)
                else:
                    callback(ack_payload, sender_ai_id, message)

    # --- Properties ---
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool):
        self._is_connected = value

    # --- Fallback Protocol Methods ---
    async def _initialize_fallback_protocols(self):
        """
        Initializes the fallback communication protocols based on the configuration.
        This is called when the primary HSP connector fails to connect.
        """
        if not self.enable_fallback:
            return
        
        try:
            # Load fallback configuration
            config_loader = get_config_loader()
            if not config_loader.is_fallback_enabled():
                self.logger.info("Fallback protocols disabled in configuration")
                return
            
            fallback_config = config_loader.get_fallback_config()
            message_config = fallback_config.get("message", {})
            
            # Set logging level for fallback protocols
            logging_config = fallback_config.get("logging", {})
            if logging_config.get("level"):
                fallback_logger = logging.getLogger("src.hsp.fallback")
                fallback_logger.setLevel(getattr(logging, logging_config["level"]))
            
            self.fallback_manager = get_fallback_manager()
            
            # Initialize protocols with the loaded configuration
            success = await self._initialize_protocols_with_config(fallback_config)
            
            if success:
                self.fallback_initialized = True
                # Register a handler for incoming fallback messages
                for _, protocol in self.fallback_manager.protocols:
                    protocol.register_handler("hsp_message", self._handle_fallback_message)
                
                # Set the health check interval for the fallback manager
                health_interval = message_config.get("health_check_interval", 30)
                self.fallback_manager.health_check_interval = health_interval
                
                self.logger.info("Fallback protocols initialized successfully with configuration")
            else:
                self.logger.error("Failed to initialize fallback protocols")
        except Exception as e:
            self.logger.error(f"Error initializing fallback protocols: {e}")

    async def _initialize_protocols_with_config(self, config: Dict[str, Any]) -> bool:
        """
        Initializes the individual fallback protocols based on the provided configuration.
        """
        try:
            from .fallback.fallback_protocols import InMemoryProtocol, FileBasedProtocol, HTTPProtocol
            
            protocols_config = config.get("protocols", {})
            
            # Initialize in-memory protocol
            memory_config = protocols_config.get("memory", {})
            if memory_config.get("enabled", True):
                memory_protocol = InMemoryProtocol()
                priority = memory_config.get("priority", 1)
                self.fallback_manager.add_protocol(memory_protocol, priority=priority)
                self.logger.debug(f"Added memory protocol with priority {priority}")
            
            # Initialize file-based protocol
            file_config = protocols_config.get("file", {})
            if file_config.get("enabled", True):
                base_path = file_config.get("base_path", "data/fallback_comm")
                file_protocol = FileBasedProtocol(base_path=base_path)
                priority = file_config.get("priority", 2)
                self.fallback_manager.add_protocol(file_protocol, priority=priority)
                self.logger.debug(f"Added file protocol with priority {priority}")
            
            # Initialize HTTP protocol
            http_config = protocols_config.get("http", {})
            if http_config.get("enabled", True):
                host = http_config.get("host", "127.0.0.1")
                # Check TESTING env var here as well
                port = 0 if os.environ.get('TESTING') == 'true' else http_config.get("port", 8765)
                http_protocol = HTTPProtocol(host=host, port=port)
                priority = http_config.get("priority", 3)
                self.fallback_manager.add_protocol(http_protocol, priority=priority)
                self.logger.debug(f"Added HTTP protocol with priority {priority}")
            
            # Initialize and start the fallback manager
            if await self.fallback_manager.initialize():
                await self.fallback_manager.start()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing protocols with config: {e}")
            return False

    async def _send_via_fallback(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        """
        Sends a message using the fallback communication protocols.
        """
        if not self.fallback_manager:
            return False
        
        try:
            # Determine the message priority
            priority = MessagePriority.NORMAL
            qos_params = envelope.get("qos_parameters")
            if qos_params:
                if qos >= 2:
                    priority = MessagePriority.HIGH
                elif qos_params.get("priority") == "high":
                    priority = MessagePriority.HIGH
                elif qos_params.get("priority") == "low":
                    priority = MessagePriority.LOW
            
            # Create a fallback message
            fallback_msg = FallbackMessage(
                id=envelope["message_id"],
                sender_id=envelope["sender_ai_id"],
                recipient_id=envelope["recipient_ai_id"],
                message_type="hsp_message",
                payload={
                    "topic": topic,
                    "envelope": envelope,
                    "qos": qos
                },
                timestamp=time.time(),
                priority=priority,
                correlation_id=envelope.get("correlation_id")
            )
            
            success = await self.fallback_manager.send_message(
                fallback_msg.recipient_id,
                fallback_msg.message_type,
                fallback_msg.payload,
                priority=fallback_msg.priority,
                correlation_id=fallback_msg.correlation_id
            )
            
            if success:
                self.logger.debug(f"Message sent via fallback: {envelope['message_id']}")
            else:
                self.logger.error(f"Failed to send message via fallback: {envelope['message_id']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending via fallback: {e}")
            return False

    async def _handle_fallback_message(self, message: FallbackMessage):
        """
        Handles a message received from a fallback protocol.
        """
        try:
            payload = message.payload
            if payload.get("envelope"):
                envelope = payload["envelope"]
                # Route the message to the internal bus, as if it was received from HSP
                await self.message_bridge.handle_external_message(
                    payload.get("topic", ""), 
                    json.dumps(envelope).encode('utf-8')
                )
                self.logger.debug(f"Processed fallback message: {message.id}")
        except Exception as e:
            self.logger.error(f"Error handling fallback message: {e}")

    def get_communication_status(self) -> Dict[str, Any]:
        """
        Returns the current communication status.
        """
        status = {
            "hsp_available": self.hsp_available,
            "is_connected": self.is_connected,
            "fallback_enabled": self.enable_fallback,
            "fallback_initialized": self.fallback_initialized
        }
        
        if self.fallback_manager:
            status["fallback_status"] = self.fallback_manager.get_status()
        
        return status

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "hsp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
        }
        
        # 检查HSP健康状态
        if self.hsp_available and self.is_connected:
            try:
                # 可以添加实际的健康检查逻辑
                health["hsp_healthy"] = True
            except:
                health["hsp_healthy"] = False
                self.hsp_available = False
        
        # 检查fallback健康状态
        if self.fallback_manager:
            try:
                fallback_status = self.fallback_manager.get_status()
                health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except:
                health["fallback_healthy"] = False
        
        health["overall_healthy"] = health["hsp_healthy"] or health["fallback_healthy"]
        return health

    async def _post_connect_synchronization(self):
        """Performs synchronization tasks after a successful connection."""
        self.logger.info("Performing post-connection synchronization...")
        
        # 1. Re-advertise Capabilities
        if self._capability_provider_callback:
            try:
                capabilities = self._capability_provider_callback()
                for cap in capabilities:
                    await self.publish_capability_advertisement(cap)
                self.logger.info(f"Re-advertised {len(capabilities)} capabilities.")
            except Exception as e:
                self.logger.error(f"Error re-advertising capabilities: {e}")
        else:
            self.logger.warning("No capability provider registered. Cannot re-advertise capabilities.")

        # 2. (Future) Re-publish important facts or request state updates
        # This would involve more complex logic, potentially interacting with the HAMMemoryManager
        # or a dedicated state synchronization module.
        self.logger.info("Post-connection synchronization complete.")

    async def _handle_hsp_connection_error(self, error: Exception, attempt: int):
        """统一 HSP 连接错误处理机制"""
        error_message = f"HSP connection error (attempt {attempt}): {error}"
        self.logger.error(error_message)
        raise HSPConnectionError(error_message)