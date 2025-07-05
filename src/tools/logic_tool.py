import os
import sys
import json

# Add src directory to sys.path to allow imports from sibling directories (tools.logic_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")) # Assuming this file is in src/tools/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR) # Add src to path

try:
    from tools.logic_model.logic_parser_eval import LogicParserEval
    from tools.logic_model.logic_model_nn import LogicNNModel
except ImportError as e:
    print(f"Error importing logic model components: {e}")
    print("Ensure that logic_parser_eval.py and logic_model_nn.py are in the tools/logic_model/ directory.")
    # Provide dummy classes if import fails, so the rest of the system can load this tool
    class LogicParserEval:
        def evaluate(self, expr_str): return None
    class LogicNNModel:
        @classmethod
        def load_model(cls, *args, **kwargs): return None
        def predict(self, *args, **kwargs): return None
    print("Using dummy LogicModel classes due to import error.")


# --- Configuration for NN Model ---
MODEL_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
CHAR_MAP_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")

# Global instances for the evaluators (loaded once)
_parser_evaluator = None
_nn_model_evaluator = None
_nn_char_to_token = None # Store char_to_token for NN prediction

def _get_parser_evaluator():
    """Initializes and returns the LogicParserEval instance."""
    global _parser_evaluator
    if _parser_evaluator is None:
        print("Initializing LogicParserEval for the first time...")
        _parser_evaluator = LogicParserEval()
    return _parser_evaluator

def _get_nn_model_evaluator():
    """Initializes and returns the LogicNNModel instance and its char_to_token map."""
    global _nn_model_evaluator, _nn_char_to_token
    if _nn_model_evaluator is None:
        print("Loading LogicNNModel for the first time...")
        if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
            print(f"Warning: NN Model ({MODEL_LOAD_PATH}) or Char Map ({CHAR_MAP_LOAD_PATH}) not found. NN method will fail.")
            return None, None # Cannot load
        try:
            # Dimensions should ideally come from char_map or a config
            # Using defaults from logic_model_nn.py for now.
            # The load_model in LogicNNModel was updated to get these from the loaded model/char_map.
            _nn_model_evaluator = LogicNNModel.load_model(MODEL_LOAD_PATH, CHAR_MAP_LOAD_PATH)

            # Load char_to_token separately for the predict method if not part of the instance
            # (Current LogicNNModel.predict takes char_to_token as arg)
            with open(CHAR_MAP_LOAD_PATH, 'r') as f:
                char_maps = json.load(f)
            _nn_char_to_token = char_maps['char_to_token']
            print("LogicNNModel loaded successfully.")

        except Exception as e:
            print(f"Error loading LogicNNModel: {e}")
            _nn_model_evaluator = None # Ensure it's None if loading fails
            _nn_char_to_token = None

    return _nn_model_evaluator, _nn_char_to_token

def evaluate_expression(expression_string: str, method: str = 'parser') -> bool | str | None:
    """
    Evaluates a logical expression string using the specified method ('parser' or 'nn').
    Returns boolean result, an error string, or None for severe errors.
    """
    print(f"LogicTool: Evaluating '{expression_string}' using '{method}' method.")

    if method == 'parser':
        parser = _get_parser_evaluator()
        if parser:
            result = parser.evaluate(expression_string)
            if result is None:
                return "Error: Invalid expression for parser."
            return result
        else: # Should not happen if LogicParserEval is correctly defined
            return "Error: Parser evaluator not available."

    elif method == 'nn':
        nn_model, char_map = _get_nn_model_evaluator()
        if nn_model and char_map:
            try:
                # The predict method in LogicNNModel expects the raw string
                # and handles tokenization internally.
                return nn_model.predict(expression_string, char_map)
            except Exception as e:
                print(f"Error during NN prediction for '{expression_string}': {e}")
                return "Error: NN model prediction failed."
        else:
            return "Error: NN model not available or char_map missing. Please train the NN model."

    else:
        return f"Error: Unknown evaluation method '{method}'. Use 'parser' or 'nn'."

if __name__ == '__main__':
    print("--- Logic Tool Example Usage ---")

    test_expressions = [
        "true AND false",
        "NOT (true OR false)",
        "false OR (true AND true)",
        "true",
        "invalid expression",
        "(false AND true" # Missing paren
    ]

    print("\n--- Testing with Parser (default) ---")
    for expr in test_expressions:
        result = evaluate_expression(expr)
        print(f"Expression: \"{expr}\" -> Parser Result: {result}")

    print("\n--- Testing with NN Model ---")
    print("(Note: NN model needs to be trained for meaningful results. This will likely show errors or random output if model files don't exist or model is untrained.)")
    # To test NN properly, ensure dummy or trained model files are present
    # For this example, it will likely print "Error: NN model not available..."

    # Create dummy files for NN model loading to pass the file existence check in _get_nn_model_evaluator
    # This is for testing the call path, not the NN's correctness.
    os.makedirs(os.path.dirname(MODEL_LOAD_PATH), exist_ok=True)
    if not os.path.exists(CHAR_MAP_LOAD_PATH):
        dummy_char_map = {"char_to_token": {"t":0, "r":1, "u":2, "e":3, " ":4, "A":5, "N":6, "D":7, "<PAD>":8, "<UNK>":9}, "token_to_char": {}, "vocab_size": 10, "max_seq_len":10}
        with open(CHAR_MAP_LOAD_PATH, 'w') as f:
            json.dump(dummy_char_map, f)
        print(f"Created dummy char map at {CHAR_MAP_LOAD_PATH} for test.")

    # We can't easily create a dummy .keras model file here.
    # So, NN evaluation will likely show the "model not found" or "NN model not available" error.
    # This is acceptable for this standalone script test.

    for expr in test_expressions:
        # Only attempt NN if we are sure the model path exists (even if it's a dummy/untrained one)
        # For now, we'll let it try and print the error if files are missing.
        result_nn = evaluate_expression(expr, method='nn')
        print(f"Expression: \"{expr}\" -> NN Result: {result_nn}")

    # Clean up dummy char map if created
    if 'dummy_char_map' in locals() and os.path.exists(CHAR_MAP_LOAD_PATH):
        if json.load(open(CHAR_MAP_LOAD_PATH)) == dummy_char_map:
            os.remove(CHAR_MAP_LOAD_PATH)
            print(f"Removed dummy char map {CHAR_MAP_LOAD_PATH}.")

    print("\nLogic Tool script execution finished.")
