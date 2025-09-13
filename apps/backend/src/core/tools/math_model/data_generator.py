import random
import csv
import json
import os # Added os module
from pathlib import Path


def _atomic_write_text(path: Path, content: str) -> None:\n    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    os.replace(tmp, path)


def generate_problem(max_digits=3, operations=None):
    """Generates a random arithmetic problem."""
    if operations is None:
        operations = ['+', '-', '*', '/']

    num1 = random.randint(0, 10**max_digits - 1)
    num2 = random.randint(1, 10**max_digits - 1) # Avoid division by zero for /
    operation = random.choice(operations)

    if operation == '/' and num2 == 0:
        num2 = 1 # Ensure divisor is not zero

    problem_str = f"{num1} {operation} {num2}"

    try:
        answer = eval(problem_str)
        if operation == '/':
            answer = round(answer, 4)
        else:
            answer = int(answer)

    except ZeroDivisionError:
        return generate_problem(max_digits, operations)
    except Exception:
        return generate_problem(max_digits, operations)

    return problem_str, answer


def generate_dataset(num_samples, output_dir, filename_prefix="arithmetic", file_format="csv", max_digits=3):
    """Generates a dataset of arithmetic problems and saves it."""
    problems = []
    for _ in range(num_samples):
        problem, answer = generate_problem(max_digits=max_digits)
        problems.append({"problem": problem, "answer": str(answer)})

    os.makedirs(output_dir, exist_ok=True)

    if file_format == "csv":
        filepath = Path(output_dir) / f"{filename_prefix}.csv"
        tmp = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["problem", "answer"])
            writer.writeheader()
            writer.writerows(problems)
        os.replace(tmp, filepath)
        print(f"Generated {num_samples} samples in {filepath}")
    elif file_format == "json":
        filepath = Path(output_dir) / f"{filename_prefix}.json"
        json_text = json.dumps(problems, indent=2)
        _atomic_write_text(filepath, json_text)
        print(f"Generated {num_samples} samples in {filepath}")
    else:
        print(f"Unsupported file format: {file_format}")


if __name__ == "__main__":
    num_train_samples = 10000
    num_test_samples = 2000
    
    # Resolve project root robustly by walking up until repo markers are found
    script_dir = Path(__file__).resolve().parent

    def _find_project_root(start: Path) -> Path:
        # Identify repository root by presence of typical top-level dirs
        for p in [start] + list(start.parents):
            if (p / "apps").exists() and (p / "training").exists():
                return p
        # Fallback to highest parent
        return start.parents[-1]

    project_root = _find_project_root(script_dir)
    output_directory = str(project_root / "data" / "raw_datasets")

    # Generate training data as JSON (for train.py)
    generate_dataset(num_train_samples,
                     output_dir=output_directory,
                     filename_prefix="arithmetic_train_dataset",
                     file_format="json", # Changed to JSON for training
                     max_digits=3)

    # Generate testing data as CSV (as originally planned, can be used by evaluate.py or manual inspection)
    generate_dataset(num_test_samples,
                     output_dir=output_directory,
                     filename_prefix="arithmetic_test_dataset",
                     file_format="csv",
                     max_digits=3)

    print("Sample data generation script execution finished.")
