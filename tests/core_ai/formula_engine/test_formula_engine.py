import unittest
import json
from pathlib import Path
import shutil # For cleaning up test directories

import sys # Added
import os  # Added
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))) # Added

from src.core_ai.formula_engine import FormulaEngine # Changed
from src.shared.types.common_types import FormulaConfigEntry # Changed

class TestFormulaEngine(unittest.TestCase):

    def setUp(self):
        """Set up a temporary test directory and dummy formula files."""
        self.test_dir = Path(__file__).parent / "test_temp_formulas"
        self.test_dir.mkdir(exist_ok=True)

        self.valid_formulas_data: List[FormulaConfigEntry] = [ # type: ignore
            {
                "name": "greeting_high",
                "conditions": ["hello", "hi there"],
                "action": "greet_user_warmly",
                "description": "A warm greeting.",
                "parameters": {"warmth": "high"},
                "priority": 5, # Numerically lower = higher actual priority
                "enabled": True,
                "version": "1.0",
                "response_template": "Greetings, {user_name}! It's a pleasure to see you."
            },
            {
                "name": "greeting_low",
                "conditions": ["hey"],
                "action": "greet_user_casually",
                "description": "A casual greeting.",
                "parameters": {"warmth": "low"},
                "priority": 10, # Lower than greeting_high
                "enabled": True,
                "version": "1.0",
                "response_template": "Hey there! What's up, {user_name}?" # Added template
            },
            {
                "name": "farewell",
                "conditions": ["bye", "see you"],
                "action": "say_goodbye",
                "description": "Says goodbye.",
                "parameters": {}, # No params for template here
                "priority": 15,
                "enabled": True,
                "version": "1.0",
                "response_template": "Goodbye! Have a great day." # Added template
            },
            {
                "name": "disabled_formula",
                "conditions": ["secret word"],
                "action": "do_nothing_secret",
                "description": "A disabled formula.",
                "parameters": {},
                "priority": 100,
                "enabled": False,
                "version": "1.0"
            }
        ]
        self.valid_formulas_path = self.test_dir / "valid_formulas.json"
        with open(self.valid_formulas_path, 'w') as f:
            json.dump(self.valid_formulas_data, f)

        self.malformed_json_path = self.test_dir / "malformed.json"
        with open(self.malformed_json_path, 'w') as f:
            f.write("{not_a_list: true}")

        self.empty_list_path = self.test_dir / "empty_list.json"
        with open(self.empty_list_path, 'w') as f:
            json.dump([], f)

    def tearDown(self):
        """Clean up the temporary test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_load_formulas_valid_file(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        expected_active_formulas_count = sum(1 for f in self.valid_formulas_data if f.get("enabled", True))
        self.assertEqual(len(engine.formulas), expected_active_formulas_count)
        self.assertEqual(engine.formulas[0]["name"], "greeting_high") # Check priority sorting
        self.assertIn("response_template", engine.formulas[0]) # Check new field loaded
        self.assertEqual(engine.formulas[0]["response_template"], "Greetings, {user_name}! It's a pleasure to see you.")

    def test_load_formulas_file_not_found(self):
        engine = FormulaEngine(formulas_filepath=str(self.test_dir / "non_existent.json"))
        self.assertEqual(len(engine.formulas), 0)

    def test_load_formulas_malformed_json(self):
        engine = FormulaEngine(formulas_filepath=str(self.malformed_json_path))
        self.assertEqual(len(engine.formulas), 0)

    def test_load_formulas_empty_list(self):
        engine = FormulaEngine(formulas_filepath=str(self.empty_list_path))
        self.assertEqual(len(engine.formulas), 0)

    def test_match_input_simple_match(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("Hello world")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

    def test_match_input_case_insensitive(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("HI THERE, friend!")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

    def test_match_input_priority(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # "hello" is in "greeting_high" (prio 20)
        # "hey" is in "greeting_low" (prio 10)
        # If input contains both, higher priority should match.
        # (Current logic matches first condition in first formula, formulas sorted by prio)
        matched = engine.match_input("Well hello there, hey you!")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

        matched_only_hey = engine.match_input("Just saying hey.")
        self.assertIsNotNone(matched_only_hey)
        self.assertEqual(matched_only_hey["name"], "greeting_low") # type: ignore


    def test_match_input_no_match(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("Some random text without keywords.")
        self.assertIsNone(matched)

    def test_match_input_disabled_formula(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("secret word") # Condition of a disabled formula
        self.assertIsNone(matched)

    def test_match_input_empty_input(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("")
        self.assertIsNone(matched)

    def test_execute_formula(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        formula_to_execute = self.valid_formulas_data[0] # "greeting_high" -> "Greetings, {user_name}! It's a pleasure to see you."
        context = {"user_name": "TestUser", "unused_key": "value"}
        result = engine.execute_formula(formula_to_execute, context) # type: ignore

        expected_result = {
            "action_name": "greet_user_warmly",
            "action_params": {"warmth": "high"},
            "formatted_response": "Greetings, TestUser! It's a pleasure to see you."
        }
        self.assertEqual(result, expected_result)

    def test_execute_formula_no_params(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # "farewell" formula has "response_template": "Goodbye! Have a great day." (no placeholders)
        # and "parameters": {}
        farewell_formula_data = None
        for f_data in self.valid_formulas_data:
            if f_data["name"] == "farewell":
                farewell_formula_data = f_data
                break
        self.assertIsNotNone(farewell_formula_data, "Farewell formula not found in test data")

        if farewell_formula_data:
            # Test with context
            context = {"user_name": "Friend"} # Context won't be used by this template
            result_with_context = engine.execute_formula(farewell_formula_data, context) # type: ignore
            expected_result_with_context = {
                "action_name": "say_goodbye",
                "action_params": {},
                "formatted_response": "Goodbye! Have a great day."
            }
            self.assertEqual(result_with_context, expected_result_with_context)

            # Test without context
            result_no_context = engine.execute_formula(farewell_formula_data) # type: ignore
            expected_result_no_context = {
                "action_name": "say_goodbye",
                "action_params": {},
                "formatted_response": "Goodbye! Have a great day." # Template returned as is
            }
            self.assertEqual(result_no_context, expected_result_no_context)


    def test_execute_formula_with_template_missing_context_keys(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # Create a dummy formula for this test or ensure one exists in valid_formulas_data
        # For now, assume greeting_high: "Greetings, {user_name}! It's a pleasure to see you."
        formula_with_template = self.valid_formulas_data[0] # greeting_high

        context_missing_keys = {"location": "the office"} # Missing user_name
        # Expect a warning to be printed by FormulaEngine, and raw template in formatted_response
        with patch('builtins.print') as mock_print:
            result = engine.execute_formula(formula_with_template, context_missing_keys) # type: ignore
            mock_print.assert_any_call(f"FormulaEngine: Warning - KeyError during response_template formatting for formula '{formula_with_template['name']}'. Missing key: 'user_name'. Returning raw template.")

        expected_result = {
            "action_name": formula_with_template["action"],
            "action_params": formula_with_template["parameters"],
            "formatted_response": formula_with_template["response_template"] # Raw template
        }
        self.assertEqual(result, expected_result)

    def test_execute_formula_no_template(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # Need a formula without 'response_template'. Add one if not present or use one.
        # Let's assume 'disabled_formula' doesn't have one, or add a new one.
        # For safety, let's create one for the test.
        formula_no_template_data: FormulaConfigEntry = { # type: ignore
            "name": "no_template_test",
            "conditions": ["trigger no template"],
            "action": "action_no_template",
            "description": "Test no template.",
            "parameters": {"p1": "v1"},
            "priority": 1, "enabled": True, "version": "1.0"
            # No response_template key
        }
        # To test this properly, we'd need to load this into an engine instance.
        # For now, we'll assume we can pick one from valid_formulas_data if it lacks a template.
        # The current valid_formulas_data all have templates. Let's assume 'disabled_formula' is modified
        # or we conceptually add one.
        # For this test, we will mock a formula entry without the template.

        mock_formula_entry = {"name": "mock_no_template", "action": "mock_action", "parameters": {}}

        context = {"user_name": "TestUser"}
        result = engine.execute_formula(mock_formula_entry, context) # type: ignore

        expected_result = {
            "action_name": "mock_action",
            "action_params": {}
            # No 'formatted_response' key expected
        }
        self.assertEqual(result, expected_result)
        self.assertNotIn("formatted_response", result)


    def test_execute_formula_no_context_with_template(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        formula_with_template = self.valid_formulas_data[0] # greeting_high has "Greetings, {user_name}!"

        # Expect a warning if template has placeholders, and raw template in formatted_response
        with patch('builtins.print') as mock_print:
            result = engine.execute_formula(formula_with_template, context=None) # type: ignore
            mock_print.assert_any_call(f"FormulaEngine: Warning - Formula '{formula_with_template['name']}' has a response template but no context was provided. Returning raw template.")

        expected_result = {
            "action_name": formula_with_template["action"],
            "action_params": formula_with_template["parameters"],
            "formatted_response": formula_with_template["response_template"] # Raw template
        }
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
