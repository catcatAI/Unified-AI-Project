import logging
import json
import asyncio
from typing import List, Dict, Optional, Any
from src.core.services.multi_llm_service import MultiLLMService, ChatMessage
from .types import ExtractedFact

logger = logging.getLogger(__name__)

class FactExtractorModule:
    """
    事实提取模块 - 使用LLM从文本中提取事实和偏好
    """

    def __init__(self, 
                 llm_service: MultiLLMService, 
                 model_id: str = "gpt-3.5-turbo", 
                 model_params: Optional[Dict[str, Any]] = None) -> None:
        self.llm_service = llm_service
        self.model_id = model_id
        self.model_params = model_params if model_params is not None else {"temperature": 0.3}
        logger.info(f"FactExtractorModule initialized with model_id: {self.model_id}")

    def _construct_fact_extraction_prompt(self, text: str, user_id: Optional[str] = None) -> str:
        prompt = "You are an expert at identifying simple facts and preferences stated by a user in their message.\n"
        prompt += "Analyze the following user message and extract any clear statements of preference (likes, dislikes, favorites) or factual assertions the user makes about themselves (e.g., their name, occupation, location, possessions, etc.).\n\n"
        prompt += f"User Message: \"{text}\"\n\n"
        prompt += "Respond in JSON format with a list of extracted facts. Each fact in the list should be an object with the following structure:\n"
        prompt += "{\n"
        prompt += '  "fact_type": "user_preference" OR "user_statement",\n'
        prompt += '  "content": { <structured_key_value_pairs> },\n'
        prompt += '  "confidence": <float 0.0 to 1.0>\n'
        prompt += "}\n"
        prompt += "Examples for 'content':\n"
        prompt += "- For 'user_preference': {\"category\": \"color\", \"preference\": \"blue\", \"liked\": true}\n"
        prompt += "- For 'user_statement': {\"attribute\": \"name\", \"value\": \"Alex\"}\n"
        prompt += "If no clear facts are found, return an empty list [].\n"
        return prompt

    async def extract_facts(self, text: str, user_id: Optional[str] = None) -> List[ExtractedFact]:
        """
        Uses an LLM to extract a list of facts/preferences from the user's text.
        """
        if not self.llm_service:
            logger.error("LLM Service not available. Cannot extract facts.")
            return []

        prompt = self._construct_fact_extraction_prompt(text, user_id)
        messages = [ChatMessage(role="user", content=prompt)]

        try:
            llm_response = await self.llm_service.chat_completion(
                messages=messages,
                model_id=self.model_id,
                **self.model_params
            )
            
            if not llm_response or not llm_response.content:
                logger.warning("Empty response from LLM during fact extraction.")
                return []

            llm_response_str = llm_response.content.strip()
            # Try to find JSON block if LLM added preamble
            if "```json" in llm_response_str:
                llm_response_str = llm_response_str.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response_str:
                 llm_response_str = llm_response_str.split("```")[1].split("```")[0].strip()

            try:
                extracted_data = json.loads(llm_response_str)
                if not isinstance(extracted_data, list):
                    logger.error(f"LLM response is not a list: {llm_response_str}")
                    return []

                valid_facts: List[ExtractedFact] = []
                for item in extracted_data:
                    if isinstance(item, dict) and "fact_type" in item and "content" in item:
                        item["confidence"] = float(item.get("confidence", 1.0))
                        valid_facts.append(item)
                
                logger.info(f"Successfully extracted {len(valid_facts)} facts.")
                return valid_facts

            except json.JSONDecodeError:
                logger.error(f"Could not decode JSON from LLM: {llm_response_str}")
                return []

        except Exception as e:
            logger.error(f"Error during LLM fact extraction: {e}")
            return []

if __name__ == "__main__":
    # Quick standalone test
    class MockLLM:
        async def chat_completion(self, messages, model_id, **kwargs):
            from collections import namedtuple
            Response = namedtuple("Response", ["content"])
            return Response(content='[{"fact_type": "user_preference", "content": {"category": "color", "preference": "green"}, "confidence": 0.9}]')

    async def test():
        extractor = FactExtractorModule(MockLLM())
        facts = await extractor.extract_facts("My favorite color is green.")
        print(f"Extracted facts: {facts}")

    asyncio.run(test())