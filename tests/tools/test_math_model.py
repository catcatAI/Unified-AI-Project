import unittest
import os
import json
import csv
import sys

# Add src directory to sys.path to allow aletive imports
# This is often needed when running tests from a tests/ subdirectory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.math_model import data_generator
try:
    from tools.math_model.model import ArithmeticSeq2Seq, get_char_token_maps
    _tensorflow_available = True
except ImportError:
    _tensorflow_available = False
    class ArithmeticSeq2Seq: # Dummy class
        def __init__(self, *args, **kwargs): pass
        def _build_inference_models(self): pass
        def predict_sequence(self, *args, **kwargs): return "Error: Model not available"
        @classmethod
        def load_for_inference(cls, *args, **kwargs): return None
    def get_char_token_maps(*args, **kwargs): return {}, {}, 0, 0, 0
from tools.math_tool import extract_arithmetic_problem, calculate as calculate_via_tool
from tools.math_tool import MODEL_WEIGHTS_PATH, CHAR_MAPS_PATH # Import constants
from tools.tool_dispatcher import ToolDispatcher

# Define a consistent test output directory
TEST_OUTPUT_DIR = "Unified-AI-Project/tests/test_output_data/"
# Ensure this test output directory exists
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

class TestMathModelComponents(unittest.TestCase):

    def setUp(self):
        # Clean up any generated files before each test run if necessary
        self.train_csv_file = os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.csv")
        self.train_json_file = os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.json")
        self.char_map_file = os.path.join(TEST_OUTPUT_DIR, "test_char_maps.json")
        self.model_file = os.path.join(TEST_OUTPUT_DIR, "test_model.keras")

        self._cleanup_files([self.train_csv_file, self.train_json_file, self.char_map_file, self.model_file])

    def tearDown(self):
        # Clean up generated files after tests
        self._cleanup_files([self.train_csv_file, self.train_json_file, self.char_map_file, self.model_file])

    def _cleanup_files(self, file_list):
        for f_path in file_list:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_data_generator_csv(self):
        print("\nRunning test_data_generator_csv...")
        data_generator.generate_dataset(
            num_samples=10,
            output_dir=TEST_OUTPUT_DIR,
            filename_prefix="test_arithmetic_train",
            file_format="csv",
            max_digits=2
        )
        self.assertTrue(os.path.exists(self.train_csv_file))
        with open(self.train_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 10)
            self.assertEqual(reader.fieldnames, ["problem", "answer"])
        print("test_data_generator_csv PASSED")

    def test_data_generator_json(self):
        print("\nRunning test_data_generator_json...")
        data_generator.generate_dataset(
            num_samples=5,
            output_dir=TEST_OUTPUT_DIR,
            filename_prefix="test_arithmetic_train", # Output will be .json
            file_format="json",
            max_digits=1
        )
        self.assertTrue(os.path.exists(self.train_json_file))
        with open(self.train_json_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 5)
            self.assertTrue("problem" in data[0])
            self.assertTrue("answer" in data[0])
        print("test_data_generator_json PASSED")

    def test_model_build_and_char_maps(self):
        print("\nRunning test_model_build_and_char_maps...")
        # Dummy data for testing structure
        dummy_problems = [{'problem': '1+1'}, {'problem': '2*3'}]
        dummy_answers = [{'answer': '2'}, {'answer': '6'}]

        char_to_token, token_to_char, n_token, max_enc, max_dec = \
            get_char_token_maps(dummy_problems, dummy_answers)

        self.assertGreater(n_token, 0)
        self.assertGreater(max_enc, 0)
        self.assertGreater(max_dec, 0)
        self.assertIn('1', char_to_token)
        self.assertIn('+', char_to_token)
        self.assertIn('\t', char_to_token) # Start token
        self.assertIn('\n', char_to_token) # End token
        self.assertIn('UNK', char_to_token)

        # Test model instantiation and build
        # Using small dimensions for quick test, no training occurs here
        model_instance = ArithmeticSeq2Seq(char_to_token, token_to_char, max_enc, max_dec, n_token, latent_dim=32, embedding_dim=16)
        # Trigger the build
        model_instance._build_inference_models()
        self.assertIsNotNone(model_instance.model)
        self.assertIsNotNone(model_instance.encoder_model)
        self.assertIsNotNone(model_instance.decoder_model)
        print("test_model_build_and_char_maps PASSED (structure check only)")

    def test_extract_arithmetic_problem(self):
        print("\nRunning test_extract_arithmetic_problem...")
        test_cases = {
            "what is 10 + 5?": "10 + 5",
            "calculate 100 / 25": "100 / 25",
            "2*3": "2 * 3", # Expects spaces
            " 5 - 1 ": "5 - 1",
            "sum of 7 and 3": None, # Current simple regex won't catch this
            "1plus1": "1 + 1" # This should ideally be caught if parser is more robust
        }
        # Current regex is basic. "1plus1" won't be parsed to "1 + 1".
        # It expects "num op num" or "num op num" within text.
        # The regex was updated to handle "1+1" -> "1 + 1"

        for query, expected in test_cases.items():
            # print(f"Testing extraction for: '{query}'")
            extracted = extract_arithmetic_problem(query)
            # print(f"Extracted: '{extracted}'")
            self.assertEqual(extracted, expected, msg=f"Failed for query: {query}")
        print("test_extract_arithmetic_problem PASSED")

    def test_math_tool_calculate_model_unavailable(self):
        print("\nRunning test_math_tool_calculate_model_unavailable...")
        # Ensure no model is "pre-loaded" by other tests or available
        # For this test, we assume the model path is invalid or model not trained
        original_model_path = os.environ.get("ARITHMETIC_MODEL_PATH_OVERRIDE", "")
        original_char_map_path = os.environ.get("ARITHMETIC_CHAR_MAP_PATH_OVERRIDE", "")

        # Point to non-existent files to ensure model load fails
        os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"] = "non_existent_model.keras"
        os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"] = "non_existent_char_map.json"

        # Need to reload math_tool for it to pick up env var for its constants
        # This is tricky in unit tests. A better way is dependency injection for paths.
        # For now, we'll test the expected error string.
        # The global _model_instance in math_tool makes this harder to isolate.
        # The most reliable way is to check the output string.

        # Simulate _load_math_model failure by checking its output
        # This test is more of an integration check on calculate's error handling

        # Temporarily rename real files if they exist to ensure load failure
        renamed_model = False
        renamed_char_map = False
        if os.path.exists(MODEL_WEIGHTS_PATH):
            os.rename(MODEL_WEIGHTS_PATH, MODEL_WEIGHTS_PATH + ".bak")
            renamed_model = True
        if os.path.exists(CHAR_MAPS_PATH):
            os.rename(CHAR_MAPS_PATH, CHAR_MAPS_PATH + ".bak")
            renamed_char_map = True

        # Reset the global model instance in math_tool for a clean test
        # This requires modifying math_tool or making _model_instance accessible for testing.
        # For now, we rely on the fact that it will try to load if _model_instance is None.
        # To truly reset: import importlib; importlib.reload(tools.math_tool)
        # This is complex for a simple test. We'll assume it tries to load.

        result = calculate_via_tool("what is 1+1?")
        self.assertIn("Error: Math model is not available.", result) # Or specific load error

        # Restore env vars and files
        if original_model_path: os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"] = original_model_path
        else: del os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"]
        if original_char_map_path: os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"] = original_char_map_path
        else: del os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"]

        if renamed_model: os.rename(MODEL_WEIGHTS_PATH + ".bak", MODEL_WEIGHTS_PATH)
        if renamed_char_map: os.rename(CHAR_MAPS_PATH + ".bak", CHAR_MAPS_PATH)

        print("test_math_tool_calculate_model_unavailable PASSED")

    def test_tool_dispatcher_math_routing(self):
        print("\nRunning test_tool_dispatcher_math_routing...")
        dispatcher = ToolDispatcher()
        # This test assumes math_tool.calculate will return the model unavailable error
        # as we are not providing a trained model.
        result = dispatcher.dispatch("calculate 2 + 2")
        self.assertIn("Error: Math model is not available.", result['payload'])

        result_explicit = dispatcher.dispatch("what is 3*3?", explicit_tool_name="calculate")
        self.assertIn("Error: Math model is not available.", result_explicit['payload'])

        result_no_tool = dispatcher.dispatch("hello world")
        self.assertIsNone(result_no_tool)
        print("test_tool_dispatcher_math_routing PASSED")

if __name__ == '__main__':
    # Create the test output directory if it doesn't exist
    # This path should be relative to where the test is run, or absolute
    # For consistency with how other paths are handled in the project:

    if not os.path.exists(TEST_OUTPUT_DIR):
        os.makedirs(TEST_OUTPUT_DIR)

    # This allows running the tests directly from this file
    # Ensure that the src directory is in sys.path if running this file directly
    # The sys.path.insert above handles this for imports within the test file.
    # If running with `python -m unittest discover`, this __main__ block is not executed.
    print(f"Current working directory: {os.getcwd()}")
    print(f"Sys.path: {sys.path}")
    print(f"Attempting to run tests for math_model...")
    unittest.main(verbosity=2)
