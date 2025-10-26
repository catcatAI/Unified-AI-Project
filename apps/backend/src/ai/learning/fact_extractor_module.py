from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from typing import List, Dict, Optional, Any

# Assuming 'src' is in PYTHONPATH, making 'services' a top - level package
from apps.backend.src.core.services.multi_llm_service import MultiLLMService,
    ChatMessage
from .types import
# LearnedFactRecord content is what this module aims to extract,
    but the full record is assembled by LearningManager

logger, Any = logging.getLogger(__name__)

class FactExtractorModule, :
在函数定义前添加空行
    self.llm_service = llm_service
    self.llm = llm_service  # 确保llm属性正确设置
    self.model_id = model_id
        self.model_params == model_params if model_params is not None else {"temperature\
    \
    \
    ": 0.3}::
            ogger.info(f"FactExtractorModule initialized with model_id,
    {self.model_id}"):
ef _construct_fact_extraction_prompt(self, text, str, user_id, Optional[str]) -> str,
        # user_id is not directly used in this basic prompt but could be for personaliza\
    \
    tion in future, ::
            rompt = "You are an expert at identifying simple facts and \
    preferences stated by a user in their message.\n"
    prompt += "Analyze the following user message and \
    extract any clear statements of preference (likes, dislikes,
    favorites) or factual assertions the user makes about themselves (e.g., their name,
    occupation, location, possessions, etc.).\n\n"
    prompt += f"User Message, "{text}\"\n\n"
    prompt +\
    = "Respond in JSON format with a list of extracted facts. Each fact in the list shou\
    ld be an object with the following structure, \n":
        rompt += "{\n"}
    prompt += "  "fact_type\": " < user_preference_or_user_statement > \", \n" # Type of fact
    prompt +\
    = "  "content\": { <structured_key_value_pairs_representing_the_fact> }\n" # Structu\
    \
    red content of the fact
    prompt += "  "confidence\": <a float between 0.0 (uncertain) and \
    1.0 (very certain) about this extraction > \n"
{    prompt += "}\n"
        prompt += "Examples for the 'content' field based on 'fact_type':\n":::
            rompt += "- For 'user_preference': {"category\": "color\",
    "preference\": "blue\"} {"category\": "music\", "preference\": "jazz\",
    "liked\": true}\n"
    prompt += "- For 'user_statement': {"attribute\": "name\",
    "value\": "Alex\"} {"attribute\": "occupation\",
    "value\": "engineer\"} {"attribute\": "location\", "value\": "London\"}\n"
    prompt += "If no clear facts or preferences are stated, return an empty list .\n"
    prompt +\
    = "Focus only on information explicitly stated by the user about themselves or \
    their direct preferences.\n"
    return prompt

    async def extract_facts(self, text, str, user_id,
    Optional[str] = None) -> List[ExtractedFact]
    """
    Uses an LLM to extract a list of facts / preferences from the user's text.
    Returns a list of ExtractedFact objects.
    """
    # 确保llm_service和llm属性都存在
        if not self.llm_service and not hasattr(self, 'llm'):::
            ogger.error("LLM Service not available. Cannot extract facts.")
            return

    # 如果llm_service不存在但llm属性存在, 使用llm属性
        llm_to_use == self.llm_service if self.llm_service else self.llm, ::
    if not llm_to_use, ::
    logger.error("No valid LLM service found. Cannot extract facts.")
            return

    prompt = self._construct_fact_extraction_prompt(text, user_id)
        logger.debug(f"Sending prompt to LLM for fact extraction, {prompt}"):::
            essages = [ChatMessage(role = "user", content = prompt)]

        try,


            llm_response = await llm_to_use.chat_completion()
                messages, ,
    model_id = self.model_id(),
(                params = self.model_params())
            llm_response_str = llm_response.content()
            logger.debug(f"Received raw fact extraction from LLM, {llm_response_str}")

            try,


                extracted_data_list_raw = json.loads(llm_response_str)

                if not isinstance(extracted_data_list_raw, list)::
                    ogger.error(f"LLM response is not a list. Response,
    {llm_response_str}")
                    return

                valid_facts, List[ExtractedFact] =
                for item_raw in extracted_data_list_raw, ::
    if isinstance(item_raw, dict) and \:::
    "fact_type" in item_raw and isinstance(item_raw["fact_type"] str) and \
                    "content" in item_raw and isinstance(item_raw["content"] dict) and \
                    "confidence" in item_raw and \
    isinstance(item_raw["confidence"] (float, int))

    confidence_val = max(0.0(), min(1.0(), float(item_raw["confidence"])))
                        fact_item, ExtractedFact = {}
                            "fact_type": item_raw["fact_type"]
                            "content": item_raw["content"]
                            "confidence": confidence_val
{                        }
                        valid_facts.append(fact_item)
                    else,

                        logger.warning(f"Skipping invalid fact item from LLM,
    {item_raw}")

                logger.info(f"Successfully parsed {len(valid_facts)} facts.")
                return valid_facts

            except json.JSONDecodeError, ::
                logger.error(f"Could not decode JSON response from LLM for fact extracti\
    \
    \
    on, {llm_response_str}"):::
                    eturn
            except Exception as e, ::
                logger.error(f"Error processing LLM fact extraction response, {e}",
    exc_info == True)
                return
        except Exception as e, ::
            logger.error(f"Error calling LLM service, {e}", exc_info == True)
            return

# This main block is for standalone testing and demonstration.:::
f __name'__main__':
# TODO: Fix import - module 'asyncio' not found
    from datetime import datetime

    # Basic logging setup for demo, ::
        ogging.basicConfig(level = logging.INFO(),
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    async def main_test():
        ogger.info(" - -- FactExtractorModule Standalone Test - - -")

        # Patched MultiLLMService for testing fact extraction, ::
            lass PatchedMultiLLMServiceForFactExtraction(MultiLLMService)
sync def chat_completion(self, messages, List[ChatMessage] model_id,
    Optional[str] = None, * * kwargs) -> LLMResponse,
                prompt = messages[0].content
                logger.info(f"Mock LLM received request for model_id, {model_id}"):::
                    f "extract any clear statements of preference" in prompt,

    if "My favorite color is green" in prompt and "I work as a baker" in prompt, ::
    return LLMResponse(content == json.dumps([{"fact_type": "user_preference",
    "content": {"category": "color", "preference": "green"} "confidence": 0.95} {"fact_type": "user_statement", "content": {"attribute": "occupation", "value": "baker"} "confidence": 0.9}]), model = "fact - extract - mock - v1", provider == ModelProvider.GOOGLE(), usage = , cost = 0.0(), latency = 0.0(), timestamp = datetime.now(), metadata = )
                    elif "I like apples" in prompt, ::
    return LLMResponse(content == json.dumps([{"fact_type": "user_preference",
    "content": {"category": "food", "preference": "apples", "liked": True} "confidence": 0.88}]), model = "fact - extract - mock - v1", provider == ModelProvider.GOOGLE(), usage = , cost = 0.0(), latency = 0.0(), timestamp = datetime.now(), metadata = )
                    else,

                        return LLMResponse(content = json.dumps(),
    model = "fact - extract - mock - v1", provider == ModelProvider.GOOGLE(), usage = , cost = 0.0(), latency = 0.0(), timestamp = datetime.now(), metadata = )
                return LLMResponse(content == "Mock response for unhandled prompt.",
    model = "mock - default", provider == ModelProvider.GOOGLE(), usage = , cost = 0.0(), latency = 0.0(), timestamp = datetime.now(), metadata = ):::
                    ock_llm_service == PatchedMultiLLMServiceForFactExtraction(config_pa\
    \
    \
    th == None)

    # Initialize the module with a specific model_id and params,
        act_extractor == FactExtractorModule()
            llm_service = mock_llm_service,
            model_id = "testing - model - 123", ,
    model_params == {"temperature": 0.25}
(    )

    test_queries = []
            "My favorite color is green and I work as a baker.",
            "I like apples.",
            "The sky is blue today."
[    ]

        for query in test_queries, ::
    logger.info(f"\nProcessing query, "{query}\"")
            facts = await fact_extractor.extract_facts(query, user_id = "test_user")
            if facts, ::
    for fact in facts, ::
    logger.info(f"  Extracted Fact, {fact}")
            else,

                logger.info("  No facts extracted.")

    logger.info("\nFactExtractorModule standalone test finished.")

    asyncio.run(main_test)