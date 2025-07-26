from __future__ import annotations
# src/core_ai/learning/learning_manager.py
import uuid
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import json

from src.core_ai.memory.ham_memory_manager import HAMMemoryManager # Corrected
from src.core_ai.learning.fact_extractor_module import FactExtractorModule # Corrected
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule # Corrected
from src.core_ai.trust_manager.trust_manager_module import TrustManager # Corrected
from src.shared.types.common_types import LearnedFactRecord # Corrected

from src.hsp.types import HSPFactPayload, HSPMessageEnvelope # Corrected
from src.core_ai.personality.personality_manager import PersonalityManager

if TYPE_CHECKING:
    from src.hsp.connector import HSPConnector # Corrected


class LearningManager:
    def __init__(self,
                 ai_id: str,
                 ham_memory_manager: HAMMemoryManager,
                 fact_extractor: FactExtractorModule,
                 personality_manager: PersonalityManager,
                 content_analyzer: Optional[ContentAnalyzerModule] = None,
                 hsp_connector: Optional[HSPConnector] = None,
                 trust_manager: Optional[TrustManager] = None,
                 operational_config: Optional[Dict[str, Any]] = None):
        self.ai_id = ai_id
        self.ham_memory = ham_memory_manager
        self.fact_extractor = fact_extractor
        self.personality_manager = personality_manager
        self.content_analyzer = content_analyzer
        self.hsp_connector = hsp_connector
        self.trust_manager = trust_manager
        self.operational_config = operational_config or {}

        learning_thresholds_config = self.operational_config.get("learning_thresholds", {})
        self.min_fact_confidence_to_store = learning_thresholds_config.get("min_fact_confidence_to_store", 0.7)
        self.min_fact_confidence_to_share_via_hsp = learning_thresholds_config.get("min_fact_confidence_to_share_via_hsp", 0.8)
        self.default_hsp_fact_topic = self.operational_config.get("default_hsp_fact_topic", "hsp/knowledge/facts/general")
        self.min_hsp_fact_confidence_to_store = learning_thresholds_config.get("min_hsp_fact_confidence_to_store", self.min_fact_confidence_to_store)
        self.hsp_fact_conflict_confidence_delta = learning_thresholds_config.get("hsp_fact_conflict_confidence_delta", 0.05)


        print(f"LearningManager initialized for AI ID '{self.ai_id}'. Min fact store conf: {self.min_fact_confidence_to_store}, share conf: {self.min_fact_confidence_to_share_via_hsp}, HSP store conf: {self.min_hsp_fact_confidence_to_store}")

    async def process_and_store_learnables(
        self, text: str, user_id: Optional[str], session_id: Optional[str], source_interaction_ref: Optional[str], source_text: Optional[str] = None
    ) -> List[str]:
        if not source_text: # If source_text isn't explicitly passed, use text
            source_text = text

        if not text: return []
        extracted_fact_data_list = self.fact_extractor.extract_facts(text, user_id)
        stored_fact_ids: List[str] = []

        for fact_data in extracted_fact_data_list:
            confidence = fact_data.get("confidence", 0.0)
            if confidence < self.min_fact_confidence_to_store:
                print(f"LearningManager: Fact confidence {confidence} below threshold {self.min_fact_confidence_to_store}. Not storing.")
                continue

            record_id = f"lfact_{uuid.uuid4().hex}"
            timestamp = datetime.now().isoformat()
            fact_type = fact_data.get("fact_type", "unknown_statement")
            content = fact_data.get("content", {})

            metadata_for_ham = {
                "record_id": record_id, "timestamp": timestamp, "user_id": user_id,
                "session_id": session_id, "source_interaction_ref": source_interaction_ref,
                "fact_type": fact_type, "confidence": confidence, "source_text": source_text
            }
            ham_data_type = f"learned_fact_{fact_type.lower().replace(' ', '_')}"

            print(f"LearningManager: Storing user-derived fact - Type: {ham_data_type}, Content: {content}, Meta: {metadata_for_ham}")
            stored_id = self.ham_memory.store_experience(raw_data=content, data_type=ham_data_type, metadata=metadata_for_ham)

            if stored_id:
                stored_fact_ids.append(stored_id)
                print(f"LearningManager: Stored fact '{record_id}' (HAM ID '{stored_id}')")

                if self.hsp_connector and confidence >= self.min_fact_confidence_to_share_via_hsp:
                    hsp_fact_id = f"hspfact_{self.ai_id.replace(':', '_')}_{uuid.uuid4().hex[:6]}"
                    nl_statement_for_hsp = source_text if source_text else json.dumps(content)
                    hsp_payload = HSPFactPayload(
                        id=hsp_fact_id, statement_type="natural_language",
                        statement_nl=nl_statement_for_hsp, statement_structured=content,
                        source_ai_id=self.ai_id,
                        original_source_info={"type": "user_utterance", "identifier": user_id or "unknown_user", #type: ignore
                                              "context_refs": {"session_id": session_id, "interaction_ref": source_interaction_ref}},
                        timestamp_created=timestamp, confidence_score=confidence,
                        weight=1.0, tags=[fact_type] if fact_type else ["user_derived"] #type: ignore
                    )
                    topic = self.default_hsp_fact_topic
                    if "user_preference" in fact_type: topic = "hsp/knowledge/facts/user_preferences"
                    elif "user_statement" in fact_type: topic = "hsp/knowledge/facts/user_statements"
                    print(f"LearningManager: Publishing fact {hsp_fact_id} to HSP topic '{topic}'")
                    self.hsp_connector.publish_fact(hsp_payload, topic=topic)
            else:
                print(f"LearningManager: Failed to store fact '{record_id}' in HAM.")
        return stored_fact_ids

    def process_and_store_hsp_fact(
        self, hsp_fact_payload: HSPFactPayload, hsp_sender_ai_id: str, hsp_envelope: HSPMessageEnvelope
    ) -> Optional[str]:
        """
        Processes an incoming fact from the HSP network using a quality-based assessment
        to prevent "idiot resonance".
        """
        original_hsp_fact_id = hsp_fact_payload.get('id')
        print(f"LearningManager: Starting quality assessment for HSP fact '{original_hsp_fact_id}' from '{hsp_sender_ai_id}'.")

        # 1. Check for Duplicates (Anti-Resonance)
        conflict_query_filters = {
            "hsp_fact_id": original_hsp_fact_id,
            "hsp_originator_ai_id": hsp_fact_payload.get('source_ai_id')
        }
        existing_facts = self.ham_memory.query_core_memory(
            metadata_filters=conflict_query_filters, data_type_filter="hsp_learned_fact_", limit=1
        )
        if existing_facts:
            existing_ham_id = existing_facts[0].get('id')
            print(f"  Fact is a duplicate of existing HAM record '{existing_ham_id}'. Incrementing corroboration count.")
            self.ham_memory.increment_metadata_field(existing_ham_id, "corroboration_count")
            return None

        # 2. Assess Source Credibility
        capability_name = hsp_fact_payload.get('tags', [None])[0] if hsp_fact_payload.get('tags') else None
        sender_trust_score = self.trust_manager.get_trust_score(hsp_sender_ai_id, capability_name) if self.trust_manager else TrustManager.DEFAULT_TRUST_SCORE
        original_confidence = hsp_fact_payload.get('confidence_score', 0.0)
        effective_confidence = original_confidence * sender_trust_score
        print(f"  Source Credibility: Trust={sender_trust_score:.2f}, OriginalConf={original_confidence:.2f} -> EffectiveConf={effective_confidence:.2f}")

        # 3. Assess Novelty & Evidence (Simplified for PoC)
        novelty_score = 0.5
        evidence_score = 0.5

        if self.content_analyzer:
            analysis_result = self.content_analyzer.process_hsp_fact_content(hsp_fact_payload, hsp_sender_ai_id)
            if analysis_result.get("updated_graph"):
                novelty_score = 0.8

        keywords = re.findall(r'\w+', hsp_fact_payload.get('statement_nl', ''))
        if keywords:
            related_facts = self.ham_memory.query_core_memory(keywords=keywords, limit=5)
            if related_facts:
                evidence_score = min(1.0, 0.5 + (0.1 * len(related_facts)))

        print(f"  Novelty Score: {novelty_score:.2f}, Evidence Score: {evidence_score:.2f}")

        # 4. Final Scoring and Decision
        final_score = (effective_confidence * 0.7) + (novelty_score * 0.15) + (evidence_score * 0.15)
        storage_threshold = self.min_hsp_fact_confidence_to_store
        print(f"  Final Score: {final_score:.2f}, Storage Threshold: {storage_threshold:.2f}")

        if final_score < storage_threshold:
            print("  Final score below threshold. Discarding fact.")
            return None

        # 5. Store the Fact
        record_id = f"lfact_hsp_{uuid.uuid4().hex}"
        fact_content_for_ham = hsp_fact_payload.get('statement_structured') or {"text": hsp_fact_payload.get('statement_nl')}

        metadata = {
            "record_id": record_id, "timestamp": datetime.now().isoformat(),
            "confidence": final_score,
            "original_confidence": original_confidence,
            "trust_score_at_storage": sender_trust_score,
            "novelty_score": novelty_score,
            "evidence_score": evidence_score,
            "corroboration_count": 1,
            "hsp_fact_id": original_hsp_fact_id,
            "hsp_originator_ai_id": hsp_fact_payload.get('source_ai_id'),
            "hsp_sender_ai_id": hsp_sender_ai_id,
        }

        ham_data_type = f"hsp_learned_fact_{hsp_fact_payload.get('tags', ['unknown'])[0]}"
        stored_id = self.ham_memory.store_experience(
            raw_data=fact_content_for_ham,
            data_type=ham_data_type,
            metadata=metadata
        )

        if stored_id:
            print(f"  Fact passed quality assessment and stored with HAM ID '{stored_id}'.")
        else:
            print("  Fact passed quality assessment but failed to store in HAM.")

        return stored_id

    async def learn_from_project_case(self, project_case: Dict[str, Any]):
        """
        Analyzes a completed project case, stores it, and attempts to distill a reusable strategy.
        """
        print(f"[{self.ai_id}] LearningManager: Processing project case for user query: '{project_case.get('user_query')}'")

        case_id = f"proj_case_{uuid.uuid4().hex}"

        # First, store the raw project case for auditing and deeper analysis later.
        raw_case_metadata = {
            "record_id": case_id, "timestamp": datetime.now().isoformat(),
            "user_id": project_case.get("user_id"), "session_id": project_case.get("session_id"),
            "source": "agent_collaboration_project"
        }
        self.ham_memory.store_experience(raw_data=project_case, data_type="project_execution_case", metadata=raw_case_metadata)

        # Now, attempt to distill a reusable strategy from this successful case.
        # This requires a powerful LLM.
        if not self.fact_extractor.llm: # fact_extractor holds the llm_interface
            print(f"[{self.ai_id}] No LLM interface available in FactExtractor, cannot distill strategy.")
            return

        distillation_prompt = self._create_strategy_distillation_prompt(project_case)
        raw_strategy_output = self.fact_extractor.llm.generate_response(prompt=distillation_prompt, params={"temperature": 0.0})

        try:
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_strategy_output)
            strategy_json_str = json_match.group(1) if json_match else raw_strategy_output
            distilled_strategy = json.loads(strategy_json_str)

            # Basic validation of the distilled strategy
            if "strategy_name" in distilled_strategy and "applicable_keywords" in distilled_strategy and "subtask_template" in distilled_strategy:
                strategy_id = f"strat_{uuid.uuid4().hex}"
                strategy_metadata = {
                    "record_id": strategy_id, "timestamp": datetime.now().isoformat(),
                    "source_case_id": case_id, "distilled_by": self.ai_id
                }
                self.ham_memory.store_experience(
                    raw_data=distilled_strategy,
                    data_type="learned_collaboration_strategy",
                    metadata=strategy_metadata
                )
                print(f"[{self.ai_id}] Successfully distilled and stored collaboration strategy '{distilled_strategy['strategy_name']}' (ID: {strategy_id}).")
            else:
                print(f"[{self.ai_id}] Distilled strategy is missing required fields. Output: {distilled_strategy}")

        except json.JSONDecodeError:
            print(f"[{self.ai_id}] Failed to decode JSON from strategy distillation output. Raw: {raw_strategy_output}")

    def _create_strategy_distillation_prompt(self, project_case: Dict[str, Any]) -> str:
        """
        Creates a prompt for an LLM to distill a reusable strategy from a successful project case.
        """
        # We need to remove large, raw data from the prompt to keep it concise.
        cleaned_subtasks = []
        for task in project_case.get("decomposed_subtasks", []):
            cleaned_params = {k: v[:100] + '...' if isinstance(v, str) and len(v) > 100 else v for k, v in task.get("task_parameters", {}).items()}
            cleaned_subtasks.append({
                "capability_needed": task.get("capability_needed"),
                "task_parameters_schema": cleaned_params,
                "task_description": task.get("task_description")
            })

        prompt = f"""
You are a brilliant AI strategist. Your goal is to analyze a successful project execution and generalize it into a reusable strategy template.
From the following project case, identify the core user intent and the successful sequence of capabilities used. Then, create a generalized strategy as a valid JSON object.

The JSON object MUST contain:
1.  `strategy_name`: A concise, descriptive name for the strategy (e.g., "Summarize CSV Data and Identify Trends").
2.  `applicable_keywords`: A list of lowercase keywords from a user's request that would trigger this strategy (e.g., ["analyze", "summarize", "csv", "report"]).
3.  `subtask_template`: An array of subtask objects. This should be a template for future use.
    - For parameters that should be filled in by the user's new request, use placeholders like `"<user_provided_data>"` or `"<user_specified_topic>"`.
    - For parameters that are outputs of previous steps, use the placeholder `"<output_of_task_X>"`, where X is the 0-based index of the prerequisite task.

---
**PROJECT CASE TO ANALYZE:**
- **User's Original Request:** "{project_case.get('user_query')}"
- **Decomposition Plan Used:** {json.dumps(cleaned_subtasks, indent=2)}
- **Final Response Summary:** "{project_case.get('final_response', '')[:200]}..."

---
**Distilled Strategy (JSON Object Only):**
"""
        return prompt

if __name__ == '__main__':
    print("--- LearningManager Standalone Test ---")
    # Mock HAMMemoryManager, FactExtractorModule, HSPConnector, TrustManager, ContentAnalyzerModule for full test
    # This __main__ block needs significant updates to test new TrustManager and conflict logic.
    # For now, keeping it as is, focusing on module-level changes. Unit/Integration tests are key.

    class MockHAMMemoryManager:
        def __init__(self):
            self.stored_experiences: Dict[str, Dict[str, Any]] = {}
            self.next_id = 1

        def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
            mem_id = f"mock_{self.next_id}"
            self.next_id += 1
            current_metadata = metadata or {}
            self.stored_experiences[mem_id] = {"d": raw_data, "t": data_type, "m": current_metadata}
            print(f"MockHAM Stored: {mem_id}")

            # If this new fact supersedes others, mark them in the mock HAM
            if 'supersedes_ham_records' in current_metadata and isinstance(current_metadata['supersedes_ham_records'], list):
                for old_ham_id in current_metadata['supersedes_ham_records']:
                    if old_ham_id in self.stored_experiences:
                        if 'm' not in self.stored_experiences[old_ham_id]: # ensure 'm' (metadata) key exists
                           self.stored_experiences[old_ham_id]['m'] = {}
                        self.stored_experiences[old_ham_id]['m']['is_superseded_by'] = mem_id
                        print(f"MockHAM: Marked old record '{old_ham_id}' as superseded by '{mem_id}'")
            return mem_id

        def query_core_memory(self, metadata_filters: Optional[Dict[str, Any]] = None,
                              data_type_filter: Optional[str] = None, limit: int = 1, **kwargs) -> List[Dict[str, Any]]:
            print(f"MockHAM Query: meta_filters={metadata_filters}, type_filter={data_type_filter}")

            candidate_results = []
            # Iterate in reverse order of storage for some recency bias if multiple match before limit
            sorted_keys = sorted(self.stored_experiences.keys(), reverse=True)

            for k in sorted_keys:
                v = self.stored_experiences[k]
                meta = v.get('m', {})

                # Skip superseded facts
                if meta.get('is_superseded_by'):
                    continue

                match_all_filters = True
                if data_type_filter and not v.get('t', '').startswith(data_type_filter):
                    match_all_filters = False

                if match_all_filters and metadata_filters:
                    for fk, fv in metadata_filters.items():
                        if meta.get(fk) != fv:
                            match_all_filters = False
                            break

                if match_all_filters:
                    candidate_results.append({"id": k, "metadata": meta, "rehydrated_gist": {"summary": str(v['d'])}})

            # Apply limit to final candidates
            return candidate_results[:limit]


    class MockFactExtractor:
        def extract_facts(self, text, user_id):
            if "store this" in text: return [{"fact_type":"test_statement","content":{"data":text},"confidence":0.9}]
            return []

    class MockHSPConnector:
        def __init__(self, *args): self.published_facts = []
        def publish_fact(self, payload, topic): self.published_facts.append(payload); print(f"MockHSP: Published to {topic}: {payload.get('id')}")
        def connect(self): return True

    class MockTrustManager:
        def get_trust_score(self, ai_id): return 0.8 # Assume good trust for testing process_and_store_hsp_fact
        def update_trust_score(self, ai_id, adjustment): pass

    class MockContentAnalyzer:
        def process_hsp_fact_content(self, payload, sender_id):
            print(f"MockCA: Processing HSP fact from {sender_id} with ID {payload.get('id')}")
            # Simulate extraction for semantic triple
            if payload.get('statement_type') == "semantic_triple" and payload.get('statement_structured'):
                ss = payload.get('statement_structured')
                return {
                    "updated_graph": True,
                    "processed_triple": {
                        "subject_id": ss.get('subject_uri'), # Keep it simple for mock
                        "predicate_type": ss.get('predicate_uri'),
                        "object_id": ss.get('object_literal') or ss.get('object_uri'),
                        "original_subject_uri": ss.get('subject_uri'),
                        "original_predicate_uri": ss.get('predicate_uri'),
                        "original_object_uri_or_literal": ss.get('object_literal') or ss.get('object_uri'),
                        "object_is_uri": bool(ss.get('object_uri'))
                    }
                }
            return {"updated_graph": True} # Default for NL or other types


    mock_ham = MockHAMMemoryManager()
    mock_fe = MockFactExtractor()
    mock_hsp = MockHSPConnector(None,None,None)
    mock_tm = MockTrustManager()
    mock_ca = MockContentAnalyzer()

    lm_config = {
        "learning_thresholds": { "min_fact_confidence_to_store": 0.7, "min_fact_confidence_to_share_via_hsp": 0.8, "min_hsp_fact_confidence_to_store": 0.5, "hsp_fact_conflict_confidence_delta": 0.1},
        "default_hsp_fact_topic": "hsp/facts/test"
    }
    lm = LearningManager("test_lm_ai", mock_ham, mock_fe, mock_ca, mock_hsp, mock_tm, lm_config)

    print("\nTest 1: Store user learnable, check HSP publish")
    lm.process_and_store_learnables("User says: store this important fact.", "user1", "sess1", "ref1")
    assert len(mock_ham.stored_experiences) == 1
    assert len(mock_hsp.published_facts) == 1
    last_published_id = mock_hsp.published_facts[0]['id']

    print("\nTest 2: Process incoming HSP fact (no conflict initially)")
    # Lowered confidence_score from 0.9 to 0.8 to allow Test 3 to supersede
    incoming_fact_payload = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1", confidence_score=0.8, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    incoming_envelope = HSPMessageEnvelope(message_id="msg1", sender_ai_id="peer_ai_1", recipient_ai_id=lm.ai_id, timestamp_sent="",message_type="HSP::Fact_v0.1",protocol_version="0.1",communication_pattern="publish",payload=incoming_fact_payload) #type: ignore
    stored_ham_id_1 = lm.process_and_store_hsp_fact(incoming_fact_payload, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_1 is not None
    assert abs(mock_ham.stored_experiences[stored_ham_id_1]['m']['confidence'] - (0.8 * 0.8)) < 0.001 # 0.8 * default trust 0.8
    assert mock_ham.stored_experiences[stored_ham_id_1]['m']['hsp_fact_id'] == "hsp_fact_abc"
    assert mock_ham.stored_experiences[stored_ham_id_1]['m']['hsp_originator_ai_id'] == "peer_ai_1"


    print("\nTest 3: Process conflicting HSP fact (new one much higher confidence)")
    # Trust for peer_ai_1 is 0.8. Effective confidence of stored fact is 0.9 * 0.8 = 0.72
    # New fact from same peer, same original ID, but higher original confidence
    incoming_fact_payload_conflict_higher = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - updated and more confident", confidence_score=0.99, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    # Effective confidence = 0.99 * 0.8 = 0.792. This is > 0.72 + 0.1 (delta)
    stored_ham_id_2 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_higher, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_2 is not None, "Higher confidence conflicting fact should be stored"
    assert abs(mock_ham.stored_experiences[stored_ham_id_2]['m']['confidence'] - (0.99 * 0.8)) < 0.001
    assert "supersedes_ham_records" in mock_ham.stored_experiences[stored_ham_id_2]['m']
    assert mock_ham.stored_experiences[stored_ham_id_2]['m']['supersedes_ham_records'] == [stored_ham_id_1]
    assert mock_ham.stored_experiences[stored_ham_id_2]['m']['resolution_strategy'] == "confidence_supersede_type1"


    print("\nTest 4: Process conflicting HSP fact (new one lower confidence)")
    # Stored fact (Test 3) has effective confidence 0.792.
    incoming_fact_payload_conflict_lower = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - less confident update", confidence_score=0.6, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    # Effective confidence = 0.6 * 0.8 = 0.48. This is < (0.792 - 0.1). Should be ignored.
    stored_ham_id_3 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_lower, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_3 is None, "Lower confidence conflicting fact should be ignored"

    print("\nTest 5: Process conflicting HSP fact (similar confidence, different value)")
    # Stored fact (Test 3) has effective confidence 0.792.
    # Incoming fact: original confidence 0.98 -> effective 0.98 * 0.8 = 0.784.
    # This is within +/- 0.1 of 0.792. Values are different. Should log contradiction.
    incoming_fact_payload_conflict_similar = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - similar confidence, different value", confidence_score=0.98, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    stored_ham_id_4 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_similar, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_4 is not None, "Similar confidence conflicting fact (diff value) should be stored with conflict logged"
    assert "conflicts_with_ham_records" in mock_ham.stored_experiences[stored_ham_id_4]['m']
    assert mock_ham.stored_experiences[stored_ham_id_4]['m']['conflicts_with_ham_records'] == [stored_ham_id_2] # Conflicts with the one stored in Test 3
    assert mock_ham.stored_experiences[stored_ham_id_4]['m']['resolution_strategy'] == "log_contradiction_type1"

    print("\nTest 5b: Process conflicting HSP fact (similar confidence, SAME value - should be ignored)")
    # Stored fact (Test 5, mock_4) has statement "Peer fact 1 - similar confidence, different value" and effective confidence 0.784
    # Incoming fact: original confidence 0.98 -> effective 0.784.
    # We make the statement identical to mock_4's statement.
    statement_from_mock_4 = "Peer fact 1 - similar confidence, different value" # This was the content of mock_4 (stored_ham_id_4)
    incoming_fact_payload_conflict_same_val = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl=statement_from_mock_4, confidence_score=0.98, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    stored_ham_id_5b = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_same_val, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_5b is None, "Similar confidence, same value fact should be ignored"


    print("\nTest 6: Process HSP fact (semantic conflict - new one more confident)")
    # Setup: Store an initial semantic fact via mock_ham directly for simplicity
    # Assume peer_ai_1 (trust 0.8) sent it earlier.
    initial_semantic_fact_ham_id = "mock_sem_1"
    mock_ham.stored_experiences[initial_semantic_fact_ham_id] = {
        "d": {"subject_uri": "http://example.org/entity/E1", "predicate_uri": "http://example.org/prop/P1", "object_literal": "old_value"},
        "t": "hsp_learned_fact_semantic",
        "m": {
            "record_id": "lfact_hsp_sem_initial", "timestamp": datetime.now().isoformat(),
            "confidence": 0.6 * 0.8, # Effective confidence of stored fact: 0.48
            "hsp_fact_id": "hsp_sem_fact_001", "hsp_originator_ai_id": "other_ai_semantic", "hsp_sender_ai_id": "peer_ai_1",
            "hsp_semantic_subject": "http://example.org/entity/E1",
            "hsp_semantic_predicate": "http://example.org/prop/P1",
            "hsp_semantic_object": "old_value",
            "source_text": "E1 P1 old_value"
        }
    }

    # New incoming semantic fact about the same S/P but different O, from peer_ai_2 (trust 0.8)
    # Original confidence 0.9 -> effective 0.72. This is > 0.48 + 0.1 (delta)
    incoming_semantic_conflict_payload = HSPFactPayload(
        id="hsp_sem_fact_002", source_ai_id="peer_ai_2",
        statement_type="semantic_triple",
        statement_structured={"subject_uri": "http://example.org/entity/E1",
                              "predicate_uri": "http://example.org/prop/P1",
                              "object_literal": "new_value_more_confident"},
        confidence_score=0.9, timestamp_created=datetime.now().isoformat()
    ) #type: ignore
    incoming_semantic_envelope = HSPMessageEnvelope(message_id="msg_sem_conflict", sender_ai_id="peer_ai_2", recipient_ai_id=lm.ai_id, timestamp_sent="",message_type="HSP::Fact_v0.1",protocol_version="0.1",communication_pattern="publish",payload=incoming_semantic_conflict_payload) #type: ignore

    stored_sem_conflict_id = lm.process_and_store_hsp_fact(incoming_semantic_conflict_payload, "peer_ai_2", incoming_semantic_envelope)
    assert stored_sem_conflict_id is not None, "Semantically conflicting fact (higher conf) should be stored"
    assert mock_ham.stored_experiences[stored_sem_conflict_id]['m']['resolution_strategy'] == "confidence_supersede_type2"
    assert mock_ham.stored_experiences[stored_sem_conflict_id]['m']['supersedes_ham_records'] == [initial_semantic_fact_ham_id]
    assert mock_ham.stored_experiences[stored_sem_conflict_id]['m']['hsp_semantic_object'] == "new_value_more_confident"


    print("\nTest 7: Process HSP fact (semantic conflict - numerical merge)")
    # Stored fact (from Test 6) has S/P E1/P1, O="new_value_more_confident", effective_confidence = 0.72 (stored as 'confidence' in HAM)
    # New incoming fact for E1/P1 from peer_ai_1 (trust 0.8), original confidence 0.85 -> effective 0.68
    # Values are numerical: existing "100.0" (need to update Test 6 mock data for this to work), new "120.0"

    # Update the previously stored semantic fact to have a numerical object for merging
    # This is mock_5 from Test 6. Its timestamp was datetime.now() at the time of Test 6.
    timestamp_of_existing_fact_for_merge = mock_ham.stored_experiences[stored_sem_conflict_id]['m']['hsp_fact_timestamp_created']

    mock_ham.stored_experiences[stored_sem_conflict_id]['m']['hsp_semantic_object'] = "100.0"
    mock_ham.stored_experiences[stored_sem_conflict_id]['d']['object_literal'] = "100.0" # Update raw data too for consistency
    mock_ham.stored_experiences[stored_sem_conflict_id]['m']['source_text'] = "E1 P1 100.0" # Update source text too

    # Ensure the new fact for merge is OLDER or same time to not win by recency, allowing merge to be tested.
    # If it's newer, tie_break_trust_recency will supersede.
    # For simplicity, let's use a slightly older fixed timestamp string, or reuse the existing one to ensure not newer.
    older_timestamp_for_merge_payload = datetime(2023,1,1,0,0,0).isoformat() # Clearly older
    if datetime.fromisoformat(timestamp_of_existing_fact_for_merge.replace('Z', '+00:00')) < datetime.fromisoformat(older_timestamp_for_merge_payload.replace('Z', '+00:00')):
        # This case should not happen if older_timestamp_for_merge_payload is truly older. Safety.
        older_timestamp_for_merge_payload = timestamp_of_existing_fact_for_merge


    numerical_merge_payload = HSPFactPayload(
        id="hsp_num_merge_fact_001", source_ai_id="peer_ai_1",
        statement_type="semantic_triple",
        statement_structured={"subject_uri": "http://example.org/entity/E1",
                              "predicate_uri": "http://example.org/prop/P1",
                              "object_literal": "120.0"}, # Numerical value as string
        confidence_score=0.85, timestamp_created=older_timestamp_for_merge_payload
    ) #type: ignore

    # Existing fact (stored_sem_conflict_id, which is mock_5): effective_confidence = 0.72, value = 100.0
    # New fact: effective_confidence = 0.68, value = 120.0
    # Confidences are within delta (0.1). 0.72 and 0.68.
    # Expected merged value: (100.0 * 0.72 + 120.0 * 0.68) / (0.72 + 0.68) = (72 + 81.6) / 1.4 = 153.6 / 1.4 = 109.71...
    # Expected merged confidence: (0.72 + 0.68) / 2 = 0.70

    stored_num_merge_id = lm.process_and_store_hsp_fact(numerical_merge_payload, "peer_ai_1", incoming_semantic_envelope) # Re-use envelope, change sender
    assert stored_num_merge_id is not None, "Numerical merge fact should be stored"
    merged_fact_meta = mock_ham.stored_experiences[stored_num_merge_id]['m']
    assert merged_fact_meta['resolution_strategy'] == "numerical_merge_type2"
    assert merged_fact_meta['merged_from_ham_records'] == [stored_sem_conflict_id]
    assert abs(float(merged_fact_meta['hsp_semantic_object']) - 109.714) < 0.01
    assert abs(merged_fact_meta['confidence'] - 0.70) < 0.01
    assert "Numerically merged value for S='http://example.org/entity/E1'" in merged_fact_meta['source_text']


    print("\nLearningManager standalone test finished.")

    async def analyze_for_personality_adjustment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes text for potential personality adjustments.

        Args:
            text (str): The text to analyze.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of personality adjustments, or None if no adjustments are needed.
        """
        # This is a simplified implementation. A real-world scenario would
        # involve a more sophisticated analysis.
        if "be more formal" in text.lower():
            return {"communication_style.tone_presets.default": "formal"}
        elif "be more friendly" in text.lower():
            return {"communication_style.tone_presets.default": "friendly"}
        else:
            return None
