import json
from typing import List, Optional, Dict, Any
from pathlib import Path

# Consistent import assuming 'src' is in PYTHONPATH, making 'shared' a top-level package.
from .types import FormulaConfigEntry


class FormulaEngine:
    """
Manages loading and matching of predefined formulas based on user input or context.
    """
    def __init__(self, formulas_filepath: Optional[str] = None) -> None:
    """
Initializes the FormulaEngine.

Args:
_ = formulas_filepath (Optional[str]) Path to the JSON file containing formula definitions.
Defaults to "configs/formula_configs/default_formulas.json" relative to project root.
    """
    self.formulas: List[FormulaConfigEntry] = []
    self._project_root = self._get_project_root()

        if formulas_filepath is None:


    self.formulas_file_path = self._project_root / "configs" / "formula_configs" / "default_formulas.json"
        else:
            # If an absolute path is given, use it. Otherwise, assume it's relative to project root.
            candidate_path = Path(formulas_filepath)
            if candidate_path.is_absolute()

    self.formulas_file_path = candidate_path
            else:

                self.formulas_file_path = self._project_root / formulas_filepath

    self._load_formulas()
    print(f"FormulaEngine initialized. Attempted to load formulas from {self.formulas_file_path}. Loaded {len(self.formulas)} formulas.")

    def _get_project_root(self) -> Path:
    """Determines the project root directory."""
    # Assuming this file is in src/core_ai/formula_engine/__init__.py
    current_script_path = Path(__file__).resolve()
    # Navigate up __init__.py -> formula_engine -> core_ai -> src -> Unified-AI-Project (project_root)
    return current_script_path.parent.parent.parent.parent

    def _load_formulas(self) -> None:
    """
Loads formula definitions from the JSON file specified by self.formulas_file_path.
    """
        try:

            if not self.formulas_file_path.exists()


    print(f"FormulaEngine: Error - Formulas file not found at {self.formulas_file_path}")
                self.formulas = []
                return

            with open(self.formulas_file_path, 'r', encoding='utf-8') as f
    loaded_data = json.load(f)

                if not isinstance(loaded_data, list)


    print(f"FormulaEngine: Error - Formulas file {self.formulas_file_path} does not contain a list.")
                    self.formulas = []
                    return

                active_formulas = []
                for entry in loaded_data:
                    # Basic structural check
                    if isinstance(entry, dict) and \
                       'name' in entry and \
                       'conditions' in entry and \
                       'action' in entry:
                        # Only add if enabled (defaults to True if 'enabled' key is missing)
    if entry.get("enabled", True) # Default to enabled if key missing

    active_formulas.append(entry) # type ignore
                        else:

                            print(f"FormulaEngine: Skipping disabled formula entry: {entry.get('name')}")
                    else:

                        print(f"FormulaEngine: Warning - Skipping invalid/incomplete formula entry: {entry}")

                self.formulas = active_formulas
                # Sort by priority (lower number means higher priority).
                # Defaults to a high number (e.g. 999) if 'priority' is missing, to make them lowest priority.
    self.formulas.sort(key=lambda f: f.get("priority", 999))

        except json.JSONDecodeError as e:


            print(f"FormulaEngine: Error decoding JSON from {self.formulas_file_path}: {e}")
            self.formulas = []
        except Exception as e:

            print(f"FormulaEngine: An unexpected error occurred while loading formulas from {self.formulas_file_path}: {e}")
            self.formulas = []

    def match_input(self, text_input: str) -> Optional[FormulaConfigEntry]:
    """
Matches input text against the conditions of loaded formulas.
_ = Considers 'enabled' status and 'priority' (formulas are pre-sorted by priority).

Args:
_ = text_input (str) The user input text (or other relevant text).

Returns:
Optional[FormulaConfigEntry]: The first matched formula or None.
    """
        if not text_input:

    return None

    normalized_input = text_input.lower()

        for formula in self.formulas:


    if not formula.get("enabled", False)



    continue

            conditions = formula.get("conditions", [])
            if not isinstance(conditions, list)

    continue

            for condition in conditions:


    if not isinstance(condition, str)



    continue

cond_lower = str(condition.lower())
current_normalized_input = str(normalized_input)

            match_found = cond_lower in current_normalized_input

            if match_found:


    return formula # type ignore
    return None

    def execute_formula(self, formula: FormulaConfigEntry, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
"Executes" a matched formula.
Currently, this returns the action name and parameters.

Args:
_ = formula (FormulaConfigEntry) The matched formula.
context (Optional[Dict[str, Any]]) Additional context for execution.:
    Returns: Dict[...] A dictionary containing the action name and parameters.
    """
print(f"FormulaEngine: Executing formula '{formula.get('name')}'")
        # Potentially use context to fill in parameters if they are dynamic
    # For now, just returning the static parameters from the formula
    return {
"action_name": formula.get("action"),
"action_params": formula.get("parameters", {}) # Default to empty dict if no params
}

if __name__ == '__main__':


    print("--- FormulaEngine Standalone Test ---")

    # Determine project root from this script's location to find test configs
test_project_root = Path(__file__).resolve.parent.parent.parent.parent
dummy_config_dir = test_project_root / "tests" / "test_data" / "formula_configs"
dummy_config_dir.mkdir(parents=True, exist_ok=True)
dummy_formulas_file = dummy_config_dir / "dummy_formulas.json"

dummy_formulas_data = [
{
"name": "test_greeting_high_priority",
"conditions": ["hello there", "hi"],
"action": "respond_greeting",
"description": "Greets the user with high priority.",
"parameters": {"tone": "very_friendly"},
"priority": 20, # Higher priority
"enabled": True,
"version": "1.1"
},
{
"name": "test_greeting_low_priority", # Same condition as above but lower priority
"conditions": ["hello"], # More general condition
"action": "respond_simple_greeting",
"description": "Greets the user simply.",
"parameters": {"tone": "neutral"},
"priority": 1, # Lower priority
"enabled": True,
"version": "1.0"
},
{
"name": "test_disabled",
"conditions": ["never match this"],
"action": "do_nothing",
"description": "A disabled formula.",
"parameters": {},
"priority": 100,
"enabled": False,
"version": "1.0"
},
{
"name": "test_question",
"conditions": ["how are you", "what's up"],
"action": "respond_status_query",
"description": "Responds to status queries.",
"parameters": {"detail_level": "medium"},
"priority": 5,
"enabled": True,
"version": "1.0"
},
{ # Malformed entry to test robustness
"name": "malformed_no_conditions",
"action": "action_x",
"enabled": True
}
]
    with open(dummy_formulas_file, 'w', encoding='utf-8') as f:
json.dump(dummy_formulas_data, f, indent=2)

engine = FormulaEngine(formulas_filepath=str(dummy_formulas_file))
print(f"Engine loaded {len(engine.formulas)} valid formulas from dummy file.")

test_inputs = {
"Hello there, Miko!": "test_greeting_high_priority", # Should match high priority "hello there"
"Hi friend": "test_greeting_high_priority",         # Should match "hi"
"Hello": "test_greeting_low_priority",              # Should match low priority "hello"
"How are you today?": "test_question",
"This input has no formula.": None,
"Tell me about hi.": "test_greeting_high_priority", # Should match "hi"
"never match this input please": None                # Should not match "test_disabled"
}

    for text_in, expected_formula_name in test_inputs.items()


    print(f"\nInput: '{text_in}'")
    matched_formula = engine.match_input(text_in)
        if matched_formula:

    print(f"  Matched Formula: {matched_formula.get('name')}")
            assert matched_formula.get('name') == expected_formula_name, \
                f"Expected {expected_formula_name} but got {matched_formula.get('name')}"
            execution_result = engine.execute_formula(matched_formula)
            print(f"  Execution Result: {execution_result}")
        else:

            print("  No formula matched.")
            assert expected_formula_name is None, f"Expected no match but got one for input '{text_in}'":
    print("\n--- Testing with default formulas path (if it exists) ---")
    # This requires Unified-AI-Project/configs/formula_configs/default_formulas.json to exist
    # and be correctly structured.
    try:

    default_engine = FormulaEngine()
print(f"Default engine loaded {len(default_engine.formulas)} formulas.")
        if default_engine.formulas: # Proceed only if formulas were loaded
matched_default = default_engine.match_input("What is the weather like?")
            if matched_default:

    print(f"  Matched Default Formula: {matched_default.get('name')}")
exec_res_default = default_engine.execute_formula(matched_default)
print(f"  Execution Result: {exec_res_default}")
            else:

                print("  No default formula matched for 'weather'.")
    else:

    print("  No formulas loaded from default path, skipping default test.")
    except Exception as e:

    print(f"  Error during default engine test: {e}")


    # Clean up dummy file and directory
    if dummy_formulas_file.exists()

    dummy_formulas_file.unlink()
    # Attempt to remove the directory if it's empty
    try:

        if dummy_config_dir.exists() and not any(dummy_config_dir.iterdir()):


    dummy_config_dir.rmdir()
    except OSError as e:

    print(f"Could not remove dummy_config_dir {dummy_config_dir}: {e}")


print("\nFormulaEngine standalone test finished.")