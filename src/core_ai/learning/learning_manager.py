# src/core_ai/learning/learning_manager.py
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from src.core_ai.memory.ham_memory_manager import HAMMemoryManager # Corrected
from src.core_ai.learning.fact_extractor_module import FactExtractorModule # Corrected
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule # Corrected
from src.core_ai.trust_manager.trust_manager_module import TrustManager # Corrected
from src.shared.types.common_types import LearnedFactRecord # Corrected
from src.hsp.connector import HSPConnector # Corrected
from src.hsp.types import HSPFactPayload, HSPMessageEnvelope # Corrected
from src.core_ai.personality.personality_manager import PersonalityManager


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
        print(f"LearningManager (AI ID: {self.ai_id}): Processing HSP fact '{hsp_fact_payload.get('id')}' from sender '{hsp_sender_ai_id}'.")

        current_time_iso_for_processing = datetime.now().isoformat() # Timestamp for this processing event

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
                existing_metadata = existing_ham_record.get("metadata", {})
                existing_stored_confidence = existing_metadata.get("confidence", 0.0)
                existing_value_for_conflict_check = existing_metadata.get("source_text", "") # Fallback to source_text
                if existing_metadata.get("hsp_semantic_object") is not None: # Prefer semantic object for comparison
                    existing_value_for_conflict_check = existing_metadata.get("hsp_semantic_object")

                print(f"  Conflict Check (Type 1 - Same ID): Incoming HSP fact '{original_hsp_fact_id}' (orig AI: '{original_hsp_fact_originator}') matches existing HAM record '{existing_ham_id}'.")

                # Value comparison for Type 1
                incoming_value_for_conflict_check = hsp_fact_payload.get('statement_nl', "")
                if hsp_fact_payload.get('statement_type') == "semantic_triple" and hsp_fact_payload.get('statement_structured'):
                    s_struct = hsp_fact_payload.get('statement_structured', {})
                    incoming_value_for_conflict_check = s_struct.get('object_literal') or s_struct.get('object_uri')


                if effective_confidence > existing_stored_confidence + self.hsp_fact_conflict_confidence_delta:
                    print(f"    New fact more confident ({effective_confidence:.2f} vs stored {existing_stored_confidence:.2f}). Storing new.")
                    conflict_metadata_update = {"supersedes_ham_records": [existing_ham_id], "resolution_strategy": "confidence_supersede_type1", "superseded_reason": "higher_confidence"}
                elif effective_confidence < existing_stored_confidence - self.hsp_fact_conflict_confidence_delta:
                    print(f"    Existing fact more confident ({existing_stored_confidence:.2f} vs new {effective_confidence:.2f}). Ignoring new fact.")
                    return None
                elif incoming_value_for_conflict_check == existing_value_for_conflict_check:
                    print(f"    Similar confidence and same value ('{str(incoming_value_for_conflict_check)[:50]}...'). Likely redundant. Ignoring new fact.")
                    # Optionally, update timestamp of existing fact if that's desired behavior
                    return None
                else: # Similar confidence, different values
                    print(f"    Similar confidence ({effective_confidence:.2f} vs stored {existing_stored_confidence:.2f}) but different values. Logging conflict.")
                    conflict_metadata_update = {"conflicts_with_ham_records": [existing_ham_id], "resolution_strategy": "log_contradiction_type1", "conflicting_values": [str(existing_value_for_conflict_check)[:100], str(incoming_value_for_conflict_check)[:100]]}

        # Semantic Identifiers from Content Analyzer will be added to learned_record_metadata later
        # This is placeholder before CA call
        ca_processed_triple_info: Optional[Dict[str, Any]] = None

        # --- Call ContentAnalyzerModule ---
        # This is done *before* semantic conflict check, as CA might extract the semantic URIs needed for it.
        hsp_semantic_subject, hsp_semantic_predicate, hsp_semantic_object = None, None, None
        if self.content_analyzer:
            try:
                print(f"  Passing HSP fact content (ID: '{original_hsp_fact_id}') to ContentAnalyzerModule before semantic conflict check.")
                ca_analysis_result = self.content_analyzer.process_hsp_fact_content(hsp_fact_payload, hsp_sender_ai_id) # type: ignore
                if ca_analysis_result.get("updated_graph"):
                     print(f"  ContentAnalyzerModule reported graph updates for HSP fact '{original_hsp_fact_id}'.")
                if ca_analysis_result.get("processed_triple"):
                    ca_processed_triple_info = ca_analysis_result["processed_triple"]
                    hsp_semantic_subject = ca_processed_triple_info.get("original_subject_uri")
                    hsp_semantic_predicate = ca_processed_triple_info.get("original_predicate_uri")
                    hsp_semantic_object = ca_processed_triple_info.get("original_object_uri_or_literal")
                    print(f"    CA extracted: S='{hsp_semantic_subject}', P='{hsp_semantic_predicate}', O='{hsp_semantic_object}'")
            except Exception as e:
                print(f"  Error calling ContentAnalyzerModule for HSP fact '{original_hsp_fact_id}': {e}")

        # --- Conflict Detection (Type 2 - Semantic Conflict) ---
        # This runs only if no Type 1 conflict already decided to ignore the fact or created a specific Type 1 resolution.
        # And if we have semantic identifiers for the incoming fact.
        if not conflict_metadata_update.get("resolution_strategy", "").endswith("_type1") and \
           not conflict_metadata_update.get("resolution_strategy") == "confidence_supersede_type1" and \
           hsp_semantic_subject and hsp_semantic_predicate:

            semantic_conflict_query_filters = {
                "hsp_semantic_subject": hsp_semantic_subject,
                "hsp_semantic_predicate": hsp_semantic_predicate,
                # We are looking for facts about the same subject/predicate but potentially different object/value
                # And ensure it's not the *exact same* HSP fact ID if it somehow got here without Type 1 conflict handling
                # (e.g. if original_hsp_fact_id was None for incoming, but then CA produced S/P that matches another)
            }
            if original_hsp_fact_id: # Exclude the current fact if it was already stored (e.g. during a re-processing test)
                 # This is tricky. We need to ensure we don't match the *exact same fact instance* if it has these S/P.
                 # A proper way would be to exclude by HAM record ID if we knew it.
                 # For now, this primarily targets different original HSP facts that map to same S/P.
                 pass


            existing_semantic_matches = self.ham_memory.query_core_memory(
                metadata_filters=semantic_conflict_query_filters, data_type_filter="hsp_learned_fact_", limit=5 # Check a few
            )

            conflicting_semantic_records = []
            for record in existing_semantic_matches:
                # Ensure it's not the same original fact if IDs are present and match (safeguard)
                if original_hsp_fact_id and record.get("metadata", {}).get("hsp_fact_id") == original_hsp_fact_id and \
                   original_hsp_fact_originator and record.get("metadata", {}).get("hsp_originator_ai_id") == original_hsp_fact_originator:
                    continue # This is the same fact, handled by Type 1 if it's an update.

                # Check if the object/value is different
                existing_obj = record.get("metadata", {}).get("hsp_semantic_object")
                if existing_obj != hsp_semantic_object: # Values differ for the same S/P
                    conflicting_semantic_records.append(record)

            if conflicting_semantic_records:
                # For PoC, consider the first conflicting record for detailed comparison.
                # A real system might need to handle multiple conflicts.
                first_conflicting_record = conflicting_semantic_records[0]
                existing_ham_id = first_conflicting_record.get('id')
                existing_metadata = first_conflicting_record.get("metadata", {})
                existing_stored_confidence = existing_metadata.get("confidence", 0.0)
                existing_value = existing_metadata.get("hsp_semantic_object", existing_metadata.get("source_text",""))

                print(f"  Conflict Check (Type 2 - Semantic): Incoming fact S/P '{hsp_semantic_subject}/{hsp_semantic_predicate}' with O '{hsp_semantic_object}' conflicts with HAM record '{existing_ham_id}' (O '{existing_value}').")

                # Attempt Resolution Strategies for Type 2 conflict
                # B. Log Explicit Conflict (default if other strategies don't apply or are not enabled)
                resolution_strategy = "log_contradiction_type2"
                current_conflict_meta = {"conflicts_with_ham_records": [existing_ham_id], "resolution_strategy": resolution_strategy, "conflicting_values": [str(existing_value)[:100], str(hsp_semantic_object)[:100]]}

                # A. Supersede/Ignore by confidence (for semantic conflict)
                if effective_confidence > existing_stored_confidence + self.hsp_fact_conflict_confidence_delta:
                    print(f"    New semantically conflicting fact more confident ({effective_confidence:.2f} vs stored {existing_stored_confidence:.2f}). Storing new, superseding.")
                    current_conflict_meta = {"supersedes_ham_records": [existing_ham_id], "resolution_strategy": "confidence_supersede_type2", "superseded_reason": "higher_confidence_semantic"}
                elif effective_confidence < existing_stored_confidence - self.hsp_fact_conflict_confidence_delta:
                    print(f"    Existing semantically conflicting fact more confident ({existing_stored_confidence:.2f} vs new {effective_confidence:.2f}). Ignoring new fact.")
                    return None # Ignore the new fact

                # C. Trust/Recency Tie-Breaking (if confidences are similar)
                # C. Trust/Recency Tie-Breaking (if confidences are similar)
                elif abs(effective_confidence - existing_stored_confidence) <= self.hsp_fact_conflict_confidence_delta:
                    # D. Value Merging/Averaging (Numerical - PoC)
                    # Attempt if the current strategy is still "log_contradiction_type2" (i.e., not superseded by confidence or tie-breaking)
                    # This is a simplified check and needs robust type checking.
                    can_average = False
                    val_new_num, val_old_num = None, None
                    try:
                        val_new_num = float(hsp_semantic_object) # type: ignore
                        val_old_num = float(existing_value)     # type: ignore
                        can_average = True
                        print(f"    Values appear numerical ({val_new_num}, {val_old_num}). Attempting merge.")
                    except (ValueError, TypeError):
                        print(f"    Values ('{hsp_semantic_object}', '{existing_value}') not both numerical for averaging.")
                        pass # Not numerical

                    if can_average and val_new_num is not None and val_old_num is not None:
                        # Trust-weighted average for value
                        merged_value = (val_new_num * effective_confidence + val_old_num * existing_stored_confidence) / (effective_confidence + existing_stored_confidence)
                        # Average confidence for the new merged fact (could be max, or average, etc.)
                        merged_confidence = (effective_confidence + existing_stored_confidence) / 2

                        # The new fact payload's object/value needs to be updated to merged_value
                        # And its confidence to merged_confidence
                        # This is a significant change: we are modifying the incoming fact's interpretation.
                        hsp_semantic_object = str(merged_value) # Update for storing
                        confidence_to_store = merged_confidence # Update for storing

                        # Update fact_content_for_ham if it was based on the structured part
                        if hsp_fact_payload.get('statement_type') == "semantic_triple" and \
                           isinstance(hsp_fact_payload.get('statement_structured'), dict):
                            hsp_fact_payload['statement_structured']['object_literal'] = hsp_semantic_object
                            if 'object_uri' in hsp_fact_payload['statement_structured']: # clear URI if we used literal
                                del hsp_fact_payload['statement_structured']['object_uri']
                            # Also update statement_nl if it's going to be derived from structured, or make a new one.
                            # For PoC, assume source_text_for_ham might need regeneration if it showed old value.
                            # This part is tricky as source_text_for_ham might be the original NL.
                            # The actual update to learned_record_metadata['source_text'] to note the merge
                            # happens later, after learned_record_metadata is initially constructed.
                            # No direct action on learned_record_metadata needed here.
                            pass

                        current_conflict_meta = {
                            "merged_from_ham_records": [existing_ham_id],
                            "resolution_strategy": "numerical_merge_type2",
                            "original_values": [str(val_old_num), str(val_new_num)],
                                "merged_value": merged_value, # The float value
                                "merged_confidence": merged_confidence # Store it here
                        }
                        print(f"    Numerically merged: old_val={val_old_num}, new_val={val_new_num} -> merged_val={merged_value:.2f} with conf={merged_confidence:.2f}")
                        conflict_metadata_update.update(current_conflict_meta) # This now contains merged_confidence if merge happened
                    else:
                        print(f"    Semantically conflicting facts have similar confidence. Applying Trust/Recency tie-breaking.")
                        new_beats_existing = False
                        # Trust
                        existing_sender_ai_id = existing_metadata.get("hsp_sender_ai_id")
                        existing_sender_trust = self.trust_manager.get_trust_score(existing_sender_ai_id) if self.trust_manager and existing_sender_ai_id else TrustManager.DEFAULT_TRUST_SCORE

                        if sender_trust_score > existing_sender_trust + 0.05: # Needs a delta for trust comparison
                            new_beats_existing = True
                            print(f"      Tie-break: New fact preferred due to higher sender trust ({sender_trust_score:.2f} vs {existing_sender_trust:.2f}).")
                        elif existing_sender_trust > sender_trust_score + 0.05:
                            new_beats_existing = False # Assume new does not beat existing initially for this block
                            print(f"      Tie-break: Existing fact preferred due to higher sender trust ({existing_sender_trust:.2f} vs {sender_trust_score:.2f}). New fact will not supersede based on trust.")
                            # Let current_conflict_meta remain "log_contradiction_type2" or whatever it was.
                            # Do not return None here, to allow other strategies (like merge if applicable) or default logging for the new fact.
                            # However, for numerical merge test, we want it to proceed if trust doesn't make new win.
                            # If existing is more trusted, the new fact should generally be ignored unless it's a merge candidate that improves things.
                            # For now, if existing is more trusted, let's assume the new one is not stored unless numerical merge explicitly creates a *new* merged fact.
                            # This means the "new_beats_existing" flag from trust determines if current_conflict_meta is updated to supersede.
                            # If new_beats_existing is false after trust, it remains false.

                        # Only proceed to recency if trust didn't yield a "new_beats_existing = True"
                        if not new_beats_existing: # This means either trust was similar, or new lost on trust.
                            new_timestamp_str = hsp_fact_payload.get('timestamp_created', current_time_iso_for_processing)
                            existing_timestamp_str = existing_metadata.get("hsp_fact_timestamp_created", existing_metadata.get("timestamp"))
                            try:
                                new_dt = datetime.fromisoformat(new_timestamp_str.replace('Z', '+00:00')) if isinstance(new_timestamp_str, str) else datetime.min
                                existing_dt = datetime.fromisoformat(existing_timestamp_str.replace('Z', '+00:00')) if isinstance(existing_timestamp_str, str) else datetime.min
                                if new_dt > existing_dt:
                                    new_beats_existing = True # New wins by recency
                                    print(f"      Tie-break: New fact preferred due to recency ({new_dt} vs {existing_dt}).")
                                else:
                                    # New is older or same age. new_beats_existing remains False.
                                    print(f"      Tie-break: Existing fact preferred or same by recency. New fact will not supersede based on recency.")
                            except ValueError:
                                print(f"      Tie-break: Could not compare timestamps for recency ('{new_timestamp_str}', '{existing_timestamp_str}'). Defaulting to current strategy.")
                                # new_beats_existing remains False.

                        if new_beats_existing: # If new won by either trust or recency
                             current_conflict_meta = {"supersedes_ham_records": [existing_ham_id], "resolution_strategy": "tie_break_trust_recency_type2"}
                        # If new_beats_existing is still False, current_conflict_meta remains as "log_contradiction_type2" (or whatever it was before this block)
                        conflict_metadata_update.update(current_conflict_meta)

        # Proceed to store
        record_id = f"lfact_hsp_{uuid.uuid4().hex}"
        # `timestamp` for the record will be defined when learned_record_metadata is built

        # Determine the final confidence for storage
        if conflict_metadata_update.get("resolution_strategy") == "numerical_merge_type2" and \
           "merged_confidence" in conflict_metadata_update:
            confidence_to_store = conflict_metadata_update["merged_confidence"]
        else:
            confidence_to_store = effective_confidence # Default if not merged, or if merge metadata is incomplete

        timestamp_for_record = datetime.now().isoformat() # Timestamp for the new HAM record

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

        print(f"  DEBUG: Final confidence_to_store before metadata construction: {confidence_to_store}")
        learned_record_metadata = {
            "record_id": record_id, "timestamp": timestamp_for_record,
            "user_id": None, "session_id": None,
            "source_interaction_ref": hsp_envelope.get('message_id'),
            "fact_type": fact_type_from_hsp, "confidence": confidence_to_store,
            "source_text": source_text_for_ham,
            "hsp_originator_ai_id": original_hsp_fact_originator,
            "hsp_sender_ai_id": hsp_sender_ai_id,
            "hsp_fact_id": original_hsp_fact_id,
            "hsp_fact_timestamp_created": hsp_fact_payload.get('timestamp_created', current_time_iso_for_processing), # Store original creation time
            **conflict_metadata_update # Add conflict resolution info
        }

        # Add semantic URIs from CA to metadata if available
        # Default to CA's extracted object, but override if numerical merge occurred.
        final_hsp_semantic_object = None
        if ca_processed_triple_info:
            learned_record_metadata["hsp_semantic_subject"] = ca_processed_triple_info.get("original_subject_uri")
            learned_record_metadata["hsp_semantic_predicate"] = ca_processed_triple_info.get("original_predicate_uri")
            final_hsp_semantic_object = ca_processed_triple_info.get("original_object_uri_or_literal") # Default
            learned_record_metadata["ca_subject_id"] = ca_processed_triple_info.get("subject_id")
            learned_record_metadata["ca_predicate_type"] = ca_processed_triple_info.get("predicate_type")
            learned_record_metadata["ca_object_id"] = ca_processed_triple_info.get("object_id")

        if conflict_metadata_update.get("resolution_strategy") == "numerical_merge_type2":
            merged_val = conflict_metadata_update.get("merged_value") # Already a float/int
            if merged_val is not None:
                final_hsp_semantic_object = str(merged_val) # Override with string representation of merged value
                # Update fact_content_for_ham if it was based on the structured part that got merged
                if hsp_fact_payload.get('statement_type') == "semantic_triple" and \
                   isinstance(fact_content_for_ham, dict) and 'object_literal' in fact_content_for_ham:
                    fact_content_for_ham['object_literal'] = str(merged_val)

            # Update source_text to reflect merge for clarity
            # The original source_text_for_ham (which could be NL or JSON dump of original structured) is used in the note.
            learned_record_metadata["source_text"] = f"Numerically merged value for S='{learned_record_metadata.get('hsp_semantic_subject')}', P='{learned_record_metadata.get('hsp_semantic_predicate')}' is '{final_hsp_semantic_object}'. Original source text was: {source_text_for_ham}"
            # Confidence is already set to confidence_to_store which would be merged_confidence

        if final_hsp_semantic_object is not None:
             learned_record_metadata["hsp_semantic_object"] = final_hsp_semantic_object


        ham_data_type = f"hsp_learned_fact_{fact_type_from_hsp.lower().replace(' ', '_')}"
        print(f"  Storing HSP-derived fact - Type: {ham_data_type}, Content: {fact_content_for_ham}, Meta: {learned_record_metadata}")

        # Before final store, if this fact is superseding others, we might want to mark those old records in HAM.
        # This is an advanced step (updating existing records). For PoC, metadata on new fact is primary.
        # Example: self.ham_memory.update_metadata(ham_id_to_update, {"superseded_by": record_id})

        stored_id = self.ham_memory.store_experience(raw_data=fact_content_for_ham, data_type=ham_data_type, metadata=learned_record_metadata)

        if stored_id:
            print(f"  Stored HSP fact '{record_id}' (original HSP ID: '{original_hsp_fact_id}') with HAM ID '{stored_id}'")
            # ContentAnalyzerModule was already called before conflict checks that might use its output.
            # No need to call it again here unless we want it to process the potentially *merged* fact,
            # but its internal graph update was based on the original incoming fact.
            return stored_id
        else:
            print(f"  Failed to store HSP fact '{record_id}' in HAM.")
            return None

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
