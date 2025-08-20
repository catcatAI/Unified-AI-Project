# scripts/mock_hsp_peer.py
import asyncio
import json
import time
import uuid
from datetime import datetime, timezone

# We need to ensure that 'src' is in PYTHONPATH if running this script directly
# This adds the project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload #, HSPTaskRequestPayload, HSPTaskResultPayload # Add more as needed

# Define other payload types that might be used by the mock, even if just for type hinting
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPEnvironmentalStatePayload


class MockHSPPeer:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883):
        self.ai_id = ai_id
        self.connector = HSPConnector(
            ai_id=self.ai_id,
            broker_address=broker_address,
            broker_port=broker_port,
            client_id_suffix="mock_peer" # Unique suffix for MQTT client ID
        )
        self.connector.register_on_generic_message_callback(self.handle_generic_hsp_message)
        self.connector.register_on_fact_callback(self.handle_fact_message)
        self.connector.register_on_task_request_callback(self.handle_task_request) # Register new handler

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

        cap_describe = HSPCapabilityAdvertisementPayload( #type: ignore
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

        cap_fact_query = HSPCapabilityAdvertisementPayload( #type: ignore
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
        self.published_conflicting_fact_ids: Dict[str, HSPFactPayload] = {} # To store facts we might send updates for


    def handle_generic_hsp_message(self, envelope: HSPMessageEnvelope, topic: str) -> None:
        print(f"\n[MockPeer-{self.ai_id}] Received generic HSP message on MQTT topic '{topic}':")
        print(f"  Msg ID  : {envelope.get('message_id')}")
        print(f"  Sender  : {envelope.get('sender_ai_id')}")
        print(f"  Type    : {envelope.get('message_type')}")
        # Avoid printing large payloads in generic handler unless debugging
        # print(f"  Payload: {json.dumps(envelope.get('payload'), indent=2)}")

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
        correlation_id = full_envelope.get('correlation_id') # This is crucial
        reply_to_address = task_payload.get('callback_address') # Address to send the result

        if not requested_cap_id or not correlation_id or not reply_to_address:
            print(f"  MockPeer: Invalid TaskRequest - missing capability_id, correlation_id, or callback_address.")
            # Optionally send a failure TaskResult
            return

        response_payload: Optional[HSPTaskResultPayload] = None

        if requested_cap_id == f"{self.ai_id}_echo_v1.0":
            response_payload = HSPTaskResultPayload( # type: ignore
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
                if operation == 'add': result_val = op1 + op2
                # Add more operations if needed for testing (subtract, etc.)
                else: result_val = "unknown_operation"

                response_payload = HSPTaskResultPayload( # type: ignore
                    result_id=f"taskres_math_{uuid.uuid4().hex[:6]}",
                    request_id=task_payload['request_id'],
                    executing_ai_id=self.ai_id,
                    status="success",
                    payload={"result": result_val, "operation_performed": operation},
                    timestamp_completed=datetime.now(timezone.utc).isoformat()
                )
            else:
                response_payload = HSPTaskResultPayload( # type: ignore
                    result_id=f"taskres_math_err_{uuid.uuid4().hex[:6]}",
                    request_id=task_payload['request_id'],
                    executing_ai_id=self.ai_id,
                    status="failure",
                    error_details={ # type: ignore
                        "error_code": "INVALID_PARAMETERS",
                        "error_message": "Operands for math must be numbers."
                    },
                    timestamp_completed=datetime.now(timezone.utc).isoformat()
                )
        elif requested_cap_id == f"{self.ai_id}_describe_entity_v1.0":
            entity_name = params.get('entity_name', 'Unknown Entity')
            response_payload = HSPTaskResultPayload( # type: ignore
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

            if query_text: # Only search if query_text is provided
                for mock_fact in self.internal_mock_kb:
                    if any(keyword in query_text for keyword in mock_fact.get("keywords", [])) or \
                       query_text in mock_fact.get("statement_nl", "").lower():

                        hsp_fact = HSPFactPayload( #type: ignore
                            id=f"hsp_mqf_{mock_fact['id']}_{uuid.uuid4().hex[:4]}", # Make ID unique for HSP context
                            statement_type="natural_language",
                            statement_nl=mock_fact["statement_nl"],
                            source_ai_id=self.ai_id, # This mock peer is the source for these facts
                            timestamp_created=datetime.now(timezone.utc).isoformat(),
                            confidence_score=mock_fact.get("confidence", 0.75),
                            tags=["mock_kb_derived", mock_fact.get("type", "general")]
                        )
                        found_facts_for_hsp.append(hsp_fact)
                        if len(found_facts_for_hsp) >= max_results:
                            break

            response_payload = HSPTaskResultPayload( #type: ignore
                result_id=f"taskres_fq_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="success",
                payload={"facts_found": found_facts_for_hsp, "query_echo": query_text},
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )
        else:
            print(f"  MockPeer: Received request for unknown/unsupported capability_id '{requested_cap_id}'.")
            response_payload = HSPTaskResultPayload( # type: ignore
                result_id=f"taskres_unknown_cap_{uuid.uuid4().hex[:6]}",
                request_id=task_payload['request_id'],
                executing_ai_id=self.ai_id,
                status="rejected",
                error_details={ # type: ignore
                    "error_code": "CAPABILITY_NOT_FOUND",
                    "error_message": f"Capability '{requested_cap_id}' not supported by {self.ai_id}."
                },
                timestamp_completed=datetime.now(timezone.utc).isoformat()
            )

        if response_payload:
            print(f"  MockPeer: Sending TaskResult (status: {response_payload.get('status')}) to '{reply_to_address}' for CorrID '{correlation_id}'.")
            await self.connector.send_task_result(response_payload, reply_to_address, correlation_id)


    async def run_loop(self):
        """Main loop for the mock peer to publish sample data periodically."""
        fact_counter = 0
        env_counter = 0
        while self.connector.is_connected:
            await asyncio.sleep(15) # Action every 15 seconds

            # Alternate between publishing a fact and an environmental state
            if fact_counter <= env_counter:
                fact_counter += 1
                print(f"\n[MockPeer-{self.ai_id}] Periodic action: Publishing sample fact {fact_counter}...")
                await self.publish_sample_fact(fact_counter)
            elif env_counter < fact_counter : # Publish env state if fewer env states have been sent
                env_counter += 1
                print(f"\n[MockPeer-{self.ai_id}] Periodic action: Publishing sample environment state {env_counter}...")
                await self.publish_sample_environmental_state(env_counter)
            # else: pass


    async def publish_sample_fact(self, counter: int):
        if not self.connector.is_connected:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        topic = "hsp/knowledge/facts/general"
        fact_payload: Optional[HSPFactPayload] = None

        # --- Type 1 Conflict Test Facts (ID-based) ---
        conflict_test_fact_original_id = "type1_conflict_target_id_001"
        if counter == 2: # Publish the original fact for Type 1 conflict test
            fact_payload = HSPFactPayload(
                id=conflict_test_fact_original_id,
                statement_type="natural_language",
                statement_nl=f"Initial: {conflict_test_fact_original_id} from {self.ai_id}.",
                source_ai_id=self.ai_id, timestamp_created=timestamp, confidence_score=0.7,
                tags=["type1_conflict", "original"] #type: ignore
            )
            self.published_conflicting_fact_ids[conflict_test_fact_original_id] = fact_payload
            print(f"  Publishing Type 1 ORIGINAL: ID '{fact_payload['id']}', Conf: {fact_payload['confidence_score']}")
        elif counter == 4 and conflict_test_fact_original_id in self.published_conflicting_fact_ids: # Update with higher confidence
            fact_payload = HSPFactPayload(
                id=conflict_test_fact_original_id, statement_type="natural_language",
                statement_nl=f"Update (HighConf): {conflict_test_fact_original_id} from {self.ai_id}.",
                source_ai_id=self.ai_id, timestamp_created=datetime.now(timezone.utc).isoformat(), confidence_score=0.9,
                tags=["type1_conflict", "update_high_conf"] #type: ignore
            )
            print(f"  Publishing Type 1 UPDATE (HighConf): ID '{fact_payload['id']}', Conf: {fact_payload['confidence_score']}")
        elif counter == 6 and conflict_test_fact_original_id in self.published_conflicting_fact_ids: # Update with different value, similar confidence
            fact_payload = HSPFactPayload(
                id=conflict_test_fact_original_id, statement_type="natural_language",
                statement_nl=f"Update (DiffValue): {conflict_test_fact_original_id} from {self.ai_id} - new info.",
                source_ai_id=self.ai_id, timestamp_created=datetime.now(timezone.utc).isoformat(), confidence_score=0.72, # Similar to original 0.7
                tags=["type1_conflict", "update_diff_value_similar_conf"] #type: ignore
            )
            print(f"  Publishing Type 1 UPDATE (DiffValue): ID '{fact_payload['id']}', Conf: {fact_payload['confidence_score']}")

        # --- Type 2 Semantic Conflict Test Facts (S/P based) & Numerical Merge ---
        # Scenario 1: Semantic conflict, new one more confident
        # S: http://example.org/entity/ProductX, P: http://example.org/prop/price
        sem_conflict_s = "http://example.org/entity/ProductX"
        sem_conflict_p = "http://example.org/prop/price" # Not in default ontology_mappings.yaml, so will be used as is.

        if counter == 8: # First semantic fact (lower confidence, from alt_ai_id_1)
            fact_payload = HSPFactPayload(
                id=f"sem_fact_1_{uuid.uuid4().hex[:4]}", statement_type="semantic_triple",
                statement_structured={"subject_uri": sem_conflict_s, "predicate_uri": sem_conflict_p, "object_literal": "100.00"}, #type: ignore
                statement_nl=f"{sem_conflict_s} has price 100.00 (from {self.alt_ai_id_1})",
                source_ai_id=self.alt_ai_id_1, timestamp_created=timestamp, confidence_score=0.6,
                tags=["type2_conflict", "semantic_initial_low_conf"] #type: ignore
            )
            print(f"  Publishing Type 2 SEMANTIC (Initial LowConf): ID '{fact_payload['id']}' for S/P '{sem_conflict_s}/{sem_conflict_p}', O='100.00', Conf: 0.6, Source: {self.alt_ai_id_1}")
        elif counter == 10: # Second semantic fact, same S/P, different O, higher confidence (from self.ai_id)
            fact_payload = HSPFactPayload(
                id=f"sem_fact_2_{uuid.uuid4().hex[:4]}", statement_type="semantic_triple",
                statement_structured={"subject_uri": sem_conflict_s, "predicate_uri": sem_conflict_p, "object_literal": "120.00"}, #type: ignore
                statement_nl=f"{sem_conflict_s} has price 120.00 (from {self.ai_id}, more confident)",
                source_ai_id=self.ai_id, timestamp_created=datetime.now(timezone.utc).isoformat(), confidence_score=0.9,
                tags=["type2_conflict", "semantic_update_high_conf"] #type: ignore
            )
            print(f"  Publishing Type 2 SEMANTIC (Update HighConf): ID '{fact_payload['id']}' for S/P '{sem_conflict_s}/{sem_conflict_p}', O='120.00', Conf: 0.9, Source: {self.ai_id}")

        # Scenario 2: Numerical Merge. Assume previous fact (O=120.00, C=0.9 from self.ai_id) is in HAM.
        # New fact from alt_ai_id_2 with O=130.00, C=0.85 (similar confidence to 0.9)
        elif counter == 12:
            fact_payload = HSPFactPayload(
                id=f"sem_fact_3_num_merge_{uuid.uuid4().hex[:4]}", statement_type="semantic_triple",
                statement_structured={"subject_uri": sem_conflict_s, "predicate_uri": sem_conflict_p, "object_literal": "130.00"}, #type: ignore
                statement_nl=f"{sem_conflict_s} has price 130.00 (from {self.alt_ai_id_2}, for num_merge test)",
                source_ai_id=self.alt_ai_id_2, timestamp_created=datetime.now(timezone.utc).isoformat(), confidence_score=0.85,
                tags=["type2_conflict", "numerical_merge_candidate"] #type: ignore
            )
            print(f"  Publishing Type 2 NUMERICAL MERGE CANDIDATE: ID '{fact_payload['id']}' for S/P '{sem_conflict_s}/{sem_conflict_p}', O='130.00', Conf: 0.85, Source: {self.alt_ai_id_2}")

        # Scenario 3: Trust/Recency Tie-Breaking
        # S: http://example.org/entity/ServiceY, P: http://example.org/prop/status
        tie_break_s = "http://example.org/entity/ServiceY"
        tie_break_p = "http://example.org/prop/status"

        if counter == 14: # Fact 1 for tie-break (from alt_ai_id_1, older, slightly lower confidence)
            fact_payload = HSPFactPayload(
                id=f"tie_break_fact_1_{uuid.uuid4().hex[:4]}", statement_type="semantic_triple",
                statement_structured={"subject_uri": tie_break_s, "predicate_uri": tie_break_p, "object_literal": "active"}, #type: ignore
                statement_nl=f"{tie_break_s} status is active (from {self.alt_ai_id_1}, older).",
                source_ai_id=self.alt_ai_id_1, timestamp_created=timestamp, confidence_score=0.75,
                tags=["type2_conflict", "tie_break_older"] #type: ignore
            )
            print(f"  Publishing Type 2 TIE-BREAK (Older): ID '{fact_payload['id']}' S/P '{tie_break_s}/{tie_break_p}', O='active', Conf: 0.75, Source: {self.alt_ai_id_1}")
        elif counter == 16: # Fact 2 for tie-break (from alt_ai_id_2, newer, slightly higher confidence but still "similar")
                           # Assume alt_ai_id_2 has higher trust than alt_ai_id_1 in the target LM's TrustManager for this test.
            await asyncio.sleep(0.1) # Ensure slightly newer timestamp for recency part of test
            fact_payload = HSPFactPayload(
                id=f"tie_break_fact_2_{uuid.uuid4().hex[:4]}", statement_type="semantic_triple",
                statement_structured={"subject_uri": tie_break_s, "predicate_uri": tie_break_p, "object_literal": "inactive"}, #type: ignore
                statement_nl=f"{tie_break_s} status is inactive (from {self.alt_ai_id_2}, newer).",
                source_ai_id=self.alt_ai_id_2, timestamp_created=datetime.now(timezone.utc).isoformat(), confidence_score=0.78,
                tags=["type2_conflict", "tie_break_newer_higher_trust_source"] #type: ignore
            )
            print(f"  Publishing Type 2 TIE-BREAK (Newer/HigherTrustSource): ID '{fact_payload['id']}' S/P '{tie_break_s}/{tie_break_p}', O='inactive', Conf: 0.78, Source: {self.alt_ai_id_2}")

        # Fallback to regular sample facts if no specific test case for the counter
        if not fact_payload and counter not in [2,4,6,8,10,12,14,16]:
            fact_id_reg = f"mock_fact_reg_{self.ai_id.replace(':', '_')}_{counter}_{uuid.uuid4().hex[:4]}"
            if counter % 3 == 0 : # Mix in some structured facts not for conflict
                subject_ext_uri_reg = f"http://example.com/ontology#Item/mock_item_{counter}"
                predicate_ext_uri_reg = "http://purl.org/dc/elements/1.1/creator" # Mapped to cai_prop:creator in ontology_mappings
                object_lit_reg = f"Mock Item Creator {counter}"
                fact_payload = HSPFactPayload(
                    id=fact_id_reg, statement_type="semantic_triple",
                    statement_structured={ "subject_uri": subject_ext_uri_reg, "predicate_uri": predicate_ext_uri_reg, "object_literal": object_lit_reg, "object_datatype": "xsd:string" }, #type: ignore
                    statement_nl=f"{subject_ext_uri_reg} was created by '{object_lit_reg}'.",
                    source_ai_id=self.ai_id, timestamp_created=timestamp, confidence_score=0.98,
                    tags=["sample_fact", "structured_mappable"] #type: ignore
                )
                print(f"  Publishing REGULAR STRUCTURED (mappable) fact: ID '{fact_payload['id']}'")
            else: # Regular NL fact
                fact_payload = HSPFactPayload(
                    id=fact_id_reg, statement_type="natural_language",
                    statement_nl=f"This is regular NL fact number {counter} from {self.ai_id} about a general topic.",
                    source_ai_id=self.ai_id, timestamp_created=timestamp, confidence_score=0.92,
                    tags=["sample_fact", "natural_language"] #type: ignore
                )
                print(f"  Publishing REGULAR NL fact: ID '{fact_payload['id']}'")

        if fact_payload:
            self.connector.publish_fact(fact_payload, topic=topic)
        else:
            # This condition means the counter matched a conflict test arm that might have already published
            # or it's an even counter where we previously didn't publish structured if it was a conflict test counter.
            # The logic has been changed to use 'if/elif' for specific counters, so this 'else' is for counters not handled.
            print(f"  No specific fact to publish for counter {counter} in this cycle, or already handled by conflict sequence.")


    def publish_sample_environmental_state(self, counter: int):
        """Example of the mock peer publishing something."""
        if not self.connector.is_connected:
            return

        payload = HSPEnvironmentalStatePayload( # type: ignore # TypedDict should be fine
            update_id=f"env_update_{uuid.uuid4().hex[:6]}",
            source_ai_id=self.ai_id, # This AI is the source
            phenomenon_type="hsp:event:MockPeerHeartbeat",
            parameters={"count": counter, "status": "alive", "peer_id": self.ai_id},
            timestamp_observed=datetime.now(timezone.utc).isoformat(),
            scope_type="global"
        )
        topic = "hsp/environment/peer_updates" # CLI peer doesn't subscribe to this by default
        print(f"[MockPeer-{self.ai_id}] Publishing sample environmental state to '{topic}' (ID: {payload['update_id']})")

        envelope: HSPMessageEnvelope = { # type: ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::EnvironmentalState_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "low"},
            "routing_info": None,
            "payload_schema_uri": "file:///HSP_EnvironmentalState_v0.1.schema.json",
            "payload": payload
        }
        await self.connector.publish_message(topic, envelope, qos=1)


    async def start(self):
        print(f"[MockPeer-{self.ai_id}] Attempting to connect...")
        await self.connector.connect()
        # Allow a brief moment for any async post-connect initialization
        await asyncio.sleep(0.2)

        if self.connector.is_connected:
            print(f"[MockPeer-{self.ai_id}] Successfully connected to MQTT broker.")

            # 1. Publish capabilities
            print(f"[MockPeer-{self.ai_id}] Publishing capabilities...")
            for cap_id, cap_payload in self.mock_capabilities.items():
                await self.connector.publish_capability_advertisement(cap_payload)
                print(f"  MockPeer: Advertised capability '{cap_id}'.")

            # 2. Subscribe to relevant topics
            topics_to_subscribe = [
                "hsp/knowledge/facts/#", # All facts
                f"hsp/requests/{self.ai_id}/#", # Task requests specifically for this mock AI
            ]
            print(f"[MockPeer-{self.ai_id}] Subscribing to topics: {topics_to_subscribe}")
            for topic in topics_to_subscribe:
                await self.connector.subscribe(topic)

            print(f"[MockPeer-{self.ai_id}] Subscriptions complete. Listening...")

            # Start a task for periodic publishing (facts, heartbeats, etc.)
            asyncio.create_task(self.run_loop())

            # Keep the main start task alive
            while True:
                await asyncio.sleep(1)
        else:
            print(f"[MockPeer-{self.ai_id}] Failed to establish connection after connect() call.")

    async def stop(self):
        print(f"[MockPeer-{self.ai_id}] Stopping...")
        await self.connector.disconnect()
        print(f"[MockPeer-{self.ai_id}] Disconnected.")


async def main_async_runner():
    peer_id = f"did:hsp:mock_peer_{uuid.uuid4().hex[:8]}"
    print(f"--- Starting Mock HSP Peer --- \nID: {peer_id}")
    # Ensure MQTT broker is running at localhost:1883
    peer = MockHSPPeer(ai_id=peer_id, broker_address="localhost", broker_port=1883)

    try:
        await peer.start()
    except KeyboardInterrupt:
        print(f"\n[MockPeer-{peer_id}] KeyboardInterrupt received.")
    except Exception as e:
        print(f"[MockPeer-{peer_id}] An error occurred: {e}")
    finally:
        print(f"[MockPeer-{peer_id}] Shutting down...")
        await peer.stop()
        # Allow time for MQTT disconnect to complete
        await asyncio.sleep(1)
        print(f"[MockPeer-{peer_id}] Exited.")

if __name__ == "__main__":
    # To run this:
    # 1. Ensure MQTT broker is running (e.g., `docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto`)
    # 2. Run this script: python scripts/mock_hsp_peer.py
    # 3. Separately, run your main AI application which also connects to HSP and publishes.

    # Add a simple check for paho-mqtt
    try:
        import paho.mqtt.client
    except ImportError:
        print("Error: paho-mqtt library not found. Please install it: pip install paho-mqtt")
        sys.exit(1)

    asyncio.run(main_async_runner())
