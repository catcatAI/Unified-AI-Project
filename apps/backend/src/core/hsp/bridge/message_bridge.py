import logging
import json
from typing import Dict, Any, Optional
from .data_aligner import DataAligner
from core.hsp.external.external_connector import ExternalConnector
from core.hsp.internal.internal_bus import InternalBus

logger = logging.getLogger(__name__)

class MessageBridge:
    """
    Bridges messages between the ExternalConnector and the InternalBus.
    (Restored to fix file corruption)
    """
    _message_type_to_internal_topic_map = {
        "HSP.Fact_v0.1": "fact",
        "HSP.CapabilityAdvertisement_v0.1": "capability_advertisement",
        "HSP.TaskRequest_v0.1": "task_request",
        "HSP.TaskResult_v0.1": "task_result",
        "HSP.Acknowledgement_v0.1": "acknowledgement",
    }

    def __init__(self, external_connector: ExternalConnector, internal_bus: InternalBus, data_aligner: DataAligner):
        self.external_connector = external_connector
        self.internal_bus = internal_bus
        self.data_aligner = data_aligner
        # In a real system we would register callbacks here.
        # self.external_connector.on_message_callback = self.handle_external_message
        # self.internal_bus.subscribe("hsp.internal.message", self.handle_internal_message)
        logger.info("MessageBridge initialized.")

    async def handle_external_message(self, topic: str, message: str):
        logger.debug(f"MessageBridge.handle_external_message - Incoming topic: {topic}")
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError:
            logger.error(f"Error: Received invalid JSON message: {message}")
            return

        aligned_message = self.data_aligner.align_incoming(message_dict)
        
        message_type = aligned_message.get("message_type")
        if message_type:
            internal_topic_suffix = self._message_type_to_internal_topic_map.get(message_type)
            if internal_topic_suffix:
                internal_channel = f"hsp.external.{internal_topic_suffix}"
                logger.debug(f"Publishing to internal bus: {internal_channel}")
                
                # Check for async publish capability
                if hasattr(self.internal_bus, 'publish_async'):
                    await self.internal_bus.publish_async(internal_channel, aligned_message)
                else:
                    self.internal_bus.publish(internal_channel, aligned_message)

    async def handle_internal_message(self, message: Dict[str, Any]):
        topic = message.get("topic")
        payload = message.get("payload")
        if not topic:
             return
             
        # Normalize payload
        if isinstance(payload, (dict, list)):
            payload_bytes = json.dumps(payload).encode('utf-8')
        elif isinstance(payload, str):
             payload_bytes = payload.encode('utf-8')
        else:
             payload_bytes = str(payload).encode('utf-8')

        await self.external_connector.send(message) # Stubbed send usually takes dict
