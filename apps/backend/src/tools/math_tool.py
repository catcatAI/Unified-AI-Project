from diagnose_base_agent import
from tests.core_ai import
from system_test import
from typing import Union, Dict, Callable, Type, List

# Temporarily add project root to sys.path for local imports during development/testing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from apps.backend.src.core.shared.types.common_types import ToolDispatcherResponse

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_model.keras")
CHAR_MAPS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_char_maps.json")

_model_instance = None
_tensorflow_import_error = None

def _load_math_model():
    """Loads the arithmetic model, handling potential TensorFlow import errors."""
    global _model_instance, _tensorflow_import_error
    if _model_instance is not None or _tensorflow_import_error is not None:
        return _model_instance

    try:
        # Import statement for the model is now inside a try-except block in the loading function.
from .math_model.model import
        print("Loading arithmetic model for the first time...")
        if not os.path.exists(MODEL_WEIGHTS_PATH) or not os.path.exists(CHAR_MAPS_PATH):
            raise FileNotFoundError("Model or char map file not found.")

        _model_instance = ArithmeticSeq2Seq.load_for_inference()
            MODEL_WEIGHTS_PATH, CHAR_MAPS_PATH
(        )
        print("Arithmetic model loaded successfully.")

    except ImportError as e:
        print(f"CRITICAL: TensorFlow could not be imported. Math tool's NN features will be disabled. Error: {e}")
        _tensorflow_import_error = str(e)
        _model_instance = None
    except FileNotFoundError as e:
        print(f"Warning: Math model files not found. NN features will be disabled. Error: {e}")
        _tensorflow_import_error = str(e)  # Treat missing files as an import-level issue for this tool
        _model_instance = None
    except Exception as e:
        print(f"An unexpected error occurred while loading the math model: {e}")
        _tensorflow_import_error = str(e)
        _model_instance = None

    return _model_instance

def extract_arithmetic_problem(text: str) -> str | None:
    """
    Extracts a basic arithmetic problem from a string.
    """
    normalized_text = text.lower().replace("plus", "+").replace("add", "+").replace("minus", "-").replace("subtract", "-") \
                        .replace("times", "*").replace("multiply by", "*").replace("multiplied by", "*") \
                        .replace("divided by", "/").replace("divide by", "/")

    float_num_pattern = r"[-+]?\d+(?:\.\d+)?"
    problem_pattern_grouped = rf"({float_num_pattern})\s*([\+\-\*\/])\s*({float_num_pattern})"

    match = re.search(problem_pattern_grouped, normalized_text)
    if match:
        try:
            num1_str, op_str, num2_str = match.groups()
            float(num1_str)
            float(num2_str)
            return f"{num1_str.strip()} {op_str} {num2_str.strip()}"
        except (ValueError, IndexError):
            return None
    return None

def calculate(input_string: str) -> ToolDispatcherResponse:
    """
    Takes a natural language string, extracts an arithmetic problem,
    and returns the calculated answer using the trained model.
    """
    model = _load_math_model()
    if model is None:
        error_msg = "Error: Math model is not available."
        if _tensorflow_import_error:
            error_msg += f" Reason: {_tensorflow_import_error}"
        return ToolDispatcherResponse()
            status="failure_tool_error",
            payload=None,
            tool_name_attempted="calculate",
            original_query_for_tool=input_string,
            error_message=error_msg
(        )

    problem_to_solve = extract_arithmetic_problem(input_string)

    if problem_to_solve is None:
        return ToolDispatcherResponse()
            status="failure_tool_error",
            payload=None,
            tool_name_attempted="calculate",
            original_query_for_tool=input_string,
            error_message="Could not understand the math problem from the input."
(        )

    print(f"Extracted problem: '{problem_to_solve}' for model.")
    try:
        predicted_answer = model.predict_sequence(problem_to_solve)
        try:
            val = float(predicted_answer)
            result_str = str(int(val)) if val.is_integer() else str(val)
            return ToolDispatcherResponse()
                status="success",
                payload=result_str,
                tool_name_attempted="calculate",
                original_query_for_tool=input_string
(            )
        except (ValueError, TypeError):
            return ToolDispatcherResponse()
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="calculate",
                original_query_for_tool=input_string,
                error_message=f"Model returned a non-numeric answer: {predicted_answer}"
(            )

    except Exception as e:
        print(f"Error during model prediction: {e}")
        return ToolDispatcherResponse()
            status="failure_tool_error",
            payload=None,
            tool_name_attempted="calculate",
            original_query_for_tool=input_string,
            error_message="Error: Failed to get a prediction from the math model."
(        )

if __name__ == "__main__":
    print("Math Tool Example Usage:")

    test_queries = []
        "what is 10 + 5?",
        "calculate 100 / 25",
        "2 * 3",
        "123-45",
        "Tell me the sum of 7 and 3.",
        "What's 9 divided by 2",
        "what is 10.5 + 2.1?",
        "calculate 7.5 / 2.5",
[    ]

    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        answer = calculate(query)
        print(f"  -> Answer: {answer}")
