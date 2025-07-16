import unittest
import os
import sys

import json
from src.core_ai.language_models.daily_language_model import DailyLanguageModel

class TestDailyLanguageModel(unittest.TestCase):

    def setUp(self):
        self.dlm = DailyLanguageModel()
        # Mocking available tools as ToolDispatcher would provide them
        self.mock_available_tools = {
            "calculate": "Performs arithmetic calculations.",
            "evaluate_logic": "Evaluates simple logical expressions.",
            "translate_text": "Translates text between languages.",
            "inspect_code": "Describes the structure of available tools."
        }
        # Patch the LLMInterface within DLM to return expected JSONs for tests
        # This is a simplified mock; a more robust approach would be to inject a mock LLMInterface
        # or use a more sophisticated patching strategy if the LLM responses need to be varied per test.
        # For now, we assume the LLM will respond correctly if the prompt is well-formed based on available_tools.

        # To make tests more robust without deep LLM mocking here, we'll assume
        # the LLM returns a somewhat predictable structure if the prompt is right.
        # The key is that `recognize_intent` needs `available_tools`.
        # The actual LLM call and its parsing is complex to fully mock here without
        # a dedicated mock LLM response strategy for each query_text.
        # The `if __name__ == '__main__'` block in daily_language_model.py shows a more detailed mock.
        # For unit testing `recognize_intent` itself, we should mock `self.llm_interface.generate_response`.

        # Let's create a simple mock for generate_response for now for these tests.
        # This mock will be very basic and might need refinement.
        def mock_generate_response(prompt):
            if "calculate" in prompt.lower() and "User Query: \"calculate 2 + 2\"" in prompt :
                 return json.dumps({"tool_name": "calculate", "parameters": {"query": "2 + 2", "original_query": "calculate 2 + 2"}})
            if "calculate" in prompt.lower() and "User Query: \"what is 10 * 5\"" in prompt :
                 return json.dumps({"tool_name": "calculate", "parameters": {"query": "10 * 5", "original_query": "what is 10 * 5"}})
            if "calculate" in prompt.lower() and "User Query: \"compute 100 / 20\"" in prompt :
                 return json.dumps({"tool_name": "calculate", "parameters": {"query": "100 / 20", "original_query": "compute 100 / 20"}})
            if "calculate" in prompt.lower() and "User Query: \"solve for 7 - 3\"" in prompt :
                 return json.dumps({"tool_name": "calculate", "parameters": {"query": "7 - 3", "original_query": "solve for 7 - 3"}})
            if "calculate" in prompt.lower() and "User Query: \"3+3\"" in prompt :
                 return json.dumps({"tool_name": "calculate", "parameters": {"query": "3+3", "original_query": "3+3"}})

            if "evaluate_logic" in prompt.lower() and "User Query: \"evaluate true AND false\"" in prompt:
                return json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "true AND false", "original_query": "evaluate true AND false"}})
            if "evaluate_logic" in prompt.lower() and "User Query: \"logic of (NOT true OR false)\"" in prompt:
                return json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "(NOT true OR false)", "original_query": "logic of (NOT true OR false)"}})
            if "evaluate_logic" in prompt.lower() and "User Query: \"true or false\"" in prompt:
                return json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "true or false", "original_query": "true or false"}})

            if "translate_text" in prompt.lower() and "User Query: \"translate hello to chinese\"" in prompt:
                return json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "hello", "target_language_hint": "chinese", "original_query": "translate hello to chinese"}})
            if "translate_text" in prompt.lower() and "User Query: \"translate 'good morning' to french\"" in prompt:
                return json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "good morning", "target_language_hint": "french", "original_query": "translate 'good morning' to french"}})
            if "translate_text" in prompt.lower() and "User Query: \"cat in spanish\"" in prompt:
                return json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate_hint": "cat", "target_language_hint": "spanish", "original_query": "cat in spanish"}})
            if "translate_text" in prompt.lower() and "User Query: \"meaning of bonjour\"" in prompt: # More complex case
                 return json.dumps({"tool_name": "translate_text", "parameters": {"original_query": "meaning of bonjour"}})


            if "User Query: \"this is a general statement without clear tool triggers\"" in prompt:
                 return json.dumps({"tool_name": "NO_TOOL", "parameters": None})
            return json.dumps({"tool_name": "NO_TOOL", "parameters": None}) # Default fallback

        self.dlm.llm_interface.generate_response = mock_generate_response


    def test_01_initialization(self):
        self.assertIsNotNone(self.dlm)
        print("TestDailyLanguageModel.test_01_initialization PASSED")

    def test_02_recognize_intent_calculate(self):
        queries = {
            "calculate 2 + 2": {"tool_name": "calculate", "query": "2 + 2"},
            "what is 10 * 5": {"tool_name": "calculate", "query": "10 * 5"},
            "compute 100 / 20": {"tool_name": "calculate", "query": "100 / 20"},
            "solve for 7 - 3": {"tool_name": "calculate", "query": "7 - 3"},
            "3+3": {"tool_name": "calculate", "query": "3+3"} # Direct expression
        }
        for query_text, expected_params in queries.items():
            intent = self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            self.assertIsNotNone(intent, f"Intent not recognized for: {query_text}")
            self.assertEqual(intent["tool_name"], expected_params["tool_name"])
            self.assertEqual(intent["parameters"]["query"], expected_params["query"])
            self.assertIn("original_query", intent["parameters"])
            self.assertEqual(intent["parameters"]["original_query"], query_text)
        print("TestDailyLanguageModel.test_02_recognize_intent_calculate PASSED")

    def test_03_recognize_intent_evaluate_logic(self):
        queries = {
            "evaluate true AND false": {"tool_name": "evaluate_logic", "query": "true AND false"},
            "logic of (NOT true OR false)": {"tool_name": "evaluate_logic", "query": "(NOT true OR false)"},
            "true or false": {"tool_name": "evaluate_logic", "query": "true or false"} # No prefix
        }
        for query_text, expected_params in queries.items():
            intent = self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            self.assertIsNotNone(intent, f"Intent not recognized for: {query_text}")
            self.assertEqual(intent["tool_name"], expected_params["tool_name"])
            self.assertEqual(intent["parameters"]["query"], expected_params["query"])
        print("TestDailyLanguageModel.test_03_recognize_intent_evaluate_logic PASSED")

    def test_04_recognize_intent_translate_text(self):
        queries = {
            "translate hello to chinese": {"tool_name": "translate_text", "text_hint": "hello", "lang_hint": "chinese"},
            "translate 'good morning' to french": {"tool_name": "translate_text", "text_hint": "good morning", "lang_hint": "french"},
            "cat in spanish": {"tool_name": "translate_text", "text_hint": "cat", "lang_hint": "spanish"},
            "meaning of bonjour": {"tool_name": "translate_text"} # More complex, tool itself will parse further from full query
        }
        for query_text, expected_details in queries.items():
            intent = self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
            self.assertIsNotNone(intent, f"Intent not recognized for: {query_text}")
            self.assertEqual(intent["tool_name"], expected_details["tool_name"])
            self.assertEqual(intent["parameters"]["original_query"], query_text)
            if "text_hint" in expected_details:
                 self.assertEqual(intent["parameters"].get("text_to_translate_hint"), expected_details["text_hint"])
            if "lang_hint" in expected_details:
                # Check if either target_language_hint or language_context_hint matches
                self.assertTrue(
                    intent["parameters"].get("target_language_hint") == expected_details["lang_hint"] or
                    intent["parameters"].get("language_context_hint") == expected_details["lang_hint"]
                )

        print("TestDailyLanguageModel.test_04_recognize_intent_translate_text PASSED")

    def test_05_no_intent_recognized(self):
        query_text = "this is a general statement without clear tool triggers"
        intent = self.dlm.recognize_intent(query_text, available_tools=self.mock_available_tools)
        # The mock generate_response for this input returns:
        # json.dumps({"tool_name": "NO_TOOL", "parameters": None})
        # The recognize_intent method then translates "NO_TOOL" to tool_name=None.
        self.assertIsNotNone(intent) # Intent dict should exist
        self.assertIsNone(intent["tool_name"]) # tool_name should be None
        self.assertIsNone(intent["parameters"]) # parameters should be None
        print("TestDailyLanguageModel.test_05_no_intent_recognized PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
