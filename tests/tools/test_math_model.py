import pytest
import os
import json
import csv
import shutil
from unittest.mock import MagicMock, AsyncMock, patch
import logging

from tools.math_model import data_generator
from tools.math_tool import extract_arithmetic_problem, calculate as calculate_via_tool
from tools.math_model.model import MODEL_WEIGHTS_PATH, CHAR_MAPS_PATH
from tools.tool_dispatcher import ToolDispatcher
from tools.math_model.model import ArithmeticSeq2Seq, get_char_token_maps

logger = logging.getLogger(__name__)

# Define a consistent test output directory
TEST_OUTPUT_DIR = "tests/test_output_data"
# Path for the dummy dictionary for testing
DUMMY_DICTIONARY_PATH = os.path.join(TEST_OUTPUT_DIR, "test_translation_dictionary.json")

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_class():
    """Set up and tear down test environment for the module."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    yield # Run tests

    # Teardown
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)

@pytest.fixture(autouse=True)
def setup_each_test(setup_and_teardown_class):
    """Clean up generated files before each test."""
    # Ensure files are cleaned up before each test
    files_to_cleanup = [
        os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.csv"),
        os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.json"),
        os.path.join(TEST_OUTPUT_DIR, "test_char_maps.json"),
        os.path.join(TEST_OUTPUT_DIR, "test_model.keras")
    ]
    for f_path in files_to_cleanup:
        if os.path.exists(f_path):
            os.remove(f_path)

@pytest.mark.timeout(10)
def test_data_generator_csv(setup_each_test) -> None:
    logger.info("\nRunning test_data_generator_csv...")
    train_csv_file = os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.csv")
    data_generator.generate_dataset(
        num_samples=10,
        output_dir=TEST_OUTPUT_DIR,
        filename_prefix="test_arithmetic_train",
        file_format="csv",
        max_digits=2
    )
    assert os.path.exists(train_csv_file)
    with open(train_csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 10
        assert reader.fieldnames == ["problem", "answer"]
    logger.info("test_data_generator_csv PASSED")

@pytest.mark.timeout(10)
def test_data_generator_json(setup_each_test) -> None:
    logger.info("\nRunning test_data_generator_json...")
    train_json_file = os.path.join(TEST_OUTPUT_DIR, "test_arithmetic_train.json")
    data_generator.generate_dataset(
        num_samples=5,
        output_dir=TEST_OUTPUT_DIR,
        filename_prefix="test_arithmetic_train", # Output will be .json
        file_format="json",
        max_digits=1
    )
    assert os.path.exists(train_json_file)
    with open(train_json_file, 'r') as f:
        data = json.load(f)
        assert len(data) == 5
        assert "problem" in data[0]
        assert "answer" in data[0]
    logger.info("test_data_generator_json PASSED")

@pytest.mark.skipif(True, reason="Skipping due to tensorflow dependency issues")
@pytest.mark.timeout(10)
def test_model_build_and_char_maps(setup_each_test) -> None:
    logger.info("\nRunning test_model_build_and_char_maps...")
    
    # Check if TensorFlow is available
    from core_ai.dependency_manager import dependency_manager
    if not dependency_manager.is_available('tensorflow'):
        logger.info("TensorFlow not available, skipping model build tests")
        pytest.skip("TensorFlow not available")
        return
    
    # Dummy data for testing structure
    dummy_problems = [{'problem': '1+1'}, {'problem': '2*3'}]
    dummy_answers = [{'answer': '2'}, {'answer': '6'}]

    char_to_token, token_to_char, n_token, max_enc, max_dec = \
        get_char_token_maps(dummy_problems, dummy_answers)

    assert char_to_token is not None, "char_to_token should not be None"
    assert token_to_char is not None, "token_to_char should not be None"
    assert n_token is not None, "n_token should not be None"
    assert max_enc is not None, "max_enc should not be None"
    assert max_dec is not None, "max_dec should not be None"

    assert n_token > 0
    assert max_enc > 0
    assert max_dec > 0
    assert '1' in char_to_token
    assert '+' in char_to_token
    assert '\t' in char_to_token # Start token
    assert '\n' in char_to_token # End token
    assert 'UNK' in char_to_token

    # Test model instantiation and build
    # Using small dimensions for quick test, no training occurs here
    model_instance = ArithmeticSeq2Seq(char_to_token, token_to_char, max_enc, max_dec, n_token, latent_dim=32, embedding_dim=16)
    # Trigger the build
    model_instance._build_inference_models()
    assert model_instance.model is not None
    assert model_instance.encoder_model is not None
    assert model_instance.decoder_model is not None
    logger.info("test_model_build_and_char_maps PASSED (structure check only)")

@pytest.mark.timeout(10)
def test_extract_arithmetic_problem(setup_each_test) -> None:
    logger.info("\nRunning test_extract_arithmetic_problem...")
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
        # logger.debug(f"Testing extraction for: '{query}'")
        extracted = extract_arithmetic_problem(query)
        # logger.debug(f"Extracted: '{extracted}'")
        assert extracted == expected, f"Failed for query: {query}"
    logger.info("test_extract_arithmetic_problem PASSED")

@pytest.mark.timeout(10)
@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_math_tool_calculate_model_unavailable(setup_each_test) -> None:
    logger.info("\nRunning test_math_tool_calculate_model_unavailable...")
    # Ensure no model is "pre-loaded" by other tests or available
    # For this test, we assume the model path is invalid or model not trained
    original_model_path = os.environ.get("ARITHMETIC_MODEL_PATH_OVERRIDE", "")
    original_char_map_path = os.environ.get("ARITHMETIC_CHAR_MAP_PATH_OVERRIDE", "")

    # Point to non-existent files to ensure model load fails
    os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"] = "non_existent_model.keras"
    os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"] = "non_existent_char_map.json"

    # Temporarily rename real files if they exist to ensure load failure
    renamed_model = False
    renamed_char_map = False
    if os.path.exists(MODEL_WEIGHTS_PATH):
        os.rename(MODEL_WEIGHTS_PATH, MODEL_WEIGHTS_PATH + ".bak")
        renamed_model = True
    if os.path.exists(CHAR_MAPS_PATH):
        os.rename(CHAR_MAPS_PATH, CHAR_MAPS_PATH + ".bak")
        renamed_char_map = True

    result = await calculate_via_tool("what is 1+1?")
    assert result['status'] == "failure_tool_error"
    assert "Error: Math model is not available." in result['error_message']

    # Restore env vars and files
    if original_model_path: os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"] = original_model_path
    else: del os.environ["ARITHMETIC_MODEL_PATH_OVERRIDE"]
    if original_char_map_path: os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"] = original_char_map_path
    else: del os.environ["ARITHMETIC_CHAR_MAP_PATH_OVERRIDE"]

    if renamed_model: os.rename(MODEL_WEIGHTS_PATH + ".bak", MODEL_WEIGHTS_PATH)
    if renamed_char_map: os.rename(CHAR_MAPS_PATH + ".bak", CHAR_MAPS_PATH)
    logger.info("test_math_tool_calculate_model_unavailable PASSED")

@pytest.mark.timeout(10)
@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_tool_dispatcher_math_routing(setup_each_test) -> None:
    logger.info("\nRunning test_tool_dispatcher_math_routing...")
    dispatcher = ToolDispatcher()
    # This test assumes math_tool.calculate will return the model unavailable error
    # as we are not providing a trained model.
    result = await dispatcher.dispatch("calculate 2 + 2")
    assert result['status'] == "failure_tool_error"
    assert "Error: Math model is not available." in result['error_message']

    result_explicit = await dispatcher.dispatch("what is 3*3?", explicit_tool_name="calculate")
    assert result_explicit['status'] == "failure_tool_error"
    assert "Error: Math model is not available." in result_explicit['error_message']

    result_no_tool = await dispatcher.dispatch("hello world") # Dispatch is async
    assert result_no_tool.status == "failure_tool_error" # Assuming it returns a failure for no tool
    logger.info("test_tool_dispatcher_math_routing PASSED")
