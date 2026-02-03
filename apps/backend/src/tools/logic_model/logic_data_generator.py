"""
This script generates a dataset of logical propositions and their evaluated results.
"""

# from tests.test_json_fix import
# TODO: Fix import - module 'random' not found
# from diagnose_base_agent import
# from unified_auto_fix_system.utils.ast_analyzer import
import os
from typing import Optional, List, Dict, Any

# Define output directory and filenames relative to the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
OUTPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_datasets")

TRAIN_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_train.json")
TEST_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_test.json")

OPERATORS = ["AND", "OR"]
UNARY_OPERATORS = ["NOT"]
VALUES = ["true", "false"]


def generate_simple_proposition(max_nesting: int = 1, current_nesting: int = 0) -> str:
    """Generates a simple logical proposition recursively."""
    if current_nesting >= max_nesting or random.random() < 0.4:
        if random.random() < 0.3 and current_nesting < max_nesting:
            return f"NOT {generate_simple_proposition(max_nesting,
    current_nesting + 1)}"
        else:
            return random.choice(VALUES)
    else:
        op = random.choice(OPERATORS)
        left = generate_simple_proposition(max_nesting, current_nesting + 1)
        right = generate_simple_proposition(max_nesting, current_nesting + 1)

        use_parens_left = random.choice([True, False]) and ("AND" in left or "OR" in left)
        use_parens_right = random.choice([True, False]) and ("AND" in right or "OR" in right)

        left_expr = f"({left})" if use_parens_left else left
        right_expr = f"({right})" if use_parens_right else right
        return f"{left_expr} {op} {right_expr}"

def evaluate_proposition(prop_str: str) -> Optional[bool]:
    """Safely evaluates a logical proposition string using Python's AST."""
    try:
        # Normalize string for safe evaluation
        normalized_str = prop_str.lower().replace("true", "True").replace("false",
    "False")
        
        # Whitelist of allowed nodes
        allowed_nodes = {
            ast.Expression,
            ast.Constant,      # For Python 3.8+
            ast.NameConstant,  # For Python < 3.8
            ast.BoolOp,
            ast.And,
            ast.Or,
            ast.UnaryOp,
            ast.Not
        }

        tree = ast.parse(normalized_str, mode = 'eval')

        for node in ast.walk(tree):
            if type(node) not in allowed_nodes:
                raise ValueError(f"Unsupported operation or node type: {type(node)}")

        # If parsing and validation pass, use Python's eval on the normalized string.
        # This is safe because we've validated the AST structure.
        return bool(eval(compile(tree, filename = " < string > ", mode = "eval")))

    except (SyntaxError, ValueError, TypeError) as e:
        # print(f"Could not evaluate '{prop_str}' - Error: {e}")
        return None

def generate_dataset(num_samples: int, max_nesting: int = 2) -> List[Dict[str, Any]]:
    """Generates a dataset of logical propositions and their answers."""
    dataset: List[Dict[str, Any]] = []
    generated_propositions = set()

    while len(dataset) < num_samples:
        prop = generate_simple_proposition(max_nesting = max_nesting)
        if prop in generated_propositions:
            continue

        answer = evaluate_proposition(prop)

        if answer is not None:
            dataset.append({"proposition": prop, "answer": answer})
            generated_propositions.add(prop)
            if len(dataset) % (num_samples // 10 if num_samples >= 10 else 1) == 0:
                print(f"Generated {len(dataset)} / {num_samples} samples...")

    return dataset

def save_dataset(dataset: List[Dict[str, Any]], file_path: str):
    """Saves the dataset to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok = True)
    with open(file_path, 'w', encoding = 'utf - 8') as f:
        json.dump(dataset, f, indent = 2)
    print(f"Dataset saved to {file_path}")