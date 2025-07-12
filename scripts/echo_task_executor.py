import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any # Added Dict, Any
import logging # Added logging

from src.hsp.connector import HSPConnector
from src.hsp.types import (
    HSPMessageEnvelope, HSPTaskRequestPayload, HSPTaskResultPayload,
    HSPCapabilityAdvertisementPayload, HSPEchoTaskRequestPayload, HSPEchoTaskResultPayload
)
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule # Added
from src.core_ai.trust_manager.trust_manager_module import TrustManager # Added

logger = logging.getLogger(__name__)

ECHO_CAPABILITY_ID = "hsp:capability:echo_service_v0.1"
ECHO_TASK_REQUEST_TYPE = "HSP::EchoTaskRequest_v0.1"
ECHO_TASK_RESULT_TYPE = "HSP::EchoTaskResult_v0.1"

class EchoTaskExecutorAI:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int):
        self.ai_id = ai_id
        self.connector = HSPConnector(ai_id=ai_id, broker_address=broker_address, broker_port=broker_port)
        self.connector.register_on_task_request_callback(self._handle_echo_task_request)
        self.connector.register_on_capability_re_advertisement_request_callback(self._handle_re_advertisement_request)

        # Initialize ServiceDiscoveryModule for this AI to store its own capabilities
        self.trust_manager = TrustManager() # Simple TrustManager for this AI
        self.service_discovery_module = ServiceDiscoveryModule(trust_manager=self.trust_manager)
        self.service_discovery_module.set_hsp_connector(self.connector) # Pass connector to SDM

    async def _handle_re_advertisement_request(self, payload: Dict[str, Any], sender_ai_id: str, full_envelope: HSPMessageEnvelope):
        logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Received re-advertisement request from {sender_ai_id}. Re-advertising capability.")
        await self.advertise_capability()

    async def _handle_echo_task_request(self, payload: HSPTaskRequestPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
        logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Received Echo Task Request from {sender_ai_id} with request_id {payload['request_id']}")

        if payload.get("capability_id_filter") != ECHO_CAPABILITY_ID:
            logger.warning(f"EchoTaskExecutorAI: Received task request for unknown capability: {payload.get('capability_id_filter')}")
            # Send a rejection or error result
            error_payload: HSPTaskResultPayload = {
                "result_id": str(uuid.uuid4()),
                "request_id": payload['request_id'],
                "executing_ai_id": self.ai_id,
                "status": "rejected",
                "error_details": {"error_code": "UNKNOWN_CAPABILITY", "error_message": "This AI does not provide the requested capability."}
            }
            self.connector.send_task_result(error_payload, payload['callback_address'], payload['request_id'])
            return

        # Extract the message from the echo task request payload
        echo_request_payload: HSPEchoTaskRequestPayload = payload["parameters"] # type: ignore
        message_to_echo = echo_request_payload.get("message")

        if message_to_echo is None:
            logger.error("EchoTaskExecutorAI: Echo task request missing 'message' parameter.")
            error_payload: HSPTaskResultPayload = {
                "result_id": str(uuid.uuid4()),
                "request_id": payload['request_id'],
                "executing_ai_id": self.ai_id,
                "status": "failure",
                "error_details": {"error_code": "INVALID_PARAMETERS", "error_message": "Echo task requires a 'message' parameter."}
            }
            self.connector.send_task_result(error_payload, payload['callback_address'], payload['request_id'])
            return

        logger.info(f'EchoTaskExecutorAI: Echoing message: "{message_to_echo}"')

        # Construct the echo task result payload
        echo_result_payload: HSPEchoTaskResultPayload = {
            "echoed_message": message_to_echo,
            "original_request_id": payload['request_id']
        }

        # Construct the task result envelope
        task_result: HSPTaskResultPayload = {
            "result_id": str(uuid.uuid4()),
            "request_id": payload['request_id'],
            "executing_ai_id": self.ai_id,
            "status": "success",
            "payload": echo_result_payload, # The actual result data
            "timestamp_completed": datetime.now(timezone.utc).isoformat()
        }

        # Send the task result back to the requester
        self.connector.send_task_result(task_result, payload['callback_address'], payload['request_id'])
        logger.info(f"EchoTaskExecutorAI: Sent Echo Task Result for request {payload['request_id']}")

    async def advertise_capability(self):
        logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Advertising capability...")
        capability_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": ECHO_CAPABILITY_ID,
            "ai_id": self.ai_id,
            "name": "Echo Service",
            "description": "Echoes back any message sent to it as a task request.",
            "version": "0.1",
            "input_schema_example": {"message": "string"},
            "output_schema_example": {"echoed_message": "string", "original_request_id": "string"},
            "availability_status": "online",
            "tags": ["utility", "test", "echo"]
        }
        # Publish to a well-known topic for capability advertisements
        self.connector.publish_capability_advertisement(capability_payload, topic="hsp/capabilities/advertisements")
        # Also store it in this AI's own ServiceDiscoveryModule
        self.service_discovery_module.process_capability_advertisement(capability_payload, self.ai_id, full_envelope={ # type: ignore
            "hsp_envelope_version": "0.1", "message_id": str(uuid.uuid4()), "correlation_id": None,
            "sender_ai_id": self.ai_id, "recipient_ai_id": "hsp/capabilities/advertisements",
            "timestamp_sent": datetime.now(timezone.utc).isoformat(), "message_type": "HSP::CapabilityAdvertisement_v0.1",
            "protocol_version": "0.1", "communication_pattern": "publish", "security_parameters": {}, "qos_parameters": {},
            "routing_info": {}, "payload_schema_uri": None, "payload": capability_payload
        })
        logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Capability advertised and stored locally.")

    async def start(self):
        logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Starting...")
        if self.connector.connect():
            logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Connected to MQTT broker.")

            # Subscribe to task request topic for this AI
            self.connector.subscribe(f"hsp/requests/{self.ai_id}")
            logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Subscribed to hsp/requests/{self.ai_id}")

            # Subscribe to the re-advertisement request topic
            self.connector.subscribe("hsp/capabilities/re_advertise_request")
            logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Subscribed to hsp/capabilities/re_advertise_request")

            await self.advertise_capability()

            # Keep the AI running to listen for requests
            logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Running and listening for tasks. Press Ctrl+C to exit.")
            try:
                while True:
                    await asyncio.sleep(1) # Keep the event loop running
            except asyncio.CancelledError:
                logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Shutting down due to cancellation.")
            except KeyboardInterrupt:
                logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Shutting down due to KeyboardInterrupt.")
            finally:
                self.connector.disconnect()
                logger.info(f"EchoTaskExecutorAI ({self.ai_id}): Disconnected from MQTT broker.")
        else:
            logger.error(f"EchoTaskExecutorAI ({self.ai_id}): Failed to connect to MQTT broker. Exiting.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Configure logging
    # To run this executor, ensure Mosquitto is running.
    # python scripts/echo_task_executor.py
    my_echo_ai_id = "did:hsp:echo_ai_001"
    broker_addr = "localhost"
    broker_port = 1883

    executor_ai = EchoTaskExecutorAI(my_echo_ai_id, broker_addr, broker_port)
    asyncio.run(executor_ai.start())
