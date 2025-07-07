import os
import re
from src.tools.math_model.model import ArithmeticSeq2Seq # Corrected import

# --- Configuration ---
# Determine paths relative to this file or a known project root.
# For now, assuming paths are relative to the project root.
# This might need adjustment if the tool is run from a different working directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

MODEL_WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_model.keras")
CHAR_MAPS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_char_maps.json")

# Global variable to hold the loaded model, so it's loaded only once.
_model_instance = None

def _load_math_model():
    """Loads the arithmetic model and character maps."""
    global _model_instance
    if _model_instance is None:
        print("Loading arithmetic model for the first time...")
        try:
            # These dimensions must match the ones used during training.
            # Ideally, these should be saved in char_maps.json or a model config file.
            # For now, using the values from train.py.
            # latent_dim = 256 # No longer needed here
            # embedding_dim = 128 # No longer needed here
            _model_instance = ArithmeticSeq2Seq.load_for_inference(
                MODEL_WEIGHTS_PATH, CHAR_MAPS_PATH # latent_dim and embedding_dim removed
            )
            print("Arithmetic model loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error loading math model: {e}")
            print("Please ensure the model and char maps are trained and saved correctly.")
            _model_instance = None # Ensure it stays None if loading fails
        except Exception as e:
            print(f"An unexpected error occurred while loading the math model: {e}")
            _model_instance = None
    return _model_instance

def extract_arithmetic_problem(text: str) -> str | None:
    """
    Extracts a basic arithmetic problem from a string.
    Example: "what is 10 + 5?" -> "10 + 5"
    Example: "calculate 100 / 25" -> "100 / 25"
    Searches for patterns like: number op number (op number)*
    """
    # Normalize word operators to symbols first
    normalized_text = text.lower()
    normalized_text = normalized_text.replace("plus", "+")
    normalized_text = normalized_text.replace("add", "+")
    normalized_text = normalized_text.replace("minus", "-")
    normalized_text = normalized_text.replace("subtract", "-")
    normalized_text = normalized_text.replace("times", "*")
    normalized_text = normalized_text.replace("multiply by", "*")
    normalized_text = normalized_text.replace("multiplied by", "*")
    normalized_text = normalized_text.replace("divided by", "/")
    normalized_text = normalized_text.replace("divide by", "/")
    # Use normalized_text for subsequent regex searches

    # Regex to find patterns like "number operator number"
    # This regex handles integers and basic operators +, -, *, /
    # It allows for spaces around numbers and operators.
    # It tries to find the most complete expression.

    # More robust regex:
    # Looks for: number (spaces) operator (spaces) number ( (spaces) operator (spaces) number )*
    # This allows for multi-part expressions like "1 + 2 - 3" but eval in data_gen doesn't handle that sequence well.
    # The current data_generator generates "num op num". So we match that.

    # Regex for "number operator number" with optional surrounding text, supporting floats.
    # Captures num1, operator, num2 in groups.
    float_num_pattern = r"[-+]?\d+(?:\.\d+)?" # Number can be int or float, optionally signed
    # Pattern to capture: (num1) <optional spaces> (operator) <optional spaces> (num2)
    # This will find the first occurrence of such a pattern.
    problem_pattern_grouped = rf"({float_num_pattern})\s*([\+\-\*\/])\s*({float_num_pattern})"

    match = re.search(problem_pattern_grouped, normalized_text)
    if match:
        num1_str = match.group(1)
        op_str = match.group(2)
        num2_str = match.group(3)

        # Validate that parts are indeed numbers (though regex should ensure it)
        try:
            float(num1_str)
            float(num2_str)
            # Return in the desired "NUM OP NUM" format with single spaces
            return f"{num1_str.strip()} {op_str} {num2_str.strip()}"
        except ValueError:
            # This should ideally not be reached if the regex is correct
            pass # Fall through if somehow parts are not valid numbers

    # If the primary search fails, it means the input doesn't contain a clear "num op num"
    # or it's more complex than the simple pattern.
    return None


def calculate(input_string: str) -> str:
    """
    Takes a natural language string, extracts an arithmetic problem,
    and returns the calculated answer using the trained model.
    """
    model = _load_math_model()
    if model is None:
        return "Error: Math model is not available."

    problem_to_solve = extract_arithmetic_problem(input_string)

    if problem_to_solve is None:
        # Fallback or simple eval for basic problems if model can't parse
        # This part is tricky: if the model is the primary calculator,
        # it should handle all valid forms. If not, direct eval is an option.
        # For now, let's assume if no problem is extracted, we can't solve.
        try:
            # As a simple fallback, try to eval the input_string directly if it looks like a simple expression
            # THIS IS RISKY AND SHOULD BE REPLACED WITH A SAFE PARSER/EVALUATOR
            # For "1+1" type inputs, it might work, but "what is 1+1" will fail here.
            # The model should be the one doing the calculation.
            # If extract_arithmetic_problem is robust, this eval is not needed.
            # Let's rely on extract_arithmetic_problem.
            return "Could not understand the math problem from the input."
        except: # Catch eval errors
             return "Could not understand or evaluate the math problem."


    print(f"Extracted problem: '{problem_to_solve}' for model.")

    try:
        predicted_answer = model.predict_sequence(problem_to_solve)
        # Validate if the answer is a number, or handle cases where it might not be (e.g. "Error")
        try:
            # Attempt to format to standard number string, e.g. "2.0" -> "2" if it's an int
            val = float(predicted_answer)
            if val.is_integer():
                return str(int(val))
            return predicted_answer
        except ValueError:
            return f"Model returned a non-numeric answer: {predicted_answer}"

    except Exception as e:
        print(f"Error during model prediction: {e}")
        return "Error: Failed to get a prediction from the math model."

if __name__ == '__main__':
    # Example Usage (ensure model and char_maps are available)
    print("Math Tool Example Usage:")

    # Create dummy files if they don't exist for basic testing without training
    # This is just for the __main__ block to run without crashing if files are missing.
    # In a real scenario, these files must be generated by training.
    if not os.path.exists(MODEL_WEIGHTS_PATH) or not os.path.exists(CHAR_MAPS_PATH):
        print(f"Warning: Model or char maps not found. Predictions will fail or use uninitialized model.")
        print(f"Looked for model at: {MODEL_WEIGHTS_PATH}")
        print(f"Looked for char_maps at: {CHAR_MAPS_PATH}")
        # To allow the script to run for basic parsing tests, we can mock the model part:
        # For this example, we'll let _load_math_model print its error and return None.

    test_queries = [
        "what is 10 + 5?",
        "calculate 100 / 25",
        "2 * 3",
        "123-45",
        "Tell me the sum of 7 and 3.", # More complex, extract_arithmetic_problem might fail
        "What's 9 divided by 2",
        # New float test cases
        "what is 10.5 + 2.1?",
        "calculate 7.5 / 2.5",
        "3.14 * 2.0",
        "10.0 - 3.55"
    ]

    for query in test_queries:
        problem_extracted = extract_arithmetic_problem(query)
        print(f"\nQuery: \"{query}\"")
        if problem_extracted:
            print(f"  -> Extracted: \"{problem_extracted}\"")
            # Only call calculate if model is expected to be available
            if _model_instance is not None or (os.path.exists(MODEL_WEIGHTS_PATH) and os.path.exists(CHAR_MAPS_PATH)):
                 answer = calculate(query) # Pass original query to calculate
                 print(f"  -> Answer: {answer}")
            else:
                print("  -> Model not loaded, skipping calculation.")
        else:
            print(f"  -> Could not extract a math problem.")

    # Test direct calculation if model is loaded
    if _load_math_model() is not None: # Ensures model is loaded if available
        print("\nDirect calculation test with loaded model:")
        direct_problem = "7 * 6"
        print(f"Problem: \"{direct_problem}\"")
        direct_answer = calculate(direct_problem) # Calculate expects full query
        print(f"Answer: {direct_answer}")
    else:
        print("\nSkipping direct calculation test as model could not be loaded.")
