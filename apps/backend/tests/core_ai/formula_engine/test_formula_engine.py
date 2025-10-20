import unittest
import pytest
import json
from pathlib import Path
import shutil # For cleaning up test directories

from apps.backend.src.ai.formula_engine import FormulaEngine
from apps.backend.src.ai.formula_engine.types import FormulaConfigEntry

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
            _ = json.dump(self.valid_formulas_data, f)

        self.malformed_json_path = self.test_dir / "malformed.json"
        with open(self.malformed_json_path, 'w') as f:
            _ = f.write("{not_a_list: true}")

        self.empty_list_path = self.test_dir / "empty_list.json"
        with open(self.empty_list_path, 'w') as f:
            _ = json.dump([], f)

    def tearDown(self):
        """Clean up the temporary test directory."""
        if self.test_dir.exists():
            _ = shutil.rmtree(self.test_dir)

    _ = @pytest.mark.timeout(5)
    def test_load_formulas_valid_file(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        expected_active_formulas_count = sum(1 for f in self.valid_formulas_data if f.get("enabled", True))
        _ = self.assertEqual(len(engine.formulas), expected_active_formulas_count)
        _ = self.assertEqual(engine.formulas[0]["name"], "greeting_high") # Check priority sorting
        _ = self.assertIn("response_template", engine.formulas[0]) # Check new field loaded
        _ = self.assertEqual(engine.formulas[0]["response_template"], "Greetings, {user_name}! It's a pleasure to see you.")

    _ = @pytest.mark.timeout(5)
    def test_load_formulas_file_not_found(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.test_dir / "non_existent.json"))
        _ = self.assertEqual(len(engine.formulas), 0)

    _ = @pytest.mark.timeout(5)
    def test_load_formulas_malformed_json(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.malformed_json_path))
        _ = self.assertEqual(len(engine.formulas), 0)

    _ = @pytest.mark.timeout(5)
    def test_load_formulas_empty_list(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.empty_list_path))
        _ = self.assertEqual(len(engine.formulas), 0)

    _ = @pytest.mark.timeout(5)
    def test_match_input_simple_match(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("Hello world")
        _ = self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

    _ = @pytest.mark.timeout(5)
    def test_match_input_case_insensitive(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("HI THERE, friend!")
        _ = self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

    _ = @pytest.mark.timeout(5)
    def test_match_input_priority(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # "hello" is in "greeting_high" (prio 20)
        # "hey" is in "greeting_low" (prio 10)
        # If input contains both, higher priority should match.
        # (Current logic matches first condition in first formula, formulas sorted by prio)
        matched = engine.match_input("Well hello there, hey you!")
        _ = self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "greeting_high") # type: ignore

        matched_only_hey = engine.match_input("Just saying hey.")
        _ = self.assertIsNotNone(matched_only_hey)
        self.assertEqual(matched_only_hey["name"], "greeting_low") # type: ignore


    _ = @pytest.mark.timeout(5)
    def test_match_input_no_match(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("Some random text without keywords.")
        _ = self.assertIsNone(matched)

    _ = @pytest.mark.timeout(5)
    def test_match_input_disabled_formula(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("secret word") # Condition of a disabled formula
        _ = self.assertIsNone(matched)

    _ = @pytest.mark.timeout(5)
    def test_match_input_empty_input(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        matched = engine.match_input("")
        _ = self.assertIsNone(matched)

    _ = @pytest.mark.timeout(5)
    def test_execute_formula(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        formula_to_execute = self.valid_formulas_data[0] # "greeting_high"
        result = engine.execute_formula(formula_to_execute) # type: ignore

        expected_result = {
            "action_name": "greet_user_warmly",
            "action_params": {"warmth": "high"}
        }
        _ = self.assertEqual(result, expected_result)

    _ = @pytest.mark.timeout(5)
    def test_execute_formula_no_params(self) -> None:
        engine = FormulaEngine(formulas_filepath=str(self.valid_formulas_path))
        # Find the "farewell" formula which has no explicit parameters in the dummy data
        # Note: The setUp data defines "parameters": {} for "farewell"
        farewell_formula = None
        for f_data in self.valid_formulas_data:
            if f_data["name"] == "farewell":
                farewell_formula = f_data
                break
        _ = self.assertIsNotNone(farewell_formula, "Farewell formula not found in test data")

        if farewell_formula:
            result = engine.execute_formula(farewell_formula) # type: ignore
            expected_result = {
                "action_name": "say_goodbye",
                "action_params": {} # Expect empty dict if 'parameters' was empty or missing
            }
            _ = self.assertEqual(result, expected_result)

if __name__ == '__main__':
    _ = unittest.main()
