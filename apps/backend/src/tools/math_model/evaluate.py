import json
import csv
import sys
import os
from typing import Tuple, Optional, List, Dict, Any

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 修复相对导入
sys.path.append(os.path.join(SCRIPT_DIR))
try:
    # 使用完整模块路径
    from apps.backend.src.core.tools.math_model.model import ArithmeticSeq2Seq
except ImportError as e:
    print(f"Error importing from model: {e}")
    sys.exit(1)

# --- Configuration ---
TEST_DATASET_PATH = "data/raw_datasets/arithmetic_test_dataset.csv"
MODEL_LOAD_PATH = "data/models/arithmetic_model.keras"
CHAR_MAP_LOAD_PATH = "data/models/arithmetic_char_maps.json"

def load_char_maps(file_path) -> Optional[Tuple[Dict[str, int], Dict[int, str], int, int, int]]:
    """Loads character token maps from a JSON file."""
    try:

    with open(file_path, 'r', encoding='utf-8') as f:
    char_map_data = json.load(f)
    return (
            char_map_data['char_to_token'],
            char_map_data['token_to_char'],
            char_map_data['n_token'],
            char_map_data['max_encoder_seq_length'],
            char_map_data['max_decoder_seq_length']
    )
    except FileNotFoundError:

    print(f"Error: Character map file not found at {file_path}")
    return None
    except json.JSONDecodeError:

    print(f"Error: Could not decode JSON from {file_path}")
    return None

def load_test_dataset_csv(file_path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Loads test dataset from a CSV file."""
    problems: List[Dict[str, str]] =   # 修复列表初始化
    answers: List[Dict[str, str]] =    # 修复列表初始化
    try:

    with open(file_path, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
            for row in reader:

    problems.append({'problem': row['problem']})
                answers.append({'answer': row['answer']})
    except FileNotFoundError:

    print(f"Error: Test dataset file not found at {file_path}")
    print("Please generate the dataset first using data_generator.py")
    except Exception as e:

    print(f"Error loading CSV: {e}")
    return problems, answers  # 总是返回列表

def main -> None:  # 修复函数定义，添加缺失的括号
    print("Starting evaluation process...")

    # 1. Load character maps
    print(f"Loading character maps from {CHAR_MAP_LOAD_PATH}...")
    maps_data = load_char_maps(CHAR_MAP_LOAD_PATH)
    if maps_data is None:

    return
    char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length = maps_data

    # 2. Load the trained model
    print(f"Loading trained model from {MODEL_LOAD_PATH}...")
    try:
    # Re-build the model architecture first
    # Note Latent_dim and embedding_dim should ideally be saved with char_maps or model config
    # For now, using the same values as in train.py; consider refactoring this.
    latent_dim = 256
    embedding_dim = 128

    math_model_shell = ArithmeticSeq2Seq(
            char_to_token, token_to_char,
            max_encoder_seq_length, max_decoder_seq_length,
            n_token, latent_dim, embedding_dim
    )
    # 修复模型构建方式
    math_model_shell._build_inference_models  # 使用正确的模型构建方法
    # 修复模型加载方式
        if math_model_shell.model is not None:

    math_model_shell.model.load_weights(MODEL_LOAD_PATH) # Load weights into the training model structure

    # The inference models (encoder_model, decoder_model) inside math_model_shell
    # should now have the trained weights because they share layers with math_model_shell.model
    print("Model loaded successfully.")
    except Exception as e:

    print(f"Error loading model: {e}")
    print(f"Ensure that the model was saved correctly at {MODEL_LOAD_PATH} after training.")
    return

    # 3. Load test data
    print(f"Loading test dataset from {TEST_DATASET_PATH}...")
    test_problems, test_answers = load_test_dataset_csv(TEST_DATASET_PATH)
    # 移除None检查，因为我们现在总是返回列表
    print(f"Loaded {len(test_problems)} test samples.")

    # 4. Evaluate the model
    correct_predictions = 0
    num_samples_to_show = 5

    print(f"\n--- Evaluating {len(test_problems)} samples ---")
    for i in range(len(test_problems)):

    input_problem_str = test_problems[i]['problem']
    expected_answer_str = test_answers[i]['answer']

    predicted_answer_str = math_model_shell.predict_sequence(input_problem_str)

        if i < num_samples_to_show:


    print(f"Problem: \"{input_problem_str}\"")
            print(f"Expected: \"{expected_answer_str}\", Got: \"{predicted_answer_str}\"")

        # Normalize answers for comparison (e.g. "2.0" vs "2")
    try:

        if float(predicted_answer_str) == float(expected_answer_str)


    correct_predictions += 1
                if i < num_samples_to_show: print("Result: CORRECT")
            else:

                if i < num_samples_to_show: print("Result: INCORRECT")
        except ValueError: # If conversion to float fails (e.g. empty or malformed prediction)
            if predicted_answer_str == expected_answer_str: # Handles cases like empty string if that's valid

    correct_predictions += 1
                 if i < num_samples_to_show: print("Result: CORRECT (non-numeric match)")
            else:

                if i < num_samples_to_show: print("Result: INCORRECT (prediction not a number)")
        if i < num_samples_to_show: print("---")


    accuracy = (correct_predictions / len(test_problems)) * 100
    print(f"\nEvaluation Complete.")
    print(f"Total test samples: {len(test_problems)}")
    print(f"Correct predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.2f}%")

if __name__ == '__main__':
    # 修复文件检查方式
    if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH)

    print("Model file or character map file not found.")
    print(f"Ensure '{MODEL_LOAD_PATH}' and '{CHAR_MAP_LOAD_PATH}' exist.")
    print("Please train the model first using train.py.")
    elif not os.path.exists(TEST_DATASET_PATH)

    print(f"Test dataset not found at {TEST_DATASET_PATH}.")
    print("Please run `python src/tools/math_model/data_generator.py` to generate the test dataset (CSV format).")
    else:

    main  # 修复函数调用，添加缺失的括号