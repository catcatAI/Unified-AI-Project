import json # Added for JSON serialization
from typing import Callable, Dict, Any, Optional # Added Optional
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
from .fallback.fallback_protocols import get_fallback_manager, FallbackMessage, MessagePriority, initialize_fallback_protocols
from .utils.fallback_config_loader import get_config_loader

class HSPConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int, mock_mode: bool = False, mock_mqtt_client: Optional[MagicMock] = None, internal_bus: Optional[Any] = None, message_bridge: Optional[Any] = None, enable_fallback: bool = True, **kwargs):
        self.ai_id = ai_id
        self.mock_mode = mock_mode
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.default_qos = 1 # Default QoS for MQTT messages
        self.enable_fallback = enable_fallback
        self.fallback_manager = None
        self.fallback_initialized = False
        self.logger = logging.getLogger(__name__)
        self.hsp_available = False  # Track HSP availability

        if self.mock_mode:
            print("HSPConnector: Initializing in mock mode.")
            print(f"DEBUG: HSPConnector.__init__ - ai_id: {ai_id}, mock_mode: {mock_mode}")
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
        self._connect_callbacks = []
        self._disconnect_callbacks = []
        
        # Initialize fallback protocols if enabled
        # Moved to connect() method to ensure event loop is running

        # Register internal message bridge handler for external messages
        if self.mock_mode:
            self.external_connector.on_message_callback = AsyncMock(side_effect=self.message_bridge.handle_external_message)
        else:
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
            self.hsp_available = True
            if self.enable_fallback:
                await self._initialize_fallback_protocols()
            # In mock mode, explicitly subscribe to relevant topics on the mock MQTT client
            await self.external_connector.subscribe("hsp/knowledge/facts/#", self.external_connector.on_message_callback)
            await self.external_connector.subscribe("hsp/capabilities/advertisements/#", self.external_connector.on_message_callback)
            await self.external_connector.subscribe(f"hsp/requests/{self.ai_id}", self.external_connector.on_message_callback)
            await self.external_connector.subscribe(f"hsp/results/{self.ai_id}", self.external_connector.on_message_callback)
        else:
            try:
                await self.external_connector.connect()
                self.is_connected = self.external_connector.is_connected
                self.hsp_available = self.is_connected
                if not self.hsp_available:
                    self.logger.warning("HSP connection failed, fallback protocols will be used")
                if self.enable_fallback:
                    await self._initialize_fallback_protocols()
            except Exception as e:
                self.logger.error(f"HSP connection error: {e}, using fallback protocols")
                self.is_connected = False
                self.hsp_available = False
        
        for callback in self._connect_callbacks:
            await callback()

    async def disconnect(self):
        if self.mock_mode:
            print("HSPConnector: Mock disconnect successful.")
            self.is_connected = False
        else:
            await self.external_connector.disconnect()
            self.is_connected = self.external_connector.is_connected

        if self.fallback_manager and self.fallback_initialized:
            await self.fallback_manager.shutdown()
            self.fallback_initialized = False

        for callback in self._disconnect_callbacks:
            await callback()

    async def publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1):
        print(f"HSPConnector: publish_message called. self.external_connector.publish is {type(self.external_connector.publish)}")
        
        # Try HSP first if available
        if self.hsp_available and self.is_connected:
            try:
                await self.external_connector.publish(topic, json.dumps(envelope).encode('utf-8'), qos=qos)
                return True
            except Exception as e:
                self.logger.error(f"HSP publish failed: {e}, trying fallback")
                self.hsp_available = False
        
        # Use fallback protocols if HSP is not available
        if self.enable_fallback and self.fallback_manager:
            return await self._send_via_fallback(topic, envelope, qos)
        
        print(f"HSPConnector: No available communication method for {topic}.")
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

    async def subscribe(self, topic: str, callback: Callable):
        # This subscribe is for internal bus subscriptions, not direct MQTT
        # MQTT subscriptions are handled by ExternalConnector
        self.internal_bus.subscribe(f"hsp.external.{topic}", callback)

    def unsubscribe(self, topic: str, callback: Callable):
        self.internal_bus.unsubscribe(f"hsp.external.{topic}", callback)

    # --- Registration methods for external modules to receive specific message types ---
    def register_on_fact_callback(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None]):
        print(f"DEBUG: register_on_fact_callback - Registering callback: {callback}")
        self._fact_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback: Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None]):
        print(f"DEBUG: register_on_capability_advertisement_callback - Before append: {len(self._capability_advertisement_callbacks)}")
        self._capability_advertisement_callbacks.append(callback)
        print(f"DEBUG: register_on_capability_advertisement_callback - After append: {len(self._capability_advertisement_callbacks)}")

    def register_on_task_request_callback(self, callback: Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None]):
        self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None]):
        self._task_result_callbacks.append(callback)

    def register_on_connect_callback(self, callback: Callable[[], None]):
        self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback: Callable[[], None]):
        self._disconnect_callbacks.append(callback)

    async def advertise_capability(self, capability: HSPCapabilityAdvertisementPayload):
        """Publishes a capability advertisement."""
        await self.publish_capability_advertisement(capability)

    # --- Internal dispatch methods ---
    async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any]):
        # message here is the full envelope from the internal bus
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        print(f"DEBUG: _dispatch_fact_to_callbacks - self._fact_callbacks = {self._fact_callbacks}")
        print(f"DEBUG: _dispatch_fact_to_callbacks - Incoming message: {message}")
        print(f"DEBUG: _dispatch_fact_to_callbacks - qos_parameters: {message.get("qos_parameters")}")

        if payload and sender_ai_id:
            fact_payload = HSPFactPayload(**payload)
            print(f"DEBUG: _dispatch_fact_to_callbacks - Type of fact_payload before callback: {type(fact_payload)}")
            print(f"DEBUG: _dispatch_fact_to_callbacks - Content of fact_payload before callback: {fact_payload}")
            for callback in self._fact_callbacks:
                print(f"DEBUG: _dispatch_fact_to_callbacks - calling callback {callback}, type: {type(callback)}")
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
                    "correlation_id": message.get("correlation_id"),
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": "hsp:schema:payload/Acknowledgement/0.1",
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope)

    async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        print(f"DEBUG: _dispatch_capability_advertisement_to_callbacks - self._capability_advertisement_callbacks = {self._capability_advertisement_callbacks}")
        print(f"DEBUG: _dispatch_capability_advertisement_to_callbacks - Incoming message: {message}")
        print(f"DEBUG: _dispatch_capability_advertisement_to_callbacks - qos_parameters: {message.get("qos_parameters")}")

        if payload and sender_ai_id:
            cap_payload = HSPCapabilityAdvertisementPayload(**payload)
            print(f"DEBUG: _dispatch_capability_advertisement_to_callbacks - Number of callbacks: {len(self._capability_advertisement_callbacks)}")
            for callback in self._capability_advertisement_callbacks:
                print(f"DEBUG: _dispatch_capability_advertisement_to_callbacks - calling callback {callback}, type: {type(callback)}")
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
                    "correlation_id": message.get("correlation_id"),
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": "hsp:schema:payload/Acknowledgement/0.1",
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope)

    async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        print(f"DEBUG: _dispatch_task_request_to_callbacks - self._task_request_callbacks = {self._task_request_callbacks}")
        print(f"DEBUG: _dispatch_task_request_to_callbacks - Incoming message: {message}")
        print(f"DEBUG: _dispatch_task_request_to_callbacks - qos_parameters: {message.get("qos_parameters")}")

        if payload and sender_ai_id:
            task_request_payload = HSPTaskRequestPayload(**payload)
            for callback in self._task_request_callbacks:
                print(f"DEBUG: _dispatch_task_request_to_callbacks - calling callback {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_request_payload, sender_ai_id, message)
                else:
                    callback(task_request_payload, sender_ai_id, message)

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
                    "correlation_id": message.get("correlation_id"),
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": "hsp:schema:payload/Acknowledgement/0.1",
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope)

    async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        print(f"DEBUG: _dispatch_task_result_to_callbacks - self._task_result_callbacks = {self._task_result_callbacks}")
        print(f"DEBUG: _dispatch_task_result_to_callbacks - Incoming message: {message}")
        print(f"DEBUG: _dispatch_task_result_to_callbacks - qos_parameters: {message.get("qos_parameters")}")

        if payload and sender_ai_id:
            task_result_payload = HSPTaskResultPayload(**payload)
            for callback in self._task_result_callbacks:
                print(f"DEBUG: _dispatch_task_result_to_callbacks - calling callback {callback}")
                await callback(task_result_payload, sender_ai_id, message)

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
                    "correlation_id": message.get("correlation_id"),
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": "hsp:schema:payload/Acknowledgement/0.1",
                    "payload": ack_payload
                }
                # Publish ACK to the sender's ACK topic
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope)

    # --- Properties ---
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool):
        self._is_connected = value

    # --- Fallback Protocol Methods ---
    async def _initialize_fallback_protocols(self):
        """初始化備用協議"""
        if not self.enable_fallback:
            return
        
        try:
            # 加載配置
            config_loader = get_config_loader()
            if not config_loader.is_fallback_enabled():
                self.logger.info("Fallback protocols disabled in configuration")
                return
            
            fallback_config = config_loader.get_fallback_config()
            message_config = fallback_config.get("message", {})
            
            # 設置日誌級別
            logging_config = fallback_config.get("logging", {})
            if logging_config.get("level"):
                fallback_logger = logging.getLogger("src.hsp.fallback")
                fallback_logger.setLevel(getattr(logging, logging_config["level"]))
            
            self.fallback_manager = get_fallback_manager()
            
            # 使用配置初始化協議
            success = await self._initialize_protocols_with_config(fallback_config)
            
            if success:
                self.fallback_initialized = True
                # 註冊消息處理器
                for _, protocol in self.fallback_manager.protocols:
                    protocol.register_handler("hsp_message", self._handle_fallback_message)
                
                # 設置健康檢查間隔
                health_interval = message_config.get("health_check_interval", 30)
                self.fallback_manager.health_check_interval = health_interval
                
                self.logger.info("Fallback protocols initialized successfully with configuration")
            else:
                self.logger.error("Failed to initialize fallback protocols")
        except Exception as e:
            self.logger.error(f"Error initializing fallback protocols: {e}")

    async def _initialize_protocols_with_config(self, config: Dict[str, Any]) -> bool:
        """使用配置初始化協議"""
        try:
            from .fallback.fallback_protocols import InMemoryProtocol, FileBasedProtocol, HTTPProtocol
            
            protocols_config = config.get("protocols", {})
            
            # 初始化內存協議
            memory_config = protocols_config.get("memory", {})
            if memory_config.get("enabled", True):
                memory_protocol = InMemoryProtocol()
                # 可以根據配置設置隊列大小等參數
                priority = memory_config.get("priority", 1)
                self.fallback_manager.add_protocol(memory_protocol, priority=priority)
                self.logger.debug(f"Added memory protocol with priority {priority}")
            
            # 初始化文件協議
            file_config = protocols_config.get("file", {})
            if file_config.get("enabled", True):
                base_path = file_config.get("base_path", "data/fallback_comm")
                file_protocol = FileBasedProtocol(base_path=base_path)
                priority = file_config.get("priority", 2)
                self.fallback_manager.add_protocol(file_protocol, priority=priority)
                self.logger.debug(f"Added file protocol with priority {priority}")
            
            # 初始化HTTP協議
            http_config = protocols_config.get("http", {})
            if http_config.get("enabled", True):
                host = http_config.get("host", "127.0.0.1")
                port = http_config.get("port", 8765)
                http_protocol = HTTPProtocol(host=host, port=port)
                priority = http_config.get("priority", 3)
                self.fallback_manager.add_protocol(http_protocol, priority=priority)
                self.logger.debug(f"Added HTTP protocol with priority {priority}")
            
            # 初始化並啟動管理器
            if await self.fallback_manager.initialize():
                await self.fallback_manager.start()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing protocols with config: {e}")
            return False

    async def _send_via_fallback(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        """通過備用協議發送消息"""
        if not self.fallback_manager:
            return False
        
        try:
            # 確定優先級
            priority = MessagePriority.NORMAL
            if qos >= 2:
                priority = MessagePriority.HIGH
            elif envelope.get("qos_parameters", {}).get("priority") == "high":
                priority = MessagePriority.HIGH
            elif envelope.get("qos_parameters", {}).get("priority") == "low":
                priority = MessagePriority.LOW
            
            # 創建fallback消息
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
                fallback_msg.sender_id,
                fallback_msg.recipient_id,
                fallback_msg.message_type,
                fallback_msg.payload,
                priority=priority
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
        """處理從備用協議接收的消息"""
        try:
            payload = message.payload
            if payload.get("envelope"):
                envelope = payload["envelope"]
                # 將消息路由到內部總線，就像從HSP接收的一樣
                await self.message_bridge.handle_external_message(
                    payload.get("topic", ""), 
                    json.dumps(envelope).encode('utf-8')
                )
                self.logger.debug(f"Processed fallback message: {message.id}")
        except Exception as e:
            self.logger.error(f"Error handling fallback message: {e}")

    def get_communication_status(self) -> Dict[str, Any]:
        """獲取通訊狀態"""
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
        """健康檢查"""
        health = {
            "hsp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
        }
        
        # 檢查HSP健康狀態
        if self.hsp_available and self.is_connected:
            try:
                # 可以添加實際的HSP健康檢查邏輯
                health["hsp_healthy"] = True
            except:
                health["hsp_healthy"] = False
                self.hsp_available = False
        
        # 檢查fallback健康狀態
        if self.fallback_manager:
            try:
                fallback_status = self.fallback_manager.get_status()
                health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except:
                health["fallback_healthy"] = False
        
        health["overall_healthy"] = health["hsp_healthy"] or health["fallback_healthy"]
        return health

        
