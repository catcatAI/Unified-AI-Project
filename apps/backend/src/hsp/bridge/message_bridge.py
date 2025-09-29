import json
from typing import TYPE_CHECKING
from .data_aligner import DataAligner
from ..external.external_connector import ExternalConnector
from ..internal.internal_bus import InternalBus

if TYPE_CHECKING:

class MessageBridge:
    _message_type_to_internal_topic_map = {
        "HSP::Fact_v0.1": "fact",
        "HSP::Opinion_v0.1": "opinion",  # 添加观点消息的映射
        "HSP::CapabilityAdvertisement_v0.1": "capability_advertisement",
        "HSP::TaskRequest_v0.1": "task_request",
        "HSP::TaskResult_v0.1": "task_result",
        "HSP::Acknowledgement_v0.1": "acknowledgement",
    }

    def __init__(self, external_connector: ExternalConnector, internal_bus: InternalBus, data_aligner: DataAligner) -> None:
        self.external_connector: ExternalConnector = external_connector
        self.internal_bus: InternalBus = internal_bus
        self.data_aligner: DataAligner = data_aligner

        # 修复类型问题：使用lambda包装异步方法以确保类型兼容性
        self.external_connector.on_message_callback = self.handle_external_message
        self.internal_bus.subscribe("hsp.internal.message", self._sync_handle_internal_message)

    def _sync_handle_internal_message(self, message: 'Any') -> None:
        """同步包装器，用于处理内部消息"""
        # 在事件循环中运行异步方法
        import asyncio
        try:
            loop = asyncio.get_event_loop
        except RuntimeError:
            loop = asyncio.new_event_loop
            asyncio.set_event_loop(loop)
        
        if loop.is_running:
            # 如果事件循环正在运行，创建任务
            loop.create_task(self.handle_internal_message(message))
        else:
            # 否则运行直到完成
            loop.run_until_complete(self.handle_internal_message(message))

    async def handle_external_message(self, topic: str, message: str):
        print(f"DEBUG: MessageBridge.handle_external_message - Incoming topic: {topic}, message: {message}")
        # Parse the incoming JSON string message into a dictionary
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError:
            # Handle invalid JSON, maybe log an error or send a NACK
            print(f"Error: Received invalid JSON message: {message}")
            return

        # Align and validate the message
        aligned_message, error = self.data_aligner.align_message(message_dict)
        print(f"DEBUG: MessageBridge.handle_external_message - Aligned message: {aligned_message}, error: {error}")
        if error:
            # Handle error, maybe publish to an error topic
            print(f"Error: MessageBridge.handle_external_message - Data alignment failed: {error}")
            return

        # Publish the aligned message to the internal bus
        message_type = aligned_message.get("message_type")
        print(f"DEBUG: MessageBridge.handle_external_message - Message type: {message_type}")
        if message_type:
            internal_topic_suffix = self._message_type_to_internal_topic_map.get(message_type)
            print(f"DEBUG: MessageBridge.handle_external_message - Internal topic suffix: {internal_topic_suffix}")
            if internal_topic_suffix:
                internal_channel = f"hsp.external.{internal_topic_suffix}"
                print(f"DEBUG: MessageBridge.handle_external_message - Publishing to internal bus channel: {internal_channel} with aligned_message: {aligned_message}")
                # Ensure the message includes sender_ai_id from the envelope
                if "sender_ai_id" not in aligned_message and "sender_ai_id" in message_dict:
                    aligned_message["sender_ai_id"] = message_dict["sender_ai_id"]
                # Await the async publish to ensure downstream async handlers complete (important for tests like ACK sending)
                if hasattr(self.internal_bus, 'publish_async'):
                    _ = await self.internal_bus.publish_async(internal_channel, aligned_message)
                else:
                    self.internal_bus.publish(internal_channel, aligned_message)
            else:
                print(f"Warning: MessageBridge.handle_external_message - Unknown message_type '{message_type}'. Not publishing to internal bus.")
        else:
            print("DEBUG: MessageBridge.handle_external_message - No message type found")

    async def handle_internal_message(self, message: 'Any'):
        # Normalize payload to bytes for MQTT publish compatibility
        topic = message.get("topic")
        payload = message.get("payload")
        qos = message.get("qos", 1)

        if isinstance(payload, (dict, list)):
            payload_str = json.dumps(payload)
        elif isinstance(payload, str):
            payload_str = payload
        elif isinstance(payload, (bytes, bytearray)):
            payload_str = payload.decode('utf-8')
        else:
            # Fallback: try JSON serialization
            try:
                payload_str = json.dumps(payload)
            except Exception:
                payload_str = str(payload)

        # Ensure we await the async publish to avoid "coroutine not awaited" and race conditions in tests
        await self.external_connector.publish(topic, payload_str, qos=qos)