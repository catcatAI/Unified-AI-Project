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
from core_ai.dependency_manager import dependency_manager, get_dependency, is_dependency_available

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
    if not is_dependency_available('tensorflow'):
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

def evaluate_expression(expression_string: str, method: str = 'parser') -> bool | str | None:
    """
    Evaluates a logical expression string using the specified method ('parser' or 'nn').
    """
    normalized_expression = expression_string.lower()
    print(f"LogicTool: Evaluating '{normalized_expression}' using '{method}' method.")

    if method == 'parser':
        parser = _get_parser_evaluator()
        result = parser.evaluate(normalized_expression)
        return result if result is not None else "Error: Invalid expression for parser."

    elif method == 'nn':
        if _tensorflow_import_error:
            return f"Error: NN model is unavailable due to an import error: {_tensorflow_import_error}"
        
        nn_model, char_map = _get_nn_model_evaluator()
        if nn_model and char_map:
            try:
                return nn_model.predict(normalized_expression, char_map)
            except Exception as e:
                print(f"Error during NN prediction for '{normalized_expression}': {e}")
                return "Error: NN model prediction failed."
        else:
            return "Error: NN model not available. Please train the NN model."

    else:
        return f"Error: Unknown evaluation method '{method}'. Use 'parser' or 'nn'."

if __name__ == '__main__':
    print("--- Logic Tool Example Usage ---")

    parser_test_cases = [
        ("true AND false", False),
        ("NOT (true OR false)", False),
        ("false OR (true AND true)", True),
        ("invalid expression", "Error: Invalid expression for parser.")
    ]

    print("\n--- Testing with Parser (default) ---")
    for expr, expected in parser_test_cases:
        result = evaluate_expression(expr)
        print(f'Test: "{expr}" -> Expected: {expected}, Got: {result}')
        assert result == expected, f'FAIL: For "{expr}"'
    print("Parser tests passed.")

    print("\n--- Testing with NN Model ---")
    print("(This will likely show an error if TensorFlow is not installed or the model is not trained)")
    for expr, _ in parser_test_cases:
        result_nn = evaluate_expression(expr, method='nn')
        print(f'Expression: "{expr}" -> NN Result: {result_nn}')

    print("\nLogic Tool script execution finished.")