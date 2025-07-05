import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

import json # Added for json.dumps in process_and_store_hsp_fact
# Assuming 'src' is in PYTHONPATH, making 'core_ai', 'shared', and 'hsp' top-level packages
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.learning.fact_extractor_module import FactExtractorModule
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule # Import ContentAnalyzerModule
from shared.types.common_types import LearnedFactRecord
from hsp.connector import HSPConnector # Import HSPConnector
from hsp.types import HSPFactPayload, HSPMessageEnvelope # Ensure HSPMessageEnvelope is imported


class LearningManager:
    def __init__(self,
                 ai_id: str,
                 ham_memory_manager: HAMMemoryManager,
                 fact_extractor: FactExtractorModule,
                 content_analyzer: Optional[ContentAnalyzerModule] = None, # Added content_analyzer
                 hsp_connector: Optional[HSPConnector] = None,
                 operational_config: Optional[Dict[str, Any]] = None):
        self.ai_id = ai_id
        self.ham_memory = ham_memory_manager
        self.fact_extractor = fact_extractor
        self.content_analyzer = content_analyzer # Store ContentAnalyzerModule instance
        self.hsp_connector = hsp_connector
        self.operational_config = operational_config or {}

        # Get thresholds from operational_config, with defaults
        learning_thresholds_config = self.operational_config.get("learning_thresholds", {})
        self.min_fact_confidence_to_store = learning_thresholds_config.get("min_fact_confidence_to_store", 0.7)
        self.min_fact_confidence_to_share_via_hsp = learning_thresholds_config.get("min_fact_confidence_to_share_via_hsp", 0.8) # New threshold
        self.default_hsp_fact_topic = self.operational_config.get("default_hsp_fact_topic", "hsp/knowledge/facts/general")

        print(f"LearningManager initialized for AI ID '{self.ai_id}'. Min fact confidence to store: {self.min_fact_confidence_to_store}, to share: {self.min_fact_confidence_to_share_via_hsp}")

    def process_and_store_learnables( # Kept synchronous for now to match HSPConnector
        self,
        text: str,
        user_id: Optional[str],
        session_id: Optional[str],
        source_interaction_ref: Optional[str]
    ) -> List[str]:
        """
        Extracts learnable facts/preferences from text and stores them as LearnedFactRecord
        in the HAMMemoryManager. (Now Asynchronous)

        Returns:
            List[str]: A list of memory IDs for the newly stored learned facts.
        """
        if not text:
            return []

        # Fact extraction itself might involve an LLM call, which could be async.
        # For now, assume fact_extractor.extract_facts() is synchronous,
        # or if it becomes async, it should be awaited here.
        # If FactExtractorModule.extract_facts becomes async:
        # extracted_fact_data_list = await self.fact_extractor.extract_facts(text, user_id)
        extracted_fact_data_list = self.fact_extractor.extract_facts(text, user_id) # Assuming sync for now

        stored_fact_ids: List[str] = []
        tasks = []

        for fact_data in extracted_fact_data_list:
            record_id = f"lfact_{uuid.uuid4().hex}" # Learned Fact ID
            timestamp = datetime.now().isoformat()

            # Construct the full LearnedFactRecord
            # fact_type, content, confidence should come from fact_data
            fact_type = fact_data.get("fact_type", "unknown_statement")
            content = fact_data.get("content", {})
            confidence = fact_data.get("confidence", 0.5) # Default confidence if not provided

            learned_record: LearnedFactRecord = { # type: ignore # Trusting structure from FactExtractor
                "record_id": record_id,
                "timestamp": timestamp,
                "user_id": user_id,
                "session_id": session_id,
                "source_interaction_ref": source_interaction_ref,
                "fact_type": fact_type,
                "content": content,
                "confidence": confidence,
                "source_text": text
            }

            # Prepare metadata for HAM store: all fields except 'content' which is the raw_data for HAM
            # HAM's store_experience expects raw_data (which will be our 'content' dict)
            # and a metadata dict.
            metadata_for_ham = {
                "record_id": learned_record["record_id"],
                "timestamp": learned_record["timestamp"],
                "user_id": learned_record["user_id"],
                "session_id": learned_record["session_id"],
                "source_interaction_ref": learned_record["source_interaction_ref"],
                "fact_type": learned_record["fact_type"], # Storing fact_type in metadata as well for querying
                "confidence": learned_record["confidence"],
                "source_text": learned_record["source_text"]
                # The actual 'content' of the fact will be the main data stored and encrypted by HAM
            }

            # The data_type for HAM could be more specific, e.g., "learned_fact_user_preference"
            ham_data_type = f"learned_fact_{fact_type.lower().replace(' ', '_')}"

            print(f"LearningManager: Storing learned fact - Type: {ham_data_type}, Content: {content}, Meta: {metadata_for_ham}")

            stored_id = self.ham_memory.store_experience(
                raw_data=content, # The 'content' dict is the core data for this memory record
                data_type=ham_data_type,
                metadata=metadata_for_ham
            )

            if stored_id:
                stored_fact_ids.append(stored_id)
                print(f"LearningManager: Stored fact '{record_id}' (HAM ID '{stored_id}')")

                # Now, potentially share this fact via HSP
                if self.hsp_connector and confidence >= self.min_fact_confidence_to_share_via_hsp:
                    hsp_fact_id = f"hspfact_{uuid.uuid4().hex}"

                    # Determine statement_type and structured content for HSP
                    # For now, let's assume fact_data["content"] is good for statement_structured
                    # and fact_data["fact_type"] can inform statement_type or tags.
                    # A more robust mapping might be needed.
                    # If content is simple key-value, it might not directly map to semantic_triple without more processing.
                    # Let's default to using content as a generic structured object for now.

                    # For statement_nl, we could use the original text, or a summary if available.
                    # For this PoC, let's use a part of the original source_text if available.
                    nl_statement_for_hsp = source_text if source_text else "Fact content: " + str(content)


                    hsp_payload = HSPFactPayload(
                        id=hsp_fact_id,
                        statement_type="natural_language", # Or determine from fact_type; default for PoC
                        statement_nl=nl_statement_for_hsp, # Could be original snippet or generated summary
                        statement_structured=content, # Use the 'content' from FactExtractor
                        source_ai_id=self.ai_id, # This AI instance is the source for HSP
                        original_source_info={ # type: ignore
                            "type": "user_utterance",
                            "identifier": user_id if user_id else "unknown_user",
                            "context_refs": {"session_id": session_id, "interaction_ref": source_interaction_ref}
                        },
                        timestamp_created=timestamp, # Use the same timestamp as LearnedFactRecord
                        timestamp_observed=timestamp, # Assuming creation and observation are close for user facts
                        confidence_score=confidence,
                        weight=1.0, # Default weight
                        tags=[fact_type] if fact_type else ["user_derived"]
                        # Other fields like valid_from/until, context, access_policy_id can be added
                    )

                    topic_to_publish = self.default_hsp_fact_topic
                    # Potentially choose topic based on fact_type or content
                    if "user_preference" in fact_type:
                        topic_to_publish = "hsp/knowledge/facts/user_preferences"
                    elif "user_statement" in fact_type:
                        topic_to_publish = "hsp/knowledge/facts/user_statements"

                    print(f"LearningManager: Publishing fact {hsp_fact_id} to HSP topic '{topic_to_publish}'")
                    self.hsp_connector.publish_fact(hsp_payload, topic=topic_to_publish)
            else:
                print(f"LearningManager: Failed to store fact '{record_id}' in HAM.")

        return stored_fact_ids

    def process_and_store_hsp_fact(
        self,
        hsp_fact_payload: HSPFactPayload,
        hsp_sender_ai_id: str,
        hsp_envelope: HSPMessageEnvelope # For context, like original message_id
    ) -> Optional[str]:
        """
        Processes a fact received via HSP and stores it in HAM if deemed appropriate.
        """
        print(f"LearningManager (AI ID: {self.ai_id}): Received HSP fact '{hsp_fact_payload.get('id')}' from '{hsp_sender_ai_id}'.")

        # Basic validation and trust (very rudimentary for PoC)
        # In a real system, hsp_sender_ai_id would be checked against a trust list/score.
        confidence = hsp_fact_payload.get('confidence_score', 0.0)
        if not isinstance(confidence, (float, int)): # Ensure confidence is a number
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                print(f"LearningManager: Invalid confidence format in HSP fact: {confidence}. Defaulting to 0.0.")
                confidence = 0.0

        # Use a specific threshold for storing facts from HSP, could be different from user-derived facts.
        # For now, let's use the existing min_fact_confidence_to_store or a dedicated one if configured.
        min_confidence_for_hsp_fact = self.operational_config.get("learning_thresholds", {}).get("min_hsp_fact_confidence_to_store", self.min_fact_confidence_to_store)

        if confidence < min_confidence_for_hsp_fact:
            print(f"LearningManager: HSP fact '{hsp_fact_payload.get('id')}' confidence {confidence} is below threshold {min_confidence_for_hsp_fact}. Not storing.")
            return None

        record_id = f"lfact_hsp_{uuid.uuid4().hex}" # Learned Fact from HSP ID
        timestamp = datetime.now().isoformat()

        # Derive LearnedFactRecord components from HSPFactPayload
        # statement_nl or statement_structured will form the core content.
        # For HAM, we need to decide what the 'raw_data' (content) is vs metadata.

        fact_content_for_ham: Any
        source_text_for_ham: str

        if hsp_fact_payload.get('statement_structured'):
            fact_content_for_ham = hsp_fact_payload['statement_structured']
            source_text_for_ham = hsp_fact_payload.get('statement_nl', json.dumps(fact_content_for_ham)) # Use NL if available, else serialize structured
        elif hsp_fact_payload.get('statement_nl'):
            fact_content_for_ham = {"text": hsp_fact_payload['statement_nl']} # Wrap NL in a simple dict for content
            source_text_for_ham = hsp_fact_payload['statement_nl']
        else:
            print(f"LearningManager: HSP fact '{hsp_fact_payload.get('id')}' has no statement_structured or statement_nl. Cannot process.")
            return None

        fact_type_from_hsp = "hsp_derived_fact" # Default
        if hsp_fact_payload.get('tags') and len(hsp_fact_payload['tags']) > 0: # type: ignore
            fact_type_from_hsp = hsp_fact_payload['tags'][0] # Use first tag as fact_type for simplicity # type: ignore

        learned_record_metadata = {
            "record_id": record_id,
            "timestamp": timestamp,
            "user_id": None, # Not directly from a user of this AI instance
            "session_id": None, # Not directly from a session of this AI instance
            "source_interaction_ref": hsp_envelope.get('message_id'), # Link to the HSP message
            "fact_type": fact_type_from_hsp,
            "confidence": confidence,
            "source_text": source_text_for_ham, # The textual representation of the fact
            "hsp_originator_ai_id": hsp_fact_payload.get('source_ai_id'), # The AI that originally created the fact
            "hsp_sender_ai_id": hsp_sender_ai_id, # The AI that sent this HSP message
            "hsp_fact_id": hsp_fact_payload.get('id') # Original ID of the fact from HSP network
        }

        ham_data_type = f"hsp_learned_fact_{fact_type_from_hsp.lower().replace(' ', '_')}"

        print(f"LearningManager: Storing HSP-derived fact - Type: {ham_data_type}, Content: {fact_content_for_ham}, Meta: {learned_record_metadata}")

        stored_id = self.ham_memory.store_experience(
            raw_data=fact_content_for_ham,
            data_type=ham_data_type,
            metadata=learned_record_metadata
        )

        if stored_id:
            print(f"LearningManager: Stored HSP fact '{record_id}' (original HSP ID: {hsp_fact_payload.get('id')}) with HAM ID '{stored_id}'")

            # Now, if ContentAnalyzer is available, pass the fact content for deeper analysis / KG integration
            if self.content_analyzer:
                # We pass the original hsp_fact_payload as it contains statement_type, statement_nl, statement_structured
                # and the source_ai_id (hsp_sender_ai_id) for context.
                try:
                    print(f"LearningManager: Passing HSP fact content (ID: {hsp_fact_payload.get('id')}) to ContentAnalyzerModule.")
                    analysis_updated_graph = self.content_analyzer.process_hsp_fact_content(
                        hsp_fact_payload=hsp_fact_payload, # type: ignore # TypedDict should be compatible
                        source_ai_id=hsp_sender_ai_id
                    )
                    if analysis_updated_graph:
                        print(f"LearningManager: ContentAnalyzerModule reported graph updates for HSP fact '{hsp_fact_payload.get('id')}'.")
                    else:
                        print(f"LearningManager: ContentAnalyzerModule did not report graph updates for HSP fact '{hsp_fact_payload.get('id')}'.")
                except Exception as e:
                    print(f"LearningManager: Error calling ContentAnalyzerModule for HSP fact '{hsp_fact_payload.get('id')}': {e}")
            return stored_id
        else:
            print(f"LearningManager: Failed to store HSP fact '{record_id}' in HAM.")
            return None


if __name__ == '__main__':
    print("--- LearningManager Standalone Test ---")

    # Mock HAMMemoryManager
    class MockHAMMemoryManager:
        def __init__(self):
            self.stored_experiences: Dict[str, Dict[str, Any]] = {}
            self.next_id = 1
            print("MockHAMMemoryManager initialized.")

        def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
            mem_id = f"mock_ham_mem_{self.next_id}"
            self.next_id += 1
            self.stored_experiences[mem_id] = {
                "raw_data": raw_data,
                "data_type": data_type,
                "metadata": metadata or {}
            }
            print(f"MockHAM: Stored '{data_type}' with ID {mem_id}, Data: {raw_data}, Meta: {metadata}")
            return mem_id

    # Use PatchedLLMInterface from FactExtractorModule for testing
    # This requires careful pathing or redefinition if FactExtractorModule is in the same directory
    # For now, assume we can import it or we redefine a similar patch here.
    try:
        # Attempt to use the one from fact_extractor_module if it's runnable standalone
        from .fact_extractor_module import PatchedLLMInterfaceForFactExtraction # type: ignore
        print("Using PatchedLLMInterfaceForFactExtraction from sibling module.")
    except ImportError:
        print("Could not import PatchedLLMInterfaceForFactExtraction, defining a local one for LearningManager test.")
        from services.llm_interface import LLMInterface, LLMInterfaceConfig # type: ignore
        class PatchedLLMInterfaceForFactExtraction(LLMInterface): # type: ignore
             def _get_mock_response(self, prompt: str, model_name: Optional[str]) -> str:
                if "extract any clear statements of preference" in prompt:
                    if "My favorite color is green" in prompt and "I work as a baker" in prompt:
                        return json.dumps([
                            {"fact_type": "user_preference", "content": {"category": "color", "preference": "green"}, "confidence": 0.95},
                            {"fact_type": "user_statement", "content": {"attribute": "occupation", "value": "baker"}, "confidence": 0.9}
                        ])
                    elif "I like apples" in prompt:
                        return json.dumps([
                            {"fact_type": "user_preference", "content": {"category": "food", "preference": "apples", "liked": True}, "confidence": 0.88}
                        ])
                return json.dumps([])


    mock_llm_config: LLMInterfaceConfig = { #type: ignore
        "default_provider": "mock", "default_model": "test-fact-extract",
        "providers": {}, "default_generation_params": {}
    }
    patched_llm_for_facts = PatchedLLMInterfaceForFactExtraction(config=mock_llm_config)

    mock_ham = MockHAMMemoryManager()
    fact_extractor = FactExtractorModule(llm_interface=patched_llm_for_facts)

    # Mock HSPConnector
    class MockHSPConnector:
        def __init__(self, ai_id: str, broker_address: str, broker_port: int):
            self.ai_id = ai_id
            self.broker_address = broker_address
            self.broker_port = broker_port
            self.published_facts: List[Dict[str, Any]] = []
            print(f"MockHSPConnector initialized for AI ID '{ai_id}'")

        def publish_fact(self, fact_payload: HSPFactPayload, topic: str) -> bool:
            print(f"MockHSPConnector: 'publish_fact' called for topic '{topic}'. Payload: {fact_payload.get('id')}")
            self.published_facts.append({"payload": fact_payload, "topic": topic})
            return True

        def connect(self) -> bool: return True # Mock connect
        def disconnect(self): pass # Mock disconnect

    mock_hsp_connector = MockHSPConnector(ai_id="test_ai_lm", broker_address="dummy", broker_port=1883)

    # Update LearningManager instantiation
    learning_manager_config = {
        "learning_thresholds": {
            "min_fact_confidence_to_store": 0.7,
            "min_fact_confidence_to_share_via_hsp": 0.85 # Set a threshold for testing sharing
        },
        "default_hsp_fact_topic": "hsp/knowledge/facts/test_general"
    }
    learning_manager = LearningManager(
        ai_id="test_ai_lm", # Provide an AI ID
        ham_memory_manager=mock_ham,
        fact_extractor=fact_extractor,
        hsp_connector=mock_hsp_connector, # Pass the mock connector
        operational_config=learning_manager_config
    )

    test_inputs = [
        ("My favorite color is green and I work as a baker.", "user123", "sessionABC", "mem_dialogue_001"), # Both facts should be shared (conf 0.95, 0.9)
        ("I like apples.", "user123", "sessionABC", "mem_dialogue_002"),
        ("The weather is nice today.", "user456", "sessionXYZ", "mem_dialogue_003") # Should extract no facts
    ]

    for text, user, session, source_ref in test_inputs:
        print(f"\nProcessing LM input: '{text}' for user '{user}'")
        stored_ids = learning_manager.process_and_store_learnables(text, user, session, source_ref)
        if stored_ids:
            print(f"  Stored Fact HAM IDs: {stored_ids}")
            for fact_id in stored_ids:
                if fact_id in mock_ham.stored_experiences:
                    print(f"    HAM Content for {fact_id}: {mock_ham.stored_experiences[fact_id]}")
                else:
                    print(f"    ERROR: HAM ID {fact_id} not found in mock_ham.stored_experiences")

        else:
            print("  No facts stored.")

    # Verify storage
    print(f"\nTotal experiences in MockHAM: {len(mock_ham.stored_experiences)}")
    assert len(mock_ham.stored_experiences) == 3 # 2 from first input, 1 from second

    # Check one stored item's metadata
    example_stored_id = learning_manager.process_and_store_learnables(
        "My cat is named Whiskers.", "user789", "sessionDEF", "mem_dialogue_004"
    ) # Assuming LLM mock would be updated to catch this or returns empty for now
    # This part of the test will depend on how the PatchedLLM handles this new input.
    # If it returns empty, this assertion might need adjustment or the patch needs more rules.
    # For now, we're mostly testing the flow.

    print("\n--- Verifying HSP Publishing ---")
    # Expected:
    # 1st input: "My favorite color is green and I work as a baker."
    #   - Fact 1 (color green, conf 0.95) -> should be shared (0.95 >= 0.85)
    #   - Fact 2 (occupation baker, conf 0.9) -> should be shared (0.9 >= 0.85)
    # 2nd input: "I like apples."
    #   - Fact 3 (likes apples, conf 0.88) -> should be shared (0.88 >= 0.85)
    # 3rd input: "The weather is nice today." -> no facts extracted, so none shared.

    expected_shared_facts_count = 3
    actual_shared_facts_count = len(mock_hsp_connector.published_facts)
    print(f"Expected shared facts via HSP: {expected_shared_facts_count}")
    print(f"Actual shared facts via HSP  : {actual_shared_facts_count}")

    assert actual_shared_facts_count == expected_shared_facts_count, \
        f"Test Failed: Expected {expected_shared_facts_count} facts to be shared via HSP, but got {actual_shared_facts_count}"

    if actual_shared_facts_count > 0:
        first_shared_fact = mock_hsp_connector.published_facts[0]
        print(f"First shared fact payload ID: {first_shared_fact['payload'].get('id')}")
        print(f"First shared fact topic: {first_shared_fact['topic']}")
        assert first_shared_fact['payload']['source_ai_id'] == "test_ai_lm"
        assert first_shared_fact['payload']['confidence_score'] >= learning_manager.min_fact_confidence_to_share_via_hsp

        # Check topics for the first two (color and occupation)
        # Assuming they are published in order of extraction by FactExtractor's mock
        if actual_shared_facts_count >= 2:
             # Fact 1 (color green, type user_preference)
            assert mock_hsp_connector.published_facts[0]['topic'] == "hsp/knowledge/facts/user_preferences"
            # Fact 2 (occupation baker, type user_statement)
            assert mock_hsp_connector.published_facts[1]['topic'] == "hsp/knowledge/facts/user_statements"
            # Fact 3 (likes apples, type user_preference)
            assert mock_hsp_connector.published_facts[2]['topic'] == "hsp/knowledge/facts/user_preferences"


    print("\nLearningManager standalone test finished.")
