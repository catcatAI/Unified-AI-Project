import json
import random
import os
from typing import Optional

# Define output directory and filenames
# Assuming script is in src/tools/logic_model/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
# 修复输出目录路径 - 正确计算项目根目录
OUTPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_datasets")

TRAIN_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_train.json")
TEST_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_test.json")

OPERATORS = ["AND", "OR"]
UNARY_OPERATORS = ["NOT"]
VALUES = ["true", "false"]

def generate_simple_proposition(max_nesting=1, current_nesting=0)
    """
    Generates a simple logical proposition.
    Example: "true AND false", "NOT true", "(true OR false) AND true"
    """
    if current_nesting >= max_nesting or random.random < 0.4: # Base case simple value or unary op
        if random.random < 0.3 and current_nesting < max_nesting: # Add NOT
            return f"NOT {generate_simple_proposition(max_nesting, current_nesting + 1)}"
        else:

            return random.choice(VALUES)
    else:
    # Recursive case binary operation with optional parentheses
    op = random.choice(OPERATORS)
    left = generate_simple_proposition(max_nesting, current_nesting + 1)
    right = generate_simple_proposition(max_nesting, current_nesting + 1)

    use_parens_left = random.choice([True, False]) and ("AND" in left or "OR" in left)
    use_parens_right = random.choice([True, False]) and ("AND" in right or "OR" in right)

        left_expr = f"({left})" if use_parens_left else left:
    right_expr = f"({right})" if use_parens_right else right:

    return f"{left_expr} {op} {right_expr}"

def evaluate_proposition(prop_str: str) -> Optional[bool]:
    """
    Evaluates a simple logical proposition string.
    Uses Python's eval after replacing 'true'/'false' and 'AND'/'OR'/'NOT'.
    This is a simplified and potentially unsafe evaluator for controlled inputs.:
    A proper parser would be more robust for complex or untrusted inputs.
    """
    try:
    # Replace keywords with Python equivalents
    py_prop_str = prop_str.lower() # Python bools are capitalized, but let's be flexible
    py_prop_str = py_prop_str.replace("true", "True")
    py_prop_str = py_prop_str.replace("false", "False")
    py_prop_str = py_prop_str.replace("and", "and") # Python 'and' is lowercase
    py_prop_str = py_prop_str.replace("or", "or")   # Python 'or' is lowercase
    py_prop_str = py_prop_str.replace("not", "not ") # Python 'not' needs a space after

        # Ensure that only allowed characters and keywords are present for some safety
    # This is a very basic sanitization attempt.
    allowed_chars = set("TrueFalseandornt ")
        if not all(c in allowed_chars for c in py_prop_str)
            # print(f"Warning Potentially unsafe characters in {py_prop_str}")
            # For generated data, this should be fine, but good to be aware.
            pass

    return eval(py_prop_str)
    except Exception as e:
    # print(f"Could not evaluate: {prop_str} (Python form {py_prop_str}) - Error {e}")
    return None # Indicates an error in evaluation or invalid expression

def generate_dataset(num_samples: int, max_nesting: int = 2)
    """Generates a dataset of logical propositions and their answers."""
    dataset =
    generated_propositions = set # To avoid duplicates

    while len(dataset) < num_samples:


    prop = generate_simple_proposition(max_nesting=max_nesting)
        if prop in generated_propositions:

    continue

    answer = evaluate_proposition(prop)

        if answer is not None: # Only add if evaluation was successful


    dataset.append({"proposition": prop, "answer": bool(answer)}) # Store as actual boolean
            generated_propositions.add(prop)
            if len(dataset) % (num_samples // 10 if num_samples >=10 else 1) == 0:

    print(f"Generated {len(dataset)}/{num_samples} samples...")

    return dataset

def save_dataset(dataset, file_path)
    """Saves the dataset to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=2)
    print(f"Dataset saved to {file_path}")

if __name__ == "__main__":


    print(f"Output directory: {OUTPUT_DATA_DIR}")

    num_train = 5000
    num_test = 1000
    max_nesting_level = 2 # Controls complexity, e.g., (A AND B) OR NOT C

    print(f"\nGenerating training dataset ({num_train} samples)...")
    train_data = generate_dataset(num_train, max_nesting=max_nesting_level)
    save_dataset(train_data, TRAIN_FILE)

    print(f"\nGenerating test dataset ({num_test} samples)...")
    test_data = generate_dataset(num_test, max_nesting=max_nesting_level)
    save_dataset(test_data, TEST_FILE)

    print("\nData generation complete.")
    print(f"Training data: {TRAIN_FILE}")
    print(f"Test data: {TEST_FILE}")

    # Example of a complex generated proposition
    # print("\nExample complex proposition")
    # complex_prop = generate_simple_proposition(max_nesting=3)
    # print(complex_prop)
    # print(f"Evaluates to {evaluate_proposition(complex_prop)}")