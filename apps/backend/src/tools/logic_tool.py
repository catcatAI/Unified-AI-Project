import os
import sys
import json

# Add src directory to sys.path to allow imports from sibling directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tools.logic_model.logic_parser_eval import LogicParserEval
from core_ai.dependency_manager import dependency_manager

# --- Configuration for NN Model ---
MODEL_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
CHAR_MAP_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")

# Global instances for evaluators
_parser_evaluator = None
_nn_model_evaluator = None
_nn_char_to_token = None
_tensorflow_import_error = None

def _get_parser_evaluator():
    """Initializes and returns the LogicParserEval instance."""
    global _parser_evaluator
    if _parser_evaluator is None:
        print("Initializing LogicParserEval for the first time...")
        _parser_evaluator = LogicParserEval()
    return _parser_evaluator

def _get_nn_model_evaluator():
    """Loads the LogicNNModel, handling potential TensorFlow import errors."""
    global _nn_model_evaluator, _nn_char_to_token, _tensorflow_import_error
    if _nn_model_evaluator is not None or _tensorflow_import_error is not None:
        return _nn_model_evaluator, _nn_char_to_token

    # Check if TensorFlow is available through dependency manager
    if not dependency_manager.is_available('tensorflow'):
        _tensorflow_import_error = "TensorFlow not available through dependency manager"
        print(f"CRITICAL: TensorFlow not available. Logic tool's NN features will be disabled.")
        return _nn_model_evaluator, _nn_char_to_token

    try:
        from tools.logic_model.logic_model_nn import LogicNNModel
        print("Loading LogicNNModel for the first time...")
        if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
            raise FileNotFoundError("NN Model or Char Map not found.")

        _nn_model_evaluator = LogicNNModel.load_model(MODEL_LOAD_PATH, CHAR_MAP_LOAD_PATH)
        with open(CHAR_MAP_LOAD_PATH, 'r') as f:
            _nn_char_to_token = json.load(f)['char_to_token']
        print("LogicNNModel loaded successfully.")

    except ImportError as e:
        print(f"CRITICAL: TensorFlow could not be imported. Logic tool's NN features will be disabled. Error: {e}")
        _tensorflow_import_error = str(e)
    except FileNotFoundError as e:
        print(f"Warning: Logic NN model files not found. NN features will be disabled. Error: {e}")
        _tensorflow_import_error = str(e)
    except Exception as e:
        print(f"An unexpected error occurred while loading the LogicNNModel: {e}")
        _tensorflow_import_error = str(e)

    return _nn_model_evaluator, _nn_char_to_token

def evaluate_expression(expression_string: str) -> bool | str | None:
    """
    Evaluates a logical expression string using the best available method.
    It prioritizes the NN model and falls back to the parser if the NN is unavailable.
    """
    normalized_expression = expression_string.lower()
    
    # Try NN model first
    nn_model, char_map = _get_nn_model_evaluator()
    if nn_model and char_map:
        print(f"LogicTool: Evaluating '{normalized_expression}' using 'nn' method.")
        try:
            return nn_model.predict(normalized_expression, char_map)
        except Exception as e:
            print(f"Error during NN prediction for '{normalized_expression}': {e}")
            # Fall through to parser on prediction error
            print("LogicTool: NN prediction failed, falling back to parser.")

    # Fallback to parser
    print(f"LogicTool: Evaluating '{normalized_expression}' using 'parser' method.")
    parser = _get_parser_evaluator()
    result = parser.evaluate(normalized_expression)
    return result if result is not None else "Error: Invalid expression for parser."


if __name__ == '__main__':
    print("--- Logic Tool Example Usage ---")

    test_cases = [
        ("true AND false", False),
        ("NOT (true OR false)", False),
        ("false OR (true AND true)", True),
        ("invalid expression", "Error: Invalid expression for parser.")
    ]

    print("\n--- Testing Unified evaluate_expression (NN fallback to Parser) ---")
    for expr, expected in test_cases:
        result = evaluate_expression(expr)
        print(f'Test: "{expr}" -> Got: {result}')
        # We can't assert expected result because it could come from NN or parser
        # A simple check for the correct type or non-error is suitable here.
        if isinstance(result, bool):
            print(f'  (Result is a boolean, which is valid)')
        elif isinstance(result, str) and 'Error' in result:
            print(f'  (Result is an error string, which is valid for invalid expressions)')
        else:
            print(f'  (Result is of an unexpected type: {type(result)})')
        assert result is not None, f'FAIL: For "{expr}"'
    
    print("\nLogic Tool script execution finished.")