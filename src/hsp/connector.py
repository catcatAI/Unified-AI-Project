from typing import Callable, Dict, Any, Optional # Added Optional
from .external.external_connector import ExternalConnector
from .internal.internal_bus import InternalBus
from .bridge.data_aligner import DataAligner
from .bridge.message_bridge import MessageBridge
from unittest.mock import MagicMock # Added for mock_mode
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload

class HSPConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int, mock_mode: bool = False, **kwargs):
        self.ai_id = ai_id
        self.mock_mode = mock_mode
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.default_qos = 1 # Default QoS for MQTT messages

        if self.mock_mode:
            print("HSPConnector: Initializing in mock mode.")
            self.external_connector = MagicMock(spec=ExternalConnector)
            self.external_connector.ai_id = ai_id # Ensure mock has ai_id
            self.external_connector.connect.return_value = True
            self.external_connector.disconnect.return_value = True
            self.external_connector.publish.return_value = True
            self.external_connector.subscribe.return_value = True
            self.external_connector.unsubscribe.return_value = True
            self.is_connected = True # Considered connected in mock mode
        else:
            self.external_connector = ExternalConnector(
                ai_id=ai_id,
                broker_address=broker_address,
                broker_port=broker_port,
                **kwargs
            )
            self.is_connected = False # Actual connection status

        self.internal_bus = InternalBus()
        self.data_aligner = DataAligner()
        self.message_bridge = MessageBridge(
            self.external_connector,
            self.internal_bus,
            self.data_aligner
        )

        # Callbacks for different message types
        self._fact_callbacks = []
        self._capability_advertisement_callbacks = []
        self._task_request_callbacks = []
        self._task_result_callbacks = []
        self._connect_callbacks = []
        self._disconnect_callbacks = []

        # Register internal message bridge handler for external messages
        self.external_connector.on_message_callback = self.message_bridge.handle_external_message

        # Subscribe to internal bus messages that need to go external
        self.internal_bus.subscribe("hsp.internal.message", self.message_bridge.handle_internal_message)

        # Subscribe to internal bus messages that are results from external
        self.internal_bus.subscribe("hsp.external.fact", self._dispatch_fact_to_callbacks)
        self.internal_bus.subscribe("hsp.external.capability_advertisement", self._dispatch_capability_advertisement_to_callbacks)
        self.internal_bus.subscribe("hsp.external.task_request", self._dispatch_task_request_to_callbacks)
        self.internal_bus.subscribe("hsp.external.task_result", self._dispatch_task_result_to_callbacks)

    async def connect(self):
        if self.mock_mode:
            print("HSPConnector: Mock connect successful.")
            self.is_connected = True
        else:
            await self.external_connector.connect()
            self.is_connected = self.external_connector.is_connected
        for callback in self._connect_callbacks:
            await callback()

    async def disconnect(self):
        if self.mock_mode:
            print("HSPConnector: Mock disconnect successful.")
            self.is_connected = False
        else:
            await self.external_connector.disconnect()
            self.is_connected = self.external_connector.is_connected
        for callback in self._disconnect_callbacks:
            await callback()

    async def publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1):
        if not self.is_connected:
            print(f"HSPConnector: Not connected, cannot publish to {topic}.")
            return False
        # The message bridge handles the actual external publishing
        # For direct external publishing, we'd use self.external_connector.publish
        # But for now, all messages go through the internal bus for routing
        # This method is for direct publishing of a fully formed HSP envelope
        # The message_bridge.handle_internal_message expects a dict with 'topic' and 'payload'
        # So we need to adapt the envelope to that format for the internal bus.
        # The topic here is the MQTT topic, not the internal bus channel.
        # The internal bus channel for external messages is "hsp.internal.message"
        # The payload for the internal bus is the full envelope.
        try:
            await self.external_connector.publish(topic, json.dumps(envelope), qos=qos)
            return True
        except Exception as e:
            print(f"HSPConnector: Error publishing message to {topic}: {e}")
            return False

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
            "payload_schema_uri": "hsp:schema:payload/Fact/0.1",
            "payload": fact_payload
        }
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
            "payload_schema_uri": "hsp:schema:payload/TaskRequest/0.1",
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
            "payload_schema_uri": "hsp:schema:payload/TaskResult/0.1",
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
            "payload_schema_uri": "hsp:schema:payload/CapabilityAdvertisement/0.1",
            "payload": cap_payload
        }
        return await self.publish_message(topic, envelope, qos)

    def subscribe(self, topic: str, callback: Callable):
        # This subscribe is for internal bus subscriptions, not direct MQTT
        # MQTT subscriptions are handled by ExternalConnector
        self.internal_bus.subscribe(f"hsp.external.{topic}", callback)

    def unsubscribe(self, topic: str, callback: Callable):
        self.internal_bus.unsubscribe(f"hsp.external.{topic}", callback)

    # --- Registration methods for external modules to receive specific message types ---
    def register_on_fact_callback(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]):
        self._fact_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback: Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]):
        self._capability_advertisement_callbacks.append(callback)

    def register_on_task_request_callback(self, callback: Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]):
        self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]):
        self._task_result_callbacks.append(callback)

    def register_on_connect_callback(self, callback: Callable[[], None]):
        self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback: Callable[[], None]):
        self._disconnect_callbacks.append(callback)

    # --- Internal dispatch methods ---
    async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any]):
        # message here is the full envelope from the internal bus
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")
        if payload and sender_ai_id:
            for callback in self._fact_callbacks:
                await callback(payload, sender_ai_id, message)

    async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")
        if payload and sender_ai_id:
            for callback in self._capability_advertisement_callbacks:
                await callback(payload, sender_ai_id, message)

    async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")
        if payload and sender_ai_id:
            for callback in self._task_request_callbacks:
                await callback(payload, sender_ai_id, message)

    async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")
        if payload and sender_ai_id:
            for callback in self._task_result_callbacks:
                await callback(payload, sender_ai_id, message)

    # --- Properties ---
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool):
        self._is_connected = value

        self.internal_bus = InternalBus()
        self.data_aligner = DataAligner()
        self.message_bridge = MessageBridge(
            self.external_connector,
            self.internal_bus,
            self.data_aligner
        )

    async def connect(self):
        await self.external_connector.connect()

    async def disconnect(self):
        await self.external_connector.disconnect()

    def subscribe(self, topic: str, callback):
        self.internal_bus.subscribe(f"hsp.external.{topic}", callback)

    def unsubscribe(self, topic: str, callback):
        self.internal_bus.unsubscribe(f"hsp.external.{topic}", callback)

    def publish(self, topic: str, message: dict):
        self.internal_bus.publish("hsp.internal.message", {"topic": topic, "payload": message})

    def publish_fact(self, fact_payload: dict, topic: str):
        # This is a simplified version for now.
        # In a real implementation, you would want to build a proper HSP envelope.
        self.publish(topic, fact_payload)
