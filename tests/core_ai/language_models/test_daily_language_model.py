import unittest
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core_ai.language_models.daily_language_model import DailyLanguageModel

class TestDailyLanguageModel(unittest.TestCase):

    def setUp(self):
        self.dlm = DailyLanguageModel()

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
            intent = self.dlm.recognize_intent(query_text)
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
            intent = self.dlm.recognize_intent(query_text)
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
            intent = self.dlm.recognize_intent(query_text)
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
        intent = self.dlm.recognize_intent(query_text)
        self.assertIsNone(intent)
        print("TestDailyLanguageModel.test_05_no_intent_recognized PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
