import unittest
import os
import json
import sys
import shutil # For cleaning up directories

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tools.logic_model import logic_data_generator
from tools.logic_model import logic_model_nn # Added this import
from tools.logic_model.logic_parser_eval import LogicParserEval
# Ensure LogicNNModel etc. are correctly imported if they are directly from logic_model_nn
from tools.logic_model.logic_model_nn import LogicNNModel, get_logic_char_token_maps, preprocess_logic_data
from tools import logic_tool # Added this import
from tools.logic_tool import evaluate_expression as evaluate_logic_via_tool
from tools.tool_dispatcher import ToolDispatcher

# Define a consistent test output directory for this test suite
TEST_DATA_GEN_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tests", "test_output_data", "logic_model_data")
TEST_MODEL_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tests", "test_output_data", "logic_model_files")


class TestLogicModelComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test output directories if they don't exist
        os.makedirs(TEST_DATA_GEN_OUTPUT_DIR, exist_ok=True)
        os.makedirs(TEST_MODEL_OUTPUT_DIR, exist_ok=True)

        # Define file paths to be used across tests
        cls.train_json_file = os.path.join(TEST_DATA_GEN_OUTPUT_DIR, "test_logic_train.json")
        cls.test_json_file = os.path.join(TEST_DATA_GEN_OUTPUT_DIR, "test_logic_test.json")
        cls.char_map_file = os.path.join(TEST_MODEL_OUTPUT_DIR, "test_logic_char_maps.json")
        cls.model_file_nn = os.path.join(TEST_MODEL_OUTPUT_DIR, "test_logic_model_nn.keras")

    @classmethod
    def tearDownClass(cls):
        # Clean up generated directories and files after all tests
        if os.path.exists(TEST_DATA_GEN_OUTPUT_DIR):
            shutil.rmtree(TEST_DATA_GEN_OUTPUT_DIR)
        if os.path.exists(TEST_MODEL_OUTPUT_DIR):
            shutil.rmtree(TEST_MODEL_OUTPUT_DIR)

    def test_01_logic_data_generator(self):
        print("\nRunning test_01_logic_data_generator...")
        dataset = logic_data_generator.generate_dataset(
            num_samples=10,
            max_nesting=1
        )
        # Now save the generated dataset to the test-specific path
        logic_data_generator.save_dataset(dataset, self.train_json_file)
        self.assertTrue(os.path.exists(self.train_json_file))
        with open(self.train_json_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 10)
            self.assertTrue("proposition" in data[0])
            self.assertTrue("answer" in data[0])
            self.assertIsInstance(data[0]["answer"], bool)
            # Check if evaluation is correct for a simple case
            for item in data:
                eval_result = logic_data_generator.evaluate_proposition(item["proposition"])
                self.assertEqual(eval_result, item["answer"], f"Proposition: {item['proposition']}")
        print("test_01_logic_data_generator PASSED")

    def test_02_logic_parser_eval(self):
        print("\nRunning test_02_logic_parser_eval...")
        evaluator = LogicParserEval()
        test_cases = [
            ("true AND false", False), ("NOT (true OR false)", False),
            ("false OR (true AND true)", True), ("(true)", True),
            ("NOT false", True), ("  true AND ( false OR true ) ", True),
            ("true AND", None), ("(true OR false", None), ("true XOR false", None)
        ]
        for expr, expected in test_cases:
            self.assertEqual(evaluator.evaluate(expr), expected, f"Failed for: {expr}")
        print("test_02_logic_parser_eval PASSED")

    def test_03_logic_model_nn_structure_and_helpers(self):
        print("\nRunning test_03_logic_model_nn_structure_and_helpers...")
        # Create a dummy dataset file for char_map generation
        dummy_data = [{"proposition": "true AND false", "answer": False}]
        with open(self.train_json_file, 'w') as f: # Use the class defined path
            json.dump(dummy_data, f)

        # Override CHAR_MAP_SAVE_PATH for logic_model_nn functions for this test
        original_char_map_path = logic_model_nn.CHAR_MAP_SAVE_PATH
        logic_model_nn.CHAR_MAP_SAVE_PATH = self.char_map_file

        char_to_token, _, vocab_size, max_len = get_logic_char_token_maps(self.train_json_file)
        self.assertGreater(vocab_size, 0)
        self.assertGreater(max_len, 0)
        # Check for individual characters from "true AND false" (dummy_data)
        self.assertIn("t", char_to_token)
        self.assertIn("r", char_to_token)
        self.assertIn("u", char_to_token)
        self.assertIn("e", char_to_token)
        self.assertIn("a", char_to_token) # from 'false' and 'AND'
        self.assertIn("N", char_to_token) # from 'AND' (corrected from 'n')
        self.assertIn("D", char_to_token) # from 'AND' (corrected from 'd')
        self.assertIn("f", char_to_token)
        self.assertIn("l", char_to_token)
        self.assertIn("s", char_to_token)
        self.assertIn(" ", char_to_token)
        self.assertIn("<PAD>", char_to_token)

        X, y = preprocess_logic_data(self.train_json_file, char_to_token, max_len, num_classes=2)
        self.assertEqual(X.shape[0], len(dummy_data))
        self.assertEqual(y.shape[0], len(dummy_data))
        self.assertEqual(y.shape[1], 2) # Categorical

        model_instance = LogicNNModel(max_seq_len=max_len, vocab_size=vocab_size, embedding_dim=8, lstm_units=16)
        self.assertIsNotNone(model_instance.model)

        # Test predict path (on untrained model)
        pred_result = model_instance.predict("true OR false", char_to_token)
        self.assertIsInstance(pred_result, bool) # Should return a bool, even if random

        # Test save and load (structural, not functional correctness of loaded model)
        model_instance.save_model(self.model_file_nn)
        self.assertTrue(os.path.exists(self.model_file_nn))

        loaded_model_instance = LogicNNModel.load_model(self.model_file_nn, self.char_map_file)
        self.assertIsNotNone(loaded_model_instance)
        self.assertIsNotNone(loaded_model_instance.model)

        logic_model_nn.CHAR_MAP_SAVE_PATH = original_char_map_path # Restore
        print("test_03_logic_model_nn_structure_and_helpers PASSED")

    def test_04_logic_tool_interface(self):
        print("\nRunning test_04_logic_tool_interface...")
        # Parser method (should work)
        result_parser = evaluate_logic_via_tool("true AND (NOT false)", method='parser')
        self.assertEqual(result_parser, True) # "Result: True" string is not correct here, it returns bool

        # NN method (will likely fail if model not trained/available, or return error string)
        # Ensure CHAR_MAP_SAVE_PATH in logic_tool points to our test one for this test
        original_lt_char_map_path = logic_tool.CHAR_MAP_LOAD_PATH
        logic_tool.CHAR_MAP_LOAD_PATH = self.char_map_file # From test_03

        # Ensure a dummy char_map exists for the NN path to not fail on file load
        if not os.path.exists(self.char_map_file):
             char_to_token, _, vocab_size, max_len = get_logic_char_token_maps(self.train_json_file) # uses self.train_json_file

        result_nn = evaluate_logic_via_tool("true OR false", method='nn')
        # Expected: "Error: NN model not available..." OR a boolean if dummy model loads
        self.assertTrue(isinstance(result_nn, str) or isinstance(result_nn, bool))
        if isinstance(result_nn, str):
            self.assertIn("Error: NN model not available", result_nn)

        logic_tool.CHAR_MAP_LOAD_PATH = original_lt_char_map_path # Restore
        print("test_04_logic_tool_interface PASSED")

    def test_05_tool_dispatcher_logic_routing(self):
        print("\nRunning test_05_tool_dispatcher_logic_routing...")
        dispatcher = ToolDispatcher()

        # Test parser routing
        result_parser = dispatcher.dispatch("evaluate true AND false")
        self.assertEqual(result_parser['payload'], False)

        result_parser_implicit = dispatcher.dispatch("NOT (true OR false)")
        self.assertEqual(result_parser_implicit['payload'], False)

        # Test NN routing (will also likely hit "NN model not available")
        # Ensure char_map file is available for _get_nn_model_evaluator in logic_tool
        original_lt_char_map_path = logic_tool.CHAR_MAP_LOAD_PATH
        logic_tool.CHAR_MAP_LOAD_PATH = self.char_map_file
        if not os.path.exists(self.char_map_file): # If test_03 didn't run or cleaned up
             char_to_token, _, vocab_size, max_len = get_logic_char_token_maps(self.train_json_file)

        result_nn = dispatcher.dispatch("evaluate true OR false using nn")
        # Based on current LLMInterface mock, "evaluate true OR false using nn"
        # will result in NO_TOOL from DLM, so dispatcher returns None.
        self.assertIsNone(result_nn, f"Expected dispatcher to return None for 'evaluate...using nn' due to current LLM mock, but got {result_nn}")

        logic_tool.CHAR_MAP_LOAD_PATH = original_lt_char_map_path # Restore
        print("test_05_tool_dispatcher_logic_routing PASSED")

if __name__ == '__main__':
    # This allows running tests with `python -m unittest path/to/test_logic_model.py`
    # or directly `python path/to/test_logic_model.py`

    # Need to modify logic_data_generator to accept output_dir and filenames for testing
    # Monkey patch generate_dataset for testing if needed, or ensure it handles flexible paths
    def PatchedGenerateDataset(num_samples, max_nesting, output_dir_override, train_filename_override, test_filename_override):
        # This is a simplified patch for the test.
        # In real scenario, logic_data_generator.py should be importable and its functions callable with parameters.
        print(f"PatchedGenerateDataset called: num_samples={num_samples}, output_dir={output_dir_override}")
        train_path = os.path.join(output_dir_override, train_filename_override)
        # test_path = os.path.join(output_dir_override, test_filename_override) # Not used in test_01

        dataset = []
        for _ in range(num_samples):
            prop = logic_data_generator.generate_simple_proposition(max_nesting=max_nesting)
            answer = logic_data_generator.evaluate_proposition(prop)
            if answer is not None:
                dataset.append({"proposition": prop, "answer": bool(answer)})

        os.makedirs(output_dir_override, exist_ok=True)
        with open(train_path, 'w') as f:
            json.dump(dataset, f)
        # with open(test_path, 'w') as f: # If test_logic_test.json is also needed by a test
        #     json.dump(dataset, f)

    logic_data_generator.generate_dataset = PatchedGenerateDataset

    # Also patch where logic_model_nn saves its char_maps for consistency in tests
    logic_model_nn.CHAR_MAP_SAVE_PATH = TestLogicModelComponents.char_map_file
    logic_tool.CHAR_MAP_LOAD_PATH = TestLogicModelComponents.char_map_file
    logic_tool.MODEL_LOAD_PATH = TestLogicModelComponents.model_file_nn


    print(f"Logic Model Test: Current working directory: {os.getcwd()}")
    print(f"Logic Model Test: Sys.path: {sys.path}")
    print(f"Logic Model Test: Test data output directory: {TEST_DATA_GEN_OUTPUT_DIR}")
    print(f"Logic Model Test: Test model file directory: {TEST_MODEL_OUTPUT_DIR}")

    unittest.main(verbosity=2)
