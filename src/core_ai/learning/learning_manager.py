import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

# Assuming 'src' is in PYTHONPATH, making 'core_ai' and 'shared' top-level packages
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.learning.fact_extractor_module import FactExtractorModule
from shared.types.common_types import LearnedFactRecord


class LearningManager:
    def __init__(self,
                 ham_memory_manager: HAMMemoryManager,
                 fact_extractor: FactExtractorModule,
                 operational_config: Optional[Dict[str, Any]] = None):
        self.ham_memory = ham_memory_manager
        self.fact_extractor = fact_extractor
        self.operational_config = operational_config or {}

        # Get thresholds from operational_config, with defaults
        learning_thresholds_config = self.operational_config.get("learning_thresholds", {})
        self.min_fact_confidence_to_store = learning_thresholds_config.get("min_fact_confidence_to_store", 0.7)

        print(f"LearningManager initialized. Min fact confidence to store: {self.min_fact_confidence_to_store}")

    async def process_and_store_learnables( # Made async
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
                print(f"LearningManager: Stored fact '{record_id}' with HAM ID '{stored_id}'")
            else:
                print(f"LearningManager: Failed to store fact '{record_id}' in HAM.")

        return stored_fact_ids

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

    learning_manager = LearningManager(ham_memory_manager=mock_ham, fact_extractor=fact_extractor)

    test_inputs = [
        ("My favorite color is green and I work as a baker.", "user123", "sessionABC", "mem_dialogue_001"),
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

    print("\nLearningManager standalone test finished.")
