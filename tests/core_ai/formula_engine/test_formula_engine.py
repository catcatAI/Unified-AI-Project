import unittest
import json
from pathlib import Path
import shutil # For cleaning up test directories

# Adjust import path to reach FormulaEngine from src/core_ai/formula_engine/
# This assumes tests are run from the project root (Unified-AI-Project)
# and PYTHONPATH includes 'src'
from core_ai.formula_engine import FormulaEngine
from shared.types.common_types import FormulaConfigEntry

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
        formula_to_execute = self.valid_formulas_data[0] # "greeting_high"
        result = engine.execute_formula(formula_to_execute) # type: ignore

        expected_result = {
            "action_name": "greet_user_warmly",
            "action_params": {"warmth": "high"}
        }
        self.assertEqual(result, expected_result)

    def test_execute_formula_no_params(self):
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # Find the "farewell" formula which has no explicit parameters in the dummy data
        # Note: The setUp data defines "parameters": {} for "farewell"
        farewell_formula = None
        for f_data in self.valid_formulas_data:
            if f_data["name"] == "farewell":
                farewell_formula = f_data
                break
        self.assertIsNotNone(farewell_formula, "Farewell formula not found in test data")

        if farewell_formula:
            result = engine.execute_formula(farewell_formula) # type: ignore
            expected_result = {
                "action_name": "say_goodbye",
                "action_params": {} # Expect empty dict if 'parameters' was empty or missing
            }
            self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
