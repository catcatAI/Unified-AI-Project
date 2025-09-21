import paho.mqtt.client as mqtt
from typing import Optional, Callable, Dict, Any
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone

from .types import MCPEnvelope, MCPCommandRequest, MCPCommandResponse
from ..shared.error import ProjectError, project_error_handler

class MCPConnector:
    def __init__(self, ai_id: str, mqtt_broker_address: str, mqtt_broker_port: int, 
                 enable_fallback: bool = True, fallback_config: Optional[Dict[str, Any]] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.ai_id = ai_id
        self.client = mqtt.Client(client_id=f"mcp-client-{ai_id}-{uuid.uuid4()}")
        self.broker_address = mqtt_broker_address
        self.broker_port = mqtt_broker_port
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.command_handlers: dict[str, Callable] = {}
        
        # Fallback支持
        self.enable_fallback = enable_fallback
        self.fallback_config = fallback_config or {}
        self.fallback_manager = None
        self.fallback_initialized = False
        self.mcp_available = False
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        self.loop = loop if loop else asyncio.get_event_loop() # Store the event loop

    async def connect(self):
        print(f"MCPConnector for {self.ai_id} connecting to {self.broker_address}:{self.broker_port}")
        try:
            # Connect and start the loop in a separate thread to avoid blocking the event loop
            # For testing purposes, we might mock this or ensure it runs in a dedicated thread/process
            # In a real application, you'd typically use an async MQTT client library
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
        print("MCPConnector disconnected.")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MCPConnector connected successfully.")
            self.is_connected = True
            self.mcp_available = True
            # Subscribe to topics relevant to this AI
            client.subscribe(f"mcp/broadcast")
            client.subscribe(f"mcp/unicast/{self.ai_id}")
        else:
            print(f"MCPConnector failed to connect, return code {rc}")
            self.is_connected = False
            self.mcp_available = False

    def _on_message(self, client, userdata, msg):
        print(f"MCP message received on topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload)
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4 and topic_parts[0] == 'mcp' and topic_parts[1] == 'cmd':
                # Topic format: mcp/cmd/{ai_id}/{command_name}
                command_name = topic_parts[3]
                if command_name in self.command_handlers:
                    handler = self.command_handlers[command_name]
                    # Schedule the coroutine in the main event loop
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.run_coroutine_threadsafe(handler(data.get('args')), self.loop)
                    else:
                        handler(data.get('args'))
        except json.JSONDecodeError:
            project_error_handler(ProjectError("Failed to decode MCP message payload as JSON.", code=400))
        except Exception as e:
            project_error_handler(ProjectError(f"Error processing MCP message: {e}", code=500))


    async def send_command(self, target_id: str, command_name: str, parameters: dict) -> str:
        request_id = str(uuid.uuid4())
        
        # 嘗試使用MQTT發送
        if self.mcp_available and self.is_connected:
            try:
                payload: MCPCommandRequest = {
                    "command_name": command_name,
                    "parameters": parameters
                }
                envelope: MCPEnvelope = {
                    "mcp_envelope_version": "0.1",
                    "message_id": request_id,
                    "sender_id": self.ai_id,
                    "recipient_id": target_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
                    "message_type": "MCP::CommandRequest_v0.1",
                    "protocol_version": "0.1",
                    "payload": payload,
                    "correlation_id": None
                }
                topic = f"mcp/cmd/{target_id}/{command_name}"
                self.client.publish(topic, json.dumps(envelope))
                print(f"Sent MCP command '{command_name}' to {target_id} via MQTT with request_id {request_id}")
                return request_id
            except Exception as e:
                self.logger.error(f"MCP MQTT發送失敗: {e}")
                self.mcp_available = False
        
        # 使用fallback協議發送
        if self.enable_fallback and self.fallback_initialized and self.fallback_manager:
            try:
                await self._send_via_fallback(target_id, command_name, parameters, request_id)
                print(f"Sent MCP command '{command_name}' to {target_id} via fallback with request_id {request_id}")
                return request_id
            except Exception as e:
                self.logger.error(f"MCP fallback發送失敗: {e}")
        
        self.logger.error(f"無法發送MCP命令 '{command_name}' 到 {target_id}")
        return request_id

    async def _initialize_fallback_protocols(self):
        """初始化MCP備用協議"""
        if not self.enable_fallback:
            return
        
        try:
            from .fallback.mcp_fallback_protocols import get_mcp_fallback_manager, initialize_mcp_fallback_protocols
            
            self.fallback_manager = get_mcp_fallback_manager()

            # 檢查是否在多進程環境中運行
            # 這裡我們使用一個簡單的標誌，實際應用中可能需要更複雜的檢測
            is_multiprocess = self.fallback_config.get("is_multiprocess", False)

            success = await initialize_mcp_fallback_protocols(is_multiprocess=is_multiprocess)
            
            if success:
                self.fallback_initialized = True
                # 註冊命令處理器
                for command_name, handler in self.command_handlers.items():
                    self.fallback_manager.register_command_handler(command_name, handler)
                
                self.logger.info("MCP fallback protocols initialized successfully")
            else:
                self.logger.error("Failed to initialize MCP fallback protocols")
                self.fallback_initialized = False
        except Exception as e:
            project_error_handler(ProjectError(f"Error initializing MCP fallback protocols: {e}", code=500))
            self.fallback_initialized = False

    async def _send_via_fallback(self, target_id: str, command_name: str, parameters: dict, request_id: str):
        """通過fallback協議發送命令"""
        if not self.fallback_manager:
            return False
        
        try:
            from .fallback.mcp_fallback_protocols import MCPMessagePriority
            
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
            self.logger.error(f"Error sending MCP command via fallback: {e}")
            return False

    def register_command_handler(self, command_name: str, handler: Callable):
        """註冊命令處理器（同時註冊到fallback）"""
        self.command_handlers[command_name] = handler
        
        # 註冊到MQTT
        if self.is_connected:
            topic = f"mcp/cmd/{self.ai_id}/{command_name}"
            self.client.subscribe(topic)
            print(f"Registered handler for command '{command_name}' on topic '{topic}'")
        
        # 註冊到fallback
        if self.fallback_manager:
            self.fallback_manager.register_command_handler(command_name, handler)

    def get_communication_status(self) -> Dict[str, Any]:
        """獲取通訊狀態"""
        status = {
            "mcp_available": self.mcp_available,
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
            "mcp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
        }
        
        # 檢查MCP MQTT健康狀態
        if self.mcp_available and self.is_connected:
            try:
                health["mcp_healthy"] = True
            except:
                health["mcp_healthy"] = False
                self.mcp_available = False
        
        # 檢查fallback健康狀態
        if self.fallback_manager:
            try:
                fallback_status = self.fallback_manager.get_status()
                health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except:
                health["fallback_healthy"] = False
        
        health["overall_healthy"] = health["mcp_healthy"] or health["fallback_healthy"]
        return health