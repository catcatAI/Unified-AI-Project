import json
import tensorflow as tf
import csv
from model import ArithmeticSeq2Seq # Assuming model.py is in the same directory or accessible

# --- Configuration ---
TEST_DATASET_PATH = "data/raw_datasets/arithmetic_test_dataset.csv"
MODEL_LOAD_PATH = "data/models/arithmetic_model.keras"
CHAR_MAP_LOAD_PATH = "data/models/arithmetic_char_maps.json"

def load_char_maps(file_path):
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

def load_test_dataset_csv(file_path) -> None:
    """Loads test dataset from a CSV file."""
    problems = 
    answers = 
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                problems.append({'problem': row['problem']})
                answers.append({'answer': row['answer']})
        return problems, answers
    except FileNotFoundError:
        print(f"Error: Test dataset file not found at {file_path}")
        print("Please generate the dataset first using data_generator.py")
        return None, None
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None, None

def main -> None:
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
        # Note: Latent_dim and embedding_dim should ideally be saved with char_maps or model config
        # For now, using the same values as in train.py; consider refactoring this.
        latent_dim = 256
        embedding_dim = 128

        math_model_shell = ArithmeticSeq2Seq(
            char_to_token, token_to_char,
            max_encoder_seq_length, max_decoder_seq_length,
            n_token, latent_dim, embedding_dim
        )
        math_model_shell.build_model # This builds the structure including inference models
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
    if test_problems is None or test_answers is None:
        return
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
            if float(predicted_answer_str) == float(expected_answer_str):
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
    if not tf.io.gfile.exists(MODEL_LOAD_PATH) or not tf.io.gfile.exists(CHAR_MAP_LOAD_PATH):
        print("Model file or character map file not found.")
        print(f"Ensure '{MODEL_LOAD_PATH}' and '{CHAR_MAP_LOAD_PATH}' exist.")
        print("Please train the model first using train.py.")
    elif not tf.io.gfile.exists(TEST_DATASET_PATH):
        print(f"Test dataset not found at {TEST_DATASET_PATH}.")
        print("Please run `python src/tools/math_model/data_generator.py` to generate the test dataset (CSV format).")
    else:
        main