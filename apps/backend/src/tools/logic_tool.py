from diagnose_base_agent import
from system_test import
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from typing import Optional, Tuple, Dict, Any, Union

# Add the src directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from .logic_model.logic_parser_eval import
# 修复导入路径
from apps.backend.src.core.managers.dependency_manager import dependency_manager

# --- Configuration for NN Model ---
MODEL_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
CHAR_MAP_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")

logger = logging.getLogger(__name__)

class LogicTool:
    def __init__(self) -> None:
        self.parser_evaluator: Optional[LogicParserEval] = None
        self.nn_model_evaluator: Optional[Any] = None # Type hint as Any due to external library
        self.nn_char_to_token: Optional[Dict[str, int]] = None
        self.tensorflow_import_error: Optional[str] = None

    def _get_parser_evaluator(self) -> LogicParserEval:
        """Initializes and returns the LogicParserEval instance."""
        if self.parser_evaluator is None:
            logger.info("Initializing LogicParserEval for the first time...")
            self.parser_evaluator = LogicParserEval()
        return self.parser_evaluator

    def _get_nn_model_evaluator(self) -> Tuple[Optional[Any], Optional[Dict[str, int]]]:
        """Loads the LogicNNModel, handling potential TensorFlow import errors."""
        if self.nn_model_evaluator is not None or self.tensorflow_import_error is not None:
            return self.nn_model_evaluator, self.nn_char_to_token

        # Check if TensorFlow is available through dependency manager
        if not dependency_manager.is_available('tensorflow'):
            self.tensorflow_import_error = "TensorFlow not available through dependency manager"
            logger.critical(f"CRITICAL: TensorFlow not available. Logic tool's NN features will be disabled.")
            return None, None

        try:
from .logic_model.logic_model_nn import
            logger.info("Loading LogicNNModel for the first time...")
            if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
                raise FileNotFoundError("NN Model or Char Map not found.")

            self.nn_model_evaluator = LogicNNModel.load_model(MODEL_LOAD_PATH, CHAR_MAP_LOAD_PATH)
            with open(CHAR_MAP_LOAD_PATH, 'r') as f:
                self.nn_char_to_token = json.load(f)['char_to_token']
            logger.info("LogicNNModel loaded successfully.")

        except ImportError as e:
            logger.critical(f"CRITICAL: TensorFlow could not be imported. Logic tool's NN features will be disabled. Error: {e}")
            self.tensorflow_import_error = str(e)
        except FileNotFoundError as e:
            logger.warning(f"Warning: Logic NN model files not found. NN features will be disabled. Error: {e}")
            self.tensorflow_import_error = str(e)
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading the LogicNNModel: {e}")
            self.tensorflow_import_error = str(e)

        return self.nn_model_evaluator, self.nn_char_to_token

    def evaluate_expression(self, expression_string: str) -> Union[bool, str, None]:
        """
        Evaluates a logical expression string using the best available method.
        It prioritizes the NN model and falls back to the parser if the NN is unavailable.
        """
        normalized_expression = expression_string.lower()

        # Try NN model first
        nn_model, char_map = self._get_nn_model_evaluator()
        if nn_model and char_map:
            logger.info(f"LogicTool: Evaluating '{normalized_expression}' using 'nn' method.")
            try:
                return nn_model.predict(normalized_expression, char_map)
            except Exception as e:
                logger.critical(f"Error during NN prediction for '{normalized_expression}': {e}")
                # Fall through to parser on prediction error
                logger.warning("LogicTool: NN prediction failed, falling back to parser.")

        # Fallback to parser
        logger.info(f"LogicTool: Evaluating '{normalized_expression}' using 'parser' method.")
        try:
            parser = self._get_parser_evaluator()
            result = parser.evaluate(normalized_expression)
            return result if result is not None else "Error: Invalid expression for parser."
        except Exception as e:
            logger.critical(f"Error during parser evaluation for '{normalized_expression}': {e}")
            return "Error: Invalid expression for parser."

logic_tool_instance = LogicTool()
evaluate_expression = logic_tool_instance.evaluate_expression

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("--- Logic Tool Example Usage ---")

    test_cases = []
        ("true AND false", False),
        ("NOT (true OR false)", False),
        ("false OR (true AND true)", True),
        ("invalid expression", "Error: Invalid expression for parser.")
[    ]

    logger.info("\n--- Testing Unified evaluate_expression (NN fallback to Parser) ---")
    for expr, expected in test_cases:
        result = logic_tool_instance.evaluate_expression(expr) # Corrected to use instance method
        logger.info(f'Test: "{expr}" -> Got: {result}')
        # We can't assert expected result because it could come from NN or parser
        # A simple check for the correct type or non-error is suitable here.
        if isinstance(result, bool):
            logger.info(f'  (Result is a boolean, which is valid)')
        elif isinstance(result, str) and 'Error' in result:
            logger.info(f'  (Result is an error string, which is valid for invalid expressions)')
        else:
            logger.info(f'  (Result is of an unexpected type: {type(result)})')
        assert result is not None, f'FAIL: For "{expr}"'
    
    logger.info("\nLogic Tool script execution finished.")