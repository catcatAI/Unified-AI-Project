# scripts/mock_hsp_peer.py
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from src.core.hsp.connector import HSPConnector
from src.hsp.types import (
    HSPMessageEnvelope, HSPFactPayload, HSPCapabilityAdvertisementPayload,
    HSPTaskRequestPayload, HSPTaskResultPayload, HSPEnvironmentalStatePayload
)

logger = logging.getLogger(__name__)

class MockHSPPeer:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883) -> None:
        self.ai_id = ai_id
        self.connector = HSPConnector(
            ai_id=self.ai_id,
            broker_address=broker_address,
            broker_port=broker_port,
            client_id_suffix="mock_peer"  # Unique suffix for MQTT client ID
        )
        self.connector.register_on_generic_message_callback(self.handle_generic_hsp_message)
        self.connector.register_on_fact_callback(self.handle_fact_message)
        self.connector.register_on_task_request_callback(self.handle_task_request)  # Register new handler

        self.mock_capabilities: Dict[str, HSPCapabilityAdvertisementPayload] = {}
        self._define_mock_capabilities()
        self.alt_ai_id_1 = f"did:hsp:mock_peer_alt1_{uuid.uuid4().hex[:4]}"
        self.alt_ai_id_2 = f"did:hsp:mock_peer_alt2_{uuid.uuid4().hex[:4]}"

    def _define_mock_capabilities(self):
        cap_echo = HSPCapabilityAdvertisementPayload(
            capability_id=f"{self.ai_id}_echo_v1.0",
            ai_id=self.ai_id,
            name="Mock Echo Service",
            description="Echoes back the parameters it receives.",
            version="1.0",
            input_schema_example={"data_to_echo": "any"},
            output_schema_example={"echoed_data": "any"},
            availability_status="online",
            tags=["mock", "echo", "testing"]
        )
        self.mock_capabilities[cap_echo['capability_id']] = cap_echo

        cap_math = HSPCapabilityAdvertisementPayload(
            capability_id=f"{self.ai_id}_simple_math_v1.0",
            ai_id=self.ai_id,
            name="Simple Math Service (Mock)",
            description="Performs basic addition on two numbers.",
            version="1.0",
            input_schema_example={"operand1": 0, "operand2": 0, "operation": "add"},
            output_schema_example={"result": 0},
            availability_status="online",
            tags=["mock", "math", "calculation"]
        )
        self.mock_capabilities[cap_math['capability_id']] = cap_math

        cap_describe = HSPCapabilityAdvertisementPayload(  # type ignore
            capability_id=f"{self.ai_id}_describe_entity_v1.0",
            ai_id=self.ai_id,
            name="Mock Entity Description Service",
            description="Provides a mock textual description for a given entity name.",
            version="1.0",
            input_schema_example={"entity_name": "string"},
            output_schema_example={"description": "string", "entity_type_guess": "string"},
            availability_status="online",
            tags=["mock", "description", "entity"]
        )
        self.mock_capabilities[cap_describe['capability_id']] = cap_describe

        cap_fact_query = HSPCapabilityAdvertisementPayload(  # type ignore
            capability_id=f"{self.ai_id}_fact_query_service_v1.0",
            ai_id=self.ai_id,
            name="Mock Fact Query Service",
            description="Searches a small internal knowledge base for facts matching a query string.",
            version="1.0",
            input_schema_example={"query_text": "topic to search", "max_results": 3},
            output_schema_example={"facts_found": [{"id": "fact_123", "statement_nl": "...", "...": "..."}]},
            availability_status="online",
            tags=["mock", "knowledge_query", "facts"]
        )
        self.mock_capabilities[cap_fact_query['capability_id']] = cap_fact_query

        self.internal_mock_kb = [
            {"id": "kb_fact_001", "keywords": ["weather", "london", "sunny"], "statement_nl": "The weather in London is expected to be sunny today.", "confidence": 0.9, "type": "forecast"},
            {"id": "kb_fact_002", "keywords": ["hsp", "protocol", "robust"], "statement_nl": "HSP aims to be a robust protocol for AI interaction.", "confidence": 0.95, "type": "definition"},
            {"id": "kb_fact_003", "keywords": ["python", "programming", "versatile"], "statement_nl": "Python is a versatile programming language.", "confidence": 0.98, "type": "general_knowledge"},
            {"id": "kb_fact_004", "keywords": ["london", "population"], "statement_nl": "London has a population of approximately 9 million.", "confidence": 0.85, "type": "demographics"},
        ]
        self.published_conflicting_fact_ids: Dict[str, HSPFactPayload] = {}  # To store facts we might send updates for

    def handle_generic_hsp_message(self, envelope: HSPMessageEnvelope, topic: str) -> None:
        print(f"\n[MockPeer-{self.ai_id}] Received generic HSP message on MQTT topic '{topic}':")
        print(f"  Msg ID  : {envelope.get('message_id')}")
        print(f"  Sender  : {envelope.get('sender_ai_id')}")
        print(f"  Type    : {envelope.get('message_type')}")
        # Avoid printing large payloads in generic handler unless debugging
        # print(f"  Payload {json.dumps(envelope.get('payload'), indent=2)}")

    def handle_fact_message(self, fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None:
        print(f"\n[MockPeer-{self.ai_id}] Received FACT from '{sender_ai_id}' (MQTT topic: '{full_envelope.get('recipient_ai_id')}'):")
        statement_nl = fact_payload.get('statement_nl', 'N/A')
        statement_structured = fact_payload.get('statement_structured', {})
        statement_to_print = statement_nl if statement_nl != 'N/A' else statement_structured

        print(f"  Fact ID    : {fact_payload.get('id')}")
        print(f"  Statement  : {statement_to_print}")
        print(f"  Confidence : {fact_payload.get('confidence_score')}")

    def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
        print(f"\n[MockPeer-{self.ai_id}] Received TASK REQUEST from '{sender_ai_id}' for capability '{task_payload.get('capability_id_filter')}'. CorrID: {full_envelope.get('correlation_id')}")

        requested_cap_id = task_payload.get('capability_id_filter')
        params = task_payload.get('parameters', {})
        correlation_id = full_envelope.get('correlation_id')  # This is crucial
        reply_to_address = task_payload.get('callback_address')  # Address to send the result

        if not requested_cap_id or not correlation_id or not reply_to_address:
            print(f"  MockPeer: Invalid TaskRequest - missing capability_id, correlation_id, or callback_address.")
            # Optionally send a failure TaskResult
            return

        response_payload: Optional[HSPTaskResultPayload] = None

        if requested_cap_id == f"{self.ai_id}_echo_v1.0":
            response_payload = HSPTaskResultPayload(  # type ignore
                result_id=f"taskres_echo_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="success",
                payload={"echoed_data": params, "message": f"Echo from {self.ai_id}"},
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )
        elif requested_cap_id == f"{self.ai_id}_simple_math_v1.0":
            op1 = params.get('operand1')
            op2 = params.get('operand2')
            operation = params.get('operation', 'add')
            if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
                result_val = None
                if operation == 'add': 
                    result_val = op1 + op2
                # Add more operations if needed for testing (subtract, etc.)
                else: 
                    result_val = "unknown_operation"

                response_payload = HSPTaskResultPayload(  # type ignore
                    result_id=f"taskres_math_{uuid.uuid4().hex[:6]}",
                    request_id=task_payload['request_id'],
                    executing_ai_id=self.ai_id,
                    status="success",
                    payload={"result": result_val, "operation_performed": operation},
                    timestamp_completed=datetime.now(timezone.utc).isoformat()
                )
            else:
                response_payload = HSPTaskResultPayload(  # type ignore
                    result_id=f"taskres_math_err_{uuid.uuid4().hex[:6]}",
                    request_id=task_payload['request_id'],
                    executing_ai_id=self.ai_id,
                    status="failure",
                    error_details={  # type ignore
                        "error_code": "INVALID_PARAMETERS",
                        "error_message": "Operands for math must be numbers."
                    },
                    timestamp_completed=datetime.now(timezone.utc).isoformat()
                )
        elif requested_cap_id == f"{self.ai_id}_describe_entity_v1.0":
            entity_name = params.get('entity_name', 'Unknown Entity')
            response_payload = HSPTaskResultPayload(  # type ignore
                result_id=f"taskres_desc_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="success",
                payload={
                    "description": f"The entity '{entity_name}' is a conceptual element often discussed in test scenarios. It represents things that need describing by mock AIs like {self.ai_id}.",
                    "entity_type_guess": "conceptual_test_entity"
                },
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )
        elif requested_cap_id == f"{self.ai_id}_fact_query_service_v1.0":
            query_text = params.get('query_text', '').lower()
            max_results = params.get('max_results', 3)
            found_facts_for_hsp: List[HSPFactPayload] = []

            if query_text:  # Only search if query_text is provided
                for mock_fact in self.internal_mock_kb:
                    if any(keyword in query_text for keyword in mock_fact.get("keywords", [])) or \
                       query_text in mock_fact.get("statement_nl", "").lower():
                        hsp_fact = HSPFactPayload(  # type ignore
                            id=f"hsp_mqf_{mock_fact['id']}_{uuid.uuid4().hex[:4]}",  # Make ID unique for HSP context
                            statement_type="natural_language",
                            statement_nl=mock_fact["statement_nl"],
                            confidence_score=mock_fact["confidence"],
                            metadata={
                                "source": "mock_internal_kb",
                                "mock_peer_id": self.ai_id,
                                "original_kb_id": mock_fact["id"]
                            }
                        )
                        found_facts_for_hsp.append(hsp_fact)

            # Limit to max_results
            found_facts_for_hsp = found_facts_for_hsp[:max_results]

            response_payload = HSPTaskResultPayload(  # type ignore
                result_id=f"taskres_fq_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="success",
                payload={
                    "facts_found": [dict(fact) for fact in found_facts_for_hsp],  # Convert to dict for serialization
                    "query_processed": query_text,
                    "total_results_available": len(found_facts_for_hsp)
                },
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )
        else:
            # Unknown capability - send failure response
            response_payload = HSPTaskResultPayload(  # type ignore
                result_id=f"taskres_unknown_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="failure",
                error_details={
                    "error_code": "UNKNOWN_CAPABILITY",
                    "error_message": f"Capability '{requested_cap_id}' is not implemented by this mock peer."
                },
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )

        # Send the response back via HSP
        if response_payload and reply_to_address:
            asyncio.create_task(self._send_task_result(response_payload, reply_to_address, correlation_id))

    async def _send_task_result(self, result_payload: HSPTaskResultPayload, target_address: str, correlation_id: str):
        """Send a task result back to the requester."""
        try:
            # Use the connector to send the result
            success = await self.connector.send_task_result(
                payload=result_payload,
                target_ai_id_or_topic=target_address,
                correlation_id=correlation_id
            )
            if success:
                print(f"[MockPeer-{self.ai_id}] Successfully sent task result for CorrID: {correlation_id}")
            else:
                print(f"[MockPeer-{self.ai_id}] Failed to send task result for CorrID: {correlation_id}")
        except Exception as e:
            print(f"[MockPeer-{self.ai_id}] Error sending task result: {e}")

    async def start(self):
        """Start the mock peer."""
        try:
            # Connect to HSP
            await self.connector.connect()
            print(f"[MockPeer-{self.ai_id}] Connected to HSP broker.")

            # Advertise capabilities
            for cap in self.mock_capabilities.values():
                await self.connector.publish_capability_advertisement(cap)
            print(f"[MockPeer-{self.ai_id}] Published {len(self.mock_capabilities)} mock capabilities.")

            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"[MockPeer-{self.ai_id}] Shutting down...")
        except Exception as e:
            print(f"[MockPeer-{self.ai_id}] Error: {e}")
        finally:
            await self.connector.disconnect()

    async def publish_test_fact(self, statement: str, confidence: float = 0.8):
        """Publish a test fact."""
        fact_payload = HSPFactPayload(
            id=f"test_fact_{uuid.uuid4().hex[:8]}",
            statement_type="natural_language",
            statement_nl=statement,
            confidence_score=confidence,
            metadata={
                "source": "mock_peer_test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        await self.connector.publish_fact(fact_payload)
        print(f"[MockPeer-{self.ai_id}] Published test fact: {statement}")

async def main():
    """Main function to run the mock HSP peer."""
    import argparse
    parser = argparse.ArgumentParser(description="Mock HSP Peer")
    parser.add_argument("--ai-id", default="did:hsp:mock_peer_001", help="AI ID for this peer")
    parser.add_argument("--broker", default="localhost", help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    args = parser.parse_args()

    peer = MockHSPPeer(ai_id=args.ai_id, broker_address=args.broker, broker_port=args.port)
    await peer.start()

if __name__ == "__main__":
    asyncio.run(main())
