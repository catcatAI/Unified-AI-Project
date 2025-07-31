import json
from typing import List, Dict, Optional, Any

# Assuming 'src' is in PYTHONPATH, making 'services' a top-level package
from services.multi_llm_service import MultiLLMService, ChatMessage
from shared.types.common_types import ExtractedFact # Import the new type
# LearnedFactRecord content is what this module aims to extract, but the full record is assembled by LearningManager


class FactExtractorModule:
    def __init__(self, llm_service: MultiLLMService):
        self.llm_service = llm_service
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
        if not self.llm_service:
            print("FactExtractorModule: LLM Service not available. Cannot extract facts.")
            return []

        prompt = self._construct_fact_extraction_prompt(text, user_id)

        print(f"FactExtractorModule: Sending prompt to LLM for fact extraction:\n---\n{prompt}\n---")

        # MultiLLMService expects a list of ChatMessage objects
        messages = [ChatMessage(role="user", content=prompt)]

        llm_response = await self.llm_service.chat_completion(
            messages,
            model_id="fact_extraction_model_placeholder"
            # params={"temperature": 0.3} # Lower temperature for more factual output
        )
        llm_response_str = llm_response.content

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
    import asyncio
    from services.multi_llm_service import MultiLLMService, ModelConfig, ModelProvider

    async def main_test():
        print("--- FactExtractorModule Standalone Test ---")

        # Patched MultiLLMService for testing fact extraction
        class PatchedMultiLLMServiceForFactExtraction(MultiLLMService):
            async def chat_completion(self, messages: List[ChatMessage], model_id: Optional[str] = None, **kwargs) -> LLMResponse:
                prompt = messages[0].content # Assuming single user message for prompt
                if "extract any clear statements of preference" in prompt: # Identifying fact extraction prompt
                    if "My favorite color is green" in prompt and "I work as a baker" in prompt:
                        return LLMResponse(
                            content=json.dumps([
                                {"fact_type": "user_preference", "content": {"category": "color", "preference": "green"}, "confidence": 0.95},
                                {"fact_type": "user_statement", "content": {"attribute": "occupation", "value": "baker"}, "confidence": 0.9}
                            ]),
                            model="fact-extract-mock-v1", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                        )
                    elif "I like apples" in prompt:
                        return LLMResponse(
                            content=json.dumps([
                                {"fact_type": "user_preference", "content": {"category": "food", "preference": "apples", "liked": True}, "confidence": 0.88}
                            ]),
                            model="fact-extract-mock-v1", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                        )
                    elif "My name is Sarah" in prompt:
                        return LLMResponse(
                            content=json.dumps([
                                {"fact_type": "user_statement", "content": {"attribute": "name", "value": "Sarah"}, "confidence": 1.0}
                            ]),
                            model="fact-extract-mock-v1", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                        )
                    elif "Just a normal chat" in prompt: # No facts
                        return LLMResponse(
                            content=json.dumps([]),
                            model="fact-extract-mock-v1", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                        )
                    else: # Default if no specific rule matches
                        print(f"PatchedMultiLLMServiceForFactExtraction: No specific mock rule for prompt: {prompt[:150]}...")
                        return LLMResponse(
                            content=json.dumps([]),
                            model="fact-extract-mock-v1", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                        )
                # Fallback for other prompts if needed, though this mock is specific to fact extraction
                return LLMResponse(
                    content="Mock response for unhandled prompt.",
                    model="mock-default", provider=ModelProvider.GOOGLE, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now(), metadata={}
                )

        # Initialize with a dummy config, as the mock service overrides chat_completion
        mock_llm_service = PatchedMultiLLMServiceForFactExtraction(config_path=None) 

        fact_extractor = FactExtractorModule(llm_service=mock_llm_service)

        test_queries = [
            "My favorite color is green and I work as a baker.",
            "I like apples.",
            "My name is Sarah.",
            "Just a normal chat, nothing special.",
            "The sky is blue today." # Should not extract as user preference/statement
        ]

        for query in test_queries:
            print(f"\nProcessing query: \"{query}\"")
            facts = await fact_extractor.extract_facts(query, user_id="test_user")
            if facts:
                for fact in facts:
                    print(f"  Extracted Fact: {fact}")
            else:
                print("  No facts extracted.")

        print("\nFactExtractorModule standalone test finished.")

    asyncio.run(main_test())
