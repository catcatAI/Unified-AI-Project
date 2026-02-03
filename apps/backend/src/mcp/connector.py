"""
MCPConnector - 多代理通信協議連接器
支持容錯機制、重試邏輯和備用端點 (SKELETON)
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any, Awaitable, List
from unittest.mock import Mock

# Mock dependencies for syntax validation
class ProjectError(Exception): pass
def project_error_handler(error): pass

class MCPEnvelope:
    def __init__(self, **kwargs): pass

class MCPMessagePriority:
    NORMAL = "NORMAL"

class FallbackManager:
    def register_command_handler(self, command_name, handler): pass
    async def send_command(self, sender_id, recipient_id, command_name, parameters, priority): return True
    def get_status(self): return {"active_protocol": "mock"}

def get_mcp_fallback_manager(): return FallbackManager()
async def initialize_mcp_fallback_protocols(is_multiprocess: bool): return True

# Mock paho.mqtt.client
class MockMQTTClient:
    def __init__(self, client_id): pass
    def on_connect(self, client, userdata, flags, rc): pass
    def on_message(self, client, userdata, msg): pass
    def connect(self, host, port, keepalive): pass
    def loop_start(self): pass
    def loop_stop(self): pass
    def disconnect(self): pass
    def subscribe(self, topic): pass
    def publish(self, topic, payload): pass
mqtt = Mock()
mqtt.Client = MockMQTTClient

logger = logging.getLogger(__name__)

class MCPConnector:
    """MCPConnector - 多代理通信協議連接器 (SKELETON)"""

    def __init__(self, ai_id: str, mqtt_broker_address: str = "localhost", mqtt_broker_port: int = 1883, enable_fallback: bool = True, fallback_config: Optional[Dict[str, Any]] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.ai_id = ai_id
        self.client = mqtt.Client(client_id=f"mcp-client-{ai_id}-{uuid.uuid4().hex[:8]}")
        self.broker_address = mqtt_broker_address
        self.broker_port = mqtt_broker_port
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.command_handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}

        self.enable_fallback = enable_fallback
        self.fallback_config = fallback_config or {}
        self.fallback_manager: Optional[FallbackManager] = None
        self.fallback_initialized = False
        self.mcp_available = False
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        self.loop = loop if loop else asyncio.get_event_loop()

    async def connect(self):
        self.logger.info(f"MCPConnector for {self.ai_id} connecting to {self.broker_address}:{self.broker_port}")
        try:
            self.client.connect(self.broker_address, self.broker_port, 60)
            self.client.loop_start()
            self.is_connected = True
            self.mcp_available = True
            if self.enable_fallback:
                await self._initialize_fallback_protocols()
        except Exception as e:
            project_error_handler(ProjectError(f"MCP MQTT connection failed: {e}", code=503))
            self.is_connected = False
            self.mcp_available = False
            if self.enable_fallback:
                self.logger.info("MCP將使用fallback協議")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("MCPConnector disconnected.")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MCPConnector connected successfully.")
            self.is_connected = True
            self.mcp_available = True
            client.subscribe(f"mcp/broadcast")
            client.subscribe(f"mcp/unicast/{self.ai_id}")
        else:
            self.logger.warning(f"MCPConnector failed to connect, return code {rc}")
            self.is_connected = False
            self.mcp_available = False

    def _on_message(self, client, userdata, msg):
        self.logger.info(f"MCP message received on topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload)
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4 and topic_parts[0] == 'mcp' and topic_parts[1] == 'cmd':
                command_name = topic_parts[3]
                if command_name in self.command_handlers:
                    handler = self.command_handlers[command_name]
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.run_coroutine_threadsafe(handler(data.get('args')), self.loop)
                    else:
                        handler(data.get('args'))
        except json.JSONDecodeError:
            project_error_handler(ProjectError("Failed to decode MCP message payload as JSON.", code=400))
        except Exception as e:
            project_error_handler(ProjectError(f"Error processing MCP message: {e}", code=500))

    async def send_command(self, target_id: str, command_name: str, parameters: Dict[str, Any]) -> str:
        request_id = str(uuid.uuid4())
        if self.mcp_available and self.is_connected:
            try:
                payload = {"command_name": command_name, "parameters": parameters}
                envelope = MCPEnvelope(
                    mcp_envelope_version="0.1",
                    message_id=request_id,
                    sender_id=self.ai_id,
                    recipient_id=target_id,
                    timestamp_sent=datetime.now(timezone.utc).isoformat(),
                    message_type="MCP.CommandRequest_v0.1",
                    protocol_version="0.1",
                    payload=payload,
                    correlation_id=None
                )
                topic = f"mcp/cmd/{target_id}/{command_name}"
                self.client.publish(topic, json.dumps(envelope))
                self.logger.info(f"Sent MCP command '{command_name}' to {target_id} via MQTT with request_id {request_id}")
                return request_id
            except Exception as e:
                self.logger.error(f"MCP MQTT發送失敗: {e}", exc_info=True)
                self.mcp_available = False

        if self.enable_fallback and self.fallback_initialized and self.fallback_manager:
            try:
                await self._send_via_fallback(target_id, command_name, parameters, request_id)
                self.logger.info(f"Sent MCP command '{command_name}' to {target_id} via fallback with request_id {request_id}")
                return request_id
            except Exception as e:
                self.logger.error(f"MCP fallback發送失敗: {e}", exc_info=True)

        self.logger.error(f"無法發送MCP命令 '{command_name}' 到 {target_id}")
        return request_id

    async def _initialize_fallback_protocols(self):
        if not self.enable_fallback:
            return
        try:
            self.fallback_manager = get_mcp_fallback_manager()
            is_multiprocess = self.fallback_config.get("is_multiprocess", False)
            success = await initialize_mcp_fallback_protocols(is_multiprocess=is_multiprocess)
            if success:
                self.fallback_initialized = True
                for command_name, handler in self.command_handlers.items():
                    self.fallback_manager.register_command_handler(command_name, handler)
                self.logger.info("MCP fallback protocols initialized successfully")
            else:
                self.logger.error("Failed to initialize MCP fallback protocols")
                self.fallback_initialized = False
        except Exception as e:
            project_error_handler(ProjectError(f"Error initializing MCP fallback protocols: {e}", code=500))
            self.fallback_initialized = False

    async def _send_via_fallback(self, target_id: str, command_name: str, parameters: Dict[str, Any], request_id: str):
        if not self.fallback_manager:
            return False
        try:
            success = await self.fallback_manager.send_command(
                sender_id=self.ai_id,
                recipient_id=target_id,
                command_name=command_name,
                parameters=parameters,
                priority=MCPMessagePriority.NORMAL
            )
            if success:
                self.logger.debug(f"MCP command sent via fallback: {request_id}")
            else:
                self.logger.error(f"Failed to send MCP command via fallback: {request_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error sending MCP command via fallback: {e}", exc_info=True)
            return False

    def register_command_handler(self, command_name: str, handler: Callable[..., Awaitable[Any]]):
        self.command_handlers[command_name] = handler
        if self.is_connected:
            topic = f"mcp/cmd/{self.ai_id}/{command_name}"
            self.client.subscribe(topic)
            self.logger.info(f"Registered handler for command '{command_name}' on topic '{topic}'")
        if self.fallback_manager:
            self.fallback_manager.register_command_handler(command_name, handler)

    def get_communication_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            "mcp_available": self.mcp_available,
            "is_connected": self.is_connected,
            "fallback_enabled": self.enable_fallback,
            "fallback_initialized": self.fallback_initialized
        }
        if self.fallback_manager:
            fallback_status = self.fallback_manager.get_status()
            status["fallback_status"] = fallback_status
        return status

    async def health_check(self) -> Dict[str, Any]:
        health: Dict[str, Any] = {
            "mcp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
        }
        if self.mcp_available and self.is_connected:
            try:
                # Simulate a ping or simple check
                # self.client.publish("mcp/ping", "ping")
                health["mcp_healthy"] = True
            except Exception:
                health["mcp_healthy"] = False
                self.mcp_available = False

        if self.fallback_manager:
            try:
                fallback_status = self.fallback_manager.get_status()
                health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except Exception:
                health["fallback_healthy"] = False

        health["overall_healthy"] = health["mcp_healthy"] or health["fallback_healthy"]
        return health
