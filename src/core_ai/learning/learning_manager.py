import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.learning.fact_extractor_module import FactExtractorModule
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from core_ai.trust_manager.trust_manager_module import TrustManager
from shared.types.common_types import LearnedFactRecord
from hsp.connector import HSPConnector
from hsp.types import HSPFactPayload, HSPMessageEnvelope


class LearningManager:
    def __init__(self,
                 ai_id: str,
                 ham_memory_manager: HAMMemoryManager,
                 fact_extractor: FactExtractorModule,
                 content_analyzer: Optional[ContentAnalyzerModule] = None,
                 hsp_connector: Optional[HSPConnector] = None,
                 trust_manager: Optional[TrustManager] = None,
                 operational_config: Optional[Dict[str, Any]] = None):
        self.ai_id = ai_id
        self.ham_memory = ham_memory_manager
        self.fact_extractor = fact_extractor
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

    def process_and_store_learnables(
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
        print(f"LearningManager (AI ID: {self.ai_id}): Processing HSP fact '{hsp_fact_payload.get('id')}' from sender '{hsp_sender_ai_id}'.")

        original_confidence = hsp_fact_payload.get('confidence_score', 0.0)
        if not isinstance(original_confidence, (float, int)):
            try: original_confidence = float(original_confidence)
            except (ValueError, TypeError): original_confidence = 0.0

        effective_confidence = original_confidence
        sender_trust_score = TrustManager.DEFAULT_TRUST_SCORE
        if self.trust_manager:
            sender_trust_score = self.trust_manager.get_trust_score(hsp_sender_ai_id)
            effective_confidence = original_confidence * sender_trust_score
            print(f"  Sender '{hsp_sender_ai_id}' Trust: {sender_trust_score:.2f}. Original Fact Confidence: {original_confidence:.2f} -> Effective Confidence: {effective_confidence:.2f}")

        if effective_confidence < self.min_hsp_fact_confidence_to_store:
            print(f"  Effective confidence {effective_confidence:.2f} is below threshold {self.min_hsp_fact_confidence_to_store}. Not storing HSP fact.")
            return None

        # --- Conflict Detection (PoC for Conflict Type 1) ---
        original_hsp_fact_id = hsp_fact_payload.get('id')
        original_hsp_fact_originator = hsp_fact_payload.get('source_ai_id')
        conflict_metadata_update: Dict[str, Any] = {}

        if original_hsp_fact_id and original_hsp_fact_originator:
            conflict_query_filters = {
                "hsp_fact_id": original_hsp_fact_id,
                "hsp_originator_ai_id": original_hsp_fact_originator
            }
            existing_facts = self.ham_memory.query_core_memory(
                metadata_filters=conflict_query_filters, data_type_filter="hsp_learned_fact_", limit=1 )

            if existing_facts:
                existing_ham_record = existing_facts[0]
                existing_ham_id = existing_ham_record.get('id') # This is HAM's internal mem_id
                existing_stored_confidence = existing_ham_record.get("metadata", {}).get("confidence", 0.0)
                print(f"  Conflict Check: Incoming HSP fact '{original_hsp_fact_id}' (orig AI: '{original_hsp_fact_originator}') matches existing HAM record '{existing_ham_id}'.")

                if effective_confidence > existing_stored_confidence + self.hsp_fact_conflict_confidence_delta:
                    print(f"    New fact more confident ({effective_confidence:.2f} vs stored {existing_stored_confidence:.2f}). PoC: Storing new. Old HAM record '{existing_ham_id}' is not deleted/updated yet.")
                    conflict_metadata_update = {"supersedes_ham_record": existing_ham_id, "resolution_strategy": "new_higher_confidence"}
                elif effective_confidence < existing_stored_confidence - self.hsp_fact_conflict_confidence_delta:
                    print(f"    Existing fact more confident ({existing_stored_confidence:.2f} vs new {effective_confidence:.2f}). Ignoring new fact.")
                    return None
                else:
                    print(f"    Similar confidence ({effective_confidence:.2f} vs stored {existing_stored_confidence:.2f}). Storing new instance, noting potential conflict.")
                    conflict_metadata_update = {"conflicts_with_ham_record": existing_ham_id, "resolution_strategy": "similar_confidence_store_new"}

        # Proceed to store
        record_id = f"lfact_hsp_{uuid.uuid4().hex}"
        timestamp = datetime.now().isoformat()
        confidence_to_store = effective_confidence

        fact_content_for_ham: Any
        source_text_for_ham: str
        if hsp_fact_payload.get('statement_structured'):
            fact_content_for_ham = hsp_fact_payload['statement_structured']
            source_text_for_ham = hsp_fact_payload.get('statement_nl', json.dumps(fact_content_for_ham))
        elif hsp_fact_payload.get('statement_nl'):
            fact_content_for_ham = {"text": hsp_fact_payload['statement_nl']}
            source_text_for_ham = hsp_fact_payload['statement_nl']
        else:
            print(f"  HSP fact '{original_hsp_fact_id}' has no statement_structured or statement_nl. Cannot process.")
            return None

        fact_type_from_hsp = "hsp_derived_fact"
        if hsp_fact_payload.get('tags') and len(hsp_fact_payload['tags']) > 0: # type: ignore
            fact_type_from_hsp = hsp_fact_payload['tags'][0] # type: ignore

        learned_record_metadata = {
            "record_id": record_id, "timestamp": timestamp,
            "user_id": None, "session_id": None,
            "source_interaction_ref": hsp_envelope.get('message_id'),
            "fact_type": fact_type_from_hsp, "confidence": confidence_to_store,
            "source_text": source_text_for_ham,
            "hsp_originator_ai_id": original_hsp_fact_originator,
            "hsp_sender_ai_id": hsp_sender_ai_id,
            "hsp_fact_id": original_hsp_fact_id,
            **conflict_metadata_update # Add conflict resolution info
        }

        ham_data_type = f"hsp_learned_fact_{fact_type_from_hsp.lower().replace(' ', '_')}"
        print(f"  Storing HSP-derived fact - Type: {ham_data_type}, Content: {fact_content_for_ham}, Meta: {learned_record_metadata}")
        stored_id = self.ham_memory.store_experience(raw_data=fact_content_for_ham, data_type=ham_data_type, metadata=learned_record_metadata)

        if stored_id:
            print(f"  Stored HSP fact '{record_id}' (original HSP ID: '{original_hsp_fact_id}') with HAM ID '{stored_id}'")
            if self.content_analyzer:
                try:
                    print(f"  Passing HSP fact content (ID: '{original_hsp_fact_id}') to ContentAnalyzerModule.")
                    analysis_updated_graph = self.content_analyzer.process_hsp_fact_content(hsp_fact_payload, hsp_sender_ai_id) # type: ignore
                    if analysis_updated_graph: print(f"  ContentAnalyzerModule reported graph updates for HSP fact '{original_hsp_fact_id}'.")
                    else: print(f"  ContentAnalyzerModule did not report graph updates for HSP fact '{original_hsp_fact_id}'.")
                except Exception as e:
                    print(f"  Error calling ContentAnalyzerModule for HSP fact '{original_hsp_fact_id}': {e}")
            return stored_id
        else:
            print(f"  Failed to store HSP fact '{record_id}' in HAM.")
            return None

if __name__ == '__main__':
    print("--- LearningManager Standalone Test ---")
    # Mock HAMMemoryManager, FactExtractorModule, HSPConnector, TrustManager, ContentAnalyzerModule for full test
    # This __main__ block needs significant updates to test new TrustManager and conflict logic.
    # For now, keeping it as is, focusing on module-level changes. Unit/Integration tests are key.

    class MockHAMMemoryManager: # Simplified from previous test
        def __init__(self): self.stored_experiences = {}; self.next_id = 1
        def store_experience(self, raw_data, data_type, metadata=None): mem_id=f"mock_{self.next_id}"; self.next_id+=1; self.stored_experiences[mem_id]={"d":raw_data,"t":data_type,"m":metadata or {}}; print(f"MockHAM Stored: {mem_id}"); return mem_id
        def query_core_memory(self, metadata_filters=None, data_type_filter=None, limit=1, **kwargs):
            print(f"MockHAM Query: meta_filters={metadata_filters}, type_filter={data_type_filter}")
            results = []
            for k,v in self.stored_experiences.items():
                meta = v.get('m',{})
                if data_type_filter and not v.get('t','').startswith(data_type_filter): continue
                if metadata_filters:
                    match_all = True
                    for fk, fv in metadata_filters.items():
                        if meta.get(fk) != fv: match_all = False; break
                    if not match_all: continue
                # Simplified recall_gist structure for test
                results.append({"id": k, "metadata": meta, "rehydrated_gist": {"summary": str(v['d'])}})
                if len(results) >= limit: break
            return results


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
        def process_hsp_fact_content(self, payload, sender_id): print(f"MockCA: Processing HSP fact from {sender_id}"); return True


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
    incoming_fact_payload = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1", confidence_score=0.9, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    incoming_envelope = HSPMessageEnvelope(message_id="msg1", sender_ai_id="peer_ai_1", recipient_ai_id=lm.ai_id, timestamp_sent="",message_type="HSP::Fact_v0.1",protocol_version="0.1",communication_pattern="publish",payload=incoming_fact_payload) #type: ignore
    stored_ham_id_1 = lm.process_and_store_hsp_fact(incoming_fact_payload, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_1 is not None
    assert mock_ham.stored_experiences[stored_ham_id_1]['m']['confidence'] == (0.9 * 0.8) # 0.9 * default trust 0.8
    assert mock_ham.stored_experiences[stored_ham_id_1]['m']['hsp_fact_id'] == "hsp_fact_abc"
    assert mock_ham.stored_experiences[stored_ham_id_1]['m']['hsp_originator_ai_id'] == "peer_ai_1"


    print("\nTest 3: Process conflicting HSP fact (new one much higher confidence)")
    # Trust for peer_ai_1 is 0.8. Effective confidence of stored fact is 0.9 * 0.8 = 0.72
    # New fact from same peer, same original ID, but higher original confidence
    incoming_fact_payload_conflict_higher = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - updated and more confident", confidence_score=0.99, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    # Effective confidence = 0.99 * 0.8 = 0.792. This is > 0.72 + 0.1 (delta)
    stored_ham_id_2 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_higher, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_2 is not None, "Higher confidence conflicting fact should be stored"
    assert mock_ham.stored_experiences[stored_ham_id_2]['m']['confidence'] == (0.99 * 0.8)
    # TODO: Add check that old one is marked or something, for now just ensure new one stored.
    # Current PoC stores new one, does not delete/update old one.
    assert "supersedes_ham_record" in mock_ham.stored_experiences[stored_ham_id_2]['m']
    assert mock_ham.stored_experiences[stored_ham_id_2]['m']['supersedes_ham_record'] == stored_ham_id_1


    print("\nTest 4: Process conflicting HSP fact (new one lower confidence)")
    incoming_fact_payload_conflict_lower = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - less confident update", confidence_score=0.6, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    # Effective confidence = 0.6 * 0.8 = 0.48. This is < (0.792 - 0.1). Should be ignored.
    stored_ham_id_3 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_lower, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_3 is None, "Lower confidence conflicting fact should be ignored"

    print("\nTest 5: Process conflicting HSP fact (similar confidence)")
    incoming_fact_payload_conflict_similar = HSPFactPayload(id="hsp_fact_abc", source_ai_id="peer_ai_1", statement_nl="Peer fact 1 - similar confidence update", confidence_score=0.98, statement_type="natural_language", timestamp_created=datetime.now().isoformat()) #type: ignore
    # Effective confidence = 0.98 * 0.8 = 0.784. This is within +/- 0.1 of 0.792. Should store new with note.
    stored_ham_id_4 = lm.process_and_store_hsp_fact(incoming_fact_payload_conflict_similar, "peer_ai_1", incoming_envelope)
    assert stored_ham_id_4 is not None, "Similar confidence conflicting fact should be stored"
    assert "conflicts_with_ham_record" in mock_ham.stored_experiences[stored_ham_id_4]['m']
    # It conflicts with the latest stored version, which is stored_ham_id_2
    assert mock_ham.stored_experiences[stored_ham_id_4]['m']['conflicts_with_ham_record'] == stored_ham_id_2


    print("\nLearningManager standalone test finished.")
```
