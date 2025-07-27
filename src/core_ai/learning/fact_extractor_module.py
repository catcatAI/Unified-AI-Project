import json
from typing import List, Dict, Optional, Any

# Assuming 'src' is in PYTHONPATH, making 'services' a top-level package
from services.llm_interface import LLMInterface, LLMInterfaceConfig
from shared.types.common_types import ExtractedFact # Import the new type
# LearnedFactRecord content is what this module aims to extract, but the full record is assembled by LearningManager


class FactExtractorModule:
    def __init__(self, llm_interface: LLMInterface):
        self.llm_interface = llm_interface
        print("FactExtractorModule initialized.")

    def _construct_fact_extraction_prompt(self, text: str, user_id: Optional[str]) -> str:
        # user_id is not directly used in this basic prompt but could be for personalization in future
        prompt = "You are an expert at identifying simple facts and preferences stated by a user in their message.\n"
        prompt += "Analyze the following user message and extract any clear statements of preference (likes, dislikes, favorites) or factual assertions the user makes about themselves (e.g., their name, occupation, location, possessions, etc.).\n\n"
        prompt += f"User Message: \"{text}\"\n\n"
        prompt += "Respond in JSON format with a list of extracted facts. Each fact in the list should be an object with the following structure:\n"
        prompt += "{\n"
        prompt += "  \"fact_type\": \"<user_preference_or_user_statement>\",\n" # Type of fact
        prompt += "  \"content\": { <structured_key_value_pairs_representing_the_fact> },\n" # Structured content of the fact
        prompt += "  \"confidence\": <a float between 0.0 (uncertain) and 1.0 (very certain) about this extraction>\n"
        prompt += "}\n"
        prompt += "Examples for the 'content' field based on 'fact_type':\n"
        prompt += "- For 'user_preference': {\"category\": \"color\", \"preference\": \"blue\"}, {\"category\": \"music\", \"preference\": \"jazz\", \"liked\": true}\n"
        prompt += "- For 'user_statement': {\"attribute\": \"name\", \"value\": \"Alex\"}, {\"attribute\": \"occupation\", \"value\": \"engineer\"}, {\"attribute\": \"location\", \"value\": \"London\"}\n"
        prompt += "If no clear facts or preferences are stated, return an empty list [].\n"
        prompt += "Focus only on information explicitly stated by the user about themselves or their direct preferences.\n"
        return prompt

    async def extract_facts(self, text: str, user_id: Optional[str] = None) -> List[ExtractedFact]:
        """
        Uses an LLM to extract a list of facts/preferences from the user's text.
        Returns a list of ExtractedFact objects.
        """
        if not self.llm_interface:
            print("FactExtractorModule: LLMInterface not available. Cannot extract facts.")
            return []

        prompt = self._construct_fact_extraction_prompt(text, user_id)

        print(f"FactExtractorModule: Sending prompt to LLM for fact extraction:\n---\n{prompt}\n---")

        # Suggesting a specific model or parameters might be useful for fact extraction
        llm_response_str = await self.llm_interface.generate_response(
            prompt,
            model_name="fact_extraction_model_placeholder"
            # params={"temperature": 0.3} # Lower temperature for more factual output
        )

        print(f"FactExtractorModule: Received raw fact extraction from LLM:\n---\n{llm_response_str}\n---")

        try:
            # The LLM is expected to return a string that is a JSON list of fact objects
            extracted_data_list_raw = json.loads(llm_response_str)

            if not isinstance(extracted_data_list_raw, list):
                print(f"FactExtractorModule: Error - LLM response is not a list. Response: {llm_response_str}")
                return []

            valid_facts: List[ExtractedFact] = []
            for item_raw in extracted_data_list_raw:
                if isinstance(item_raw, dict) and \
                   "fact_type" in item_raw and isinstance(item_raw["fact_type"], str) and \
                   "content" in item_raw and isinstance(item_raw["content"], dict) and \
                   "confidence" in item_raw and isinstance(item_raw["confidence"], (float, int)):

                    # Normalize confidence
                    confidence_val = max(0.0, min(1.0, float(item_raw["confidence"])))

                    # Create an ExtractedFact TypedDict.
                    # The 'content' field's specific type (Preference or Statement) isn't strictly validated here beyond being a dict.
                    # The consumer (LearningManager) would handle it based on fact_type.
                    fact_item: ExtractedFact = { # type: ignore # content can be more specific
                        "fact_type": item_raw["fact_type"],
                        "content": item_raw["content"], # This is ExtractedFactContent union
                        "confidence": confidence_val
                    }
                    valid_facts.append(fact_item)
                else:
                    print(f"FactExtractorModule: Warning - Skipping invalid fact item from LLM: {item_raw}")

            print(f"FactExtractorModule: Parsed facts: {valid_facts}")
            return valid_facts

        except json.JSONDecodeError:
            print(f"FactExtractorModule: Error - Could not decode JSON response from LLM for fact extraction: {llm_response_str}")
            return []
        except Exception as e:
            print(f"FactExtractorModule: Error processing LLM fact extraction response: {e}")
            return []

if __name__ == '__main__':
    print("--- FactExtractorModule Standalone Test ---")

    # Patched LLMInterface for testing fact extraction
    class PatchedLLMInterfaceForFactExtraction(LLMInterface):
        def _get_mock_response(self, prompt: str, model_name: Optional[str]) -> str:
            if "extract any clear statements of preference" in prompt: # Identifying fact extraction prompt
                if "My favorite color is green" in prompt and "I work as a baker" in prompt:
                    return json.dumps([
                        {"fact_type": "user_preference", "content": {"category": "color", "preference": "green"}, "confidence": 0.95},
                        {"fact_type": "user_statement", "content": {"attribute": "occupation", "value": "baker"}, "confidence": 0.9}
                    ])
                elif "I like apples" in prompt:
                    return json.dumps([
                        {"fact_type": "user_preference", "content": {"category": "food", "preference": "apples", "liked": True}, "confidence": 0.88}
                    ])
                elif "My name is Sarah" in prompt:
                     return json.dumps([
                        {"fact_type": "user_statement", "content": {"attribute": "name", "value": "Sarah"}, "confidence": 1.0}
                    ])
                elif "Just a normal chat" in prompt: # No facts
                    return json.dumps([])
                else: # Default if no specific rule matches
                    print(f"PatchedLLMInterfaceForFactExtraction: No specific mock rule for prompt: {prompt[:150]}...")
                    return json.dumps([])
            return super()._get_mock_response(prompt, model_name) # Fallback for other prompts

    mock_llm_config_for_facts: LLMInterfaceConfig = { #type: ignore
        "default_provider": "mock", "default_model": "fact-extract-mock-v1",
        "providers": {}, "default_generation_params": {}
    }
    patched_llm = PatchedLLMInterfaceForFactExtraction(config=mock_llm_config_for_facts)

    fact_extractor = FactExtractorModule(llm_interface=patched_llm)

    test_queries = [
        "My favorite color is green and I work as a baker.",
        "I like apples.",
        "My name is Sarah.",
        "Just a normal chat, nothing special.",
        "The sky is blue today." # Should not extract as user preference/statement
    ]

    for query in test_queries:
        print(f"\nProcessing query: \"{query}\"")
        facts = fact_extractor.extract_facts(query, user_id="test_user")
        if facts:
            for fact in facts:
                print(f"  Extracted Fact: {fact}")
        else:
            print("  No facts extracted.")

    print("\nFactExtractorModule standalone test finished.")
