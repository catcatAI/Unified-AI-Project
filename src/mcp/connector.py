import paho.mqtt.client as mqtt
from typing import Optional, Callable
import json
import uuid
from datetime import datetime, timezone

from src.mcp.types import MCPEnvelope, MCPCommandRequest, MCPCommandResponse

class MCPConnector:
    def __init__(self, ai_id: str, mqtt_broker_address: str, mqtt_broker_port: int):
        self.ai_id = ai_id
        self.client = mqtt.Client(client_id=f"mcp-client-{ai_id}-{uuid.uuid4()}")
        self.broker_address = mqtt_broker_address
        self.broker_port = mqtt_broker_port
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.command_handlers: dict[str, Callable] = {}

    def connect(self):
        print(f"MCPConnector for {self.ai_id} connecting to {self.broker_address}:{self.broker_port}")
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("MCPConnector disconnected.")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MCPConnector connected successfully.")
            # Subscribe to topics relevant to this AI
            client.subscribe(f"mcp/broadcast")
            client.subscribe(f"mcp/unicast/{self.ai_id}")
        else:
            print(f"MCPConnector failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        print(f"MCP message received on topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload)
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4 and topic_parts[0] == 'mcp' and topic_parts[1] == 'cmd':
                # Topic format: mcp/cmd/{ai_id}/{command_name}
                command_name = topic_parts[3]
                if command_name in self.command_handlers:
                    self.command_handlers[command_name](data.get('args'))
        except json.JSONDecodeError:
            print("Failed to decode MCP message payload as JSON.")
        except Exception as e:
            print(f"Error processing MCP message: {e}")

    def register_command_handler(self, command_name: str, handler: Callable):
        self.command_handlers[command_name] = handler
        topic = f"mcp/cmd/{self.ai_id}/{command_name}"
        self.client.subscribe(topic)
        print(f"Registered handler for command '{command_name}' on topic '{topic}'")

    def send_command(self, target_id: str, command_name: str, parameters: dict) -> str:
        request_id = str(uuid.uuid4())
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
        print(f"Sent command '{command_name}' to {target_id} with request_id {request_id}")
        return request_id