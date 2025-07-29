import unittest
import pytest
import os
import sys
from unittest.mock import AsyncMock # Added for AsyncMock

import json
from src.core_ai.language_models.daily_language_model import DailyLanguageModel
from src.services.multi_llm_service import LLMResponse, ModelProvider, ChatMessage
from datetime import datetime

class TestDailyLanguageModel:

    @pytest.fixture(autouse=True)
    def setup_dlm(self):
        # Create a mock for MultiLLMService
        mock_llm_service = AsyncMock(spec=MultiLLMService)

        # Define the behavior of the mocked chat_completion
        async def mock_chat_completion_behavior(messages, model_id=None, **kwargs):
            prompt = messages[0].content # Assuming single user message for prompt
            if "calculate" in prompt.lower() and "User Query: \"calculate 2 + 2\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "calculate", "parameters": {"query": "2 + 2", "original_query": "calculate 2 + 2"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "calculate" in prompt.lower() and "User Query: \"what is 10 * 5\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "calculate", "parameters": {"query": "10 * 5", "original_query": "what is 10 * 5"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "calculate" in prompt.lower() and "User Query: \"compute 100 / 20\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "calculate", "parameters": {"query": "100 / 20", "original_query": "compute 100 / 20"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "calculate" in prompt.lower() and "User Query: \"solve for 7 - 3\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "calculate", "parameters": {"query": "7 - 3", "original_query": "solve for 7 - 3"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "calculate" in prompt.lower() and "User Query: \"3+3\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "calculate", "parameters": {"query": "3+3", "original_query": "3+3"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())

            if "evaluate_logic" in prompt.lower() and "User Query: \"evaluate true AND false\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "true AND false", "original_query": "evaluate true AND false"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "evaluate_logic" in prompt.lower() and "User Query: \"logic of (NOT true OR false)\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "(NOT true OR false)", "original_query": "logic of (NOT true OR false)"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "evaluate_logic" in prompt.lower() and "User Query: \"true or false\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "true or false", "original_query": "true or false"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())

            if "translate_text" in prompt.lower() and "User Query: \"translate hello to chinese\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "hello", "target_language_hint": "chinese", "original_query": "translate hello to chinese"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "translate_text" in prompt.lower() and "User Query: \"translate 'good morning' to french'\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "good morning", "target_language_hint": "french", "original_query": "translate 'good morning' to french"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "translate_text" in prompt.lower() and "User Query: \"cat in spanish\"" in prompt:
                return LLMResponse(content=json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "cat", "target_language_hint": "spanish", "original_query": "cat in spanish"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())
            if "translate_text" in prompt.lower() and "User Query: \"meaning of bonjour\"" in prompt: # More complex case
                 return LLMResponse(content=json.dumps({"tool_name": "translate_text", "parameters": {"original_query": "meaning of bonjour"}}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())


            if "User Query: \"this is a general statement without clear tool triggers\"" in prompt:
                 return LLMResponse(content=json.dumps({"tool_name": "NO_TOOL", "parameters": None}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now()) # Default fallback

            # Default response if no specific match
            return LLMResponse(content=json.dumps({"tool_name": "NO_TOOL", "parameters": None}), model="mock", provider=ModelProvider.OPENAI, usage={}, cost=0.0, latency=0.0, timestamp=datetime.now())


        mock_llm_service.chat_completion.side_effect = mock_chat_completion_behavior

        # Pass the mocked LLM service to DailyLanguageModel
        self.dlm = DailyLanguageModel(llm_service=mock_llm_service)
        yield


    @pytest.mark.timeout(5)
    def test_01_initialization(self):
        assert self.dlm is not None
        print("TestDailyLanguageModel.test_01_initialization PASSED")

    @pytest.mark.timeout(5)
    async def test_02_recognize_intent_calculate(self):
        queries = {
            "calculate 2 + 2": {"tool_name": "calculate", "query": "2 + 2"},
            "what is 10 * 5": {"tool_name": "calculate", "query": "10 * 5"},
            "compute 100 / 20": {"tool_name": "calculate", "query": "100 / 20"},
            "solve for 7 - 3": {"tool_name": "calculate", "query": "7 - 3"},
            "3+3": {"tool_name": "calculate", "query": "3+3"} # Direct expression
        }
        for query_text, expected_params in queries.items():
            intent = await self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            assert intent is not None, f"Intent not recognized for: {query_text}"
            assert intent["tool_name"] == expected_params["tool_name"]
            assert intent["parameters"]["query"] == expected_params["query"]
            assert "original_query" in intent["parameters"]
            assert intent["parameters"]["original_query"] == query_text
        print("TestDailyLanguageModel.test_02_recognize_intent_calculate PASSED")

    @pytest.mark.timeout(5)
    async def test_03_recognize_intent_evaluate_logic(self):
        queries = {
            "evaluate true AND false": {"tool_name": "evaluate_logic", "query": "true AND false"},
            "logic of (NOT true OR false)": {"tool_name": "evaluate_logic", "query": "(NOT true OR false)"},
            "true or false": {"tool_name": "evaluate_logic", "query": "true or false"} # No prefix
        }
        for query_text, expected_params in queries.items():
            intent = await self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            assert intent is not None, f"Intent not recognized for: {query_text}"
            assert intent["tool_name"] == expected_params["tool_name"]
            assert intent["parameters"]["query"] == expected_params["query"]
        print("TestDailyLanguageModel.test_03_recognize_intent_evaluate_logic PASSED")

    @pytest.mark.timeout(5)
    async def test_04_recognize_intent_translate_text(self):
        queries = {
            "translate hello to chinese": {"tool_name": "translate_text", "text_hint": "hello", "lang_hint": "chinese"},
            "translate 'good morning' to french": {"tool_name": "translate_text", "text_hint": "good morning", "lang_hint": "french"},
            "cat in spanish": {"tool_name": "translate_text", "text_hint": "cat", "lang_hint": "spanish"},
            "meaning of bonjour": {"tool_name": "translate_text"} # More complex, tool itself will parse further from full query
        }
        for query_text, expected_details in queries.items():
            intent = await self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            assert intent is not None, f"Intent not recognized for: {query_text}"
            assert intent["tool_name"] == expected_details["tool_name"]
            assert intent["parameters"]["original_query"] == query_text
            if "text_hint" in expected_details:
                 assert intent["parameters"].get("text_to_translate_hint") == expected_details["text_hint"]
            if "lang_hint" in expected_details:
                # Check if either target_language_hint or language_context_hint matches
                assert (
                    intent["parameters"].get("target_language_hint") == expected_details["lang_hint"] or
                    intent["parameters"].get("language_context_hint") == expected_details["lang_hint"]
                )

        print("TestDailyLanguageModel.test_04_recognize_intent_translate_text PASSED")

    @pytest.mark.timeout(5)
    async def test_05_no_intent_recognized(self):
        query_text = "this is a general statement without clear tool triggers"
        intent = await self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
        # The mock generate_response for this input returns:
        # json.dumps({"tool_name": "NO_TOOL", "parameters": None})
        # The recognize_intent method then translates "NO_TOOL" to tool_name=None.
        assert intent is not None # Intent dict should exist
        assert intent["tool_name"] is None # tool_name should be None
        assert intent["parameters"] is None # parameters should be None
        print("TestDailyLanguageModel.test_05_no_intent_recognized PASSED")
        

if __name__ == '__main__':
    unittest.main(verbosity=2)
