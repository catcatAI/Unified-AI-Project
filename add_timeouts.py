import os
import re

def add_timeout_to_tests(directory="tests"):
    print(f"Starting to add timeouts in {directory}")
    filepath = "tests/core_ai/test_crisis_system.py"
    print(f"Processing {filepath}")
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("def test_"):
            new_lines.append("@pytest.mark.timeout(60)\n")
        new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print("Finished adding timeouts.")

if __name__ == "__main__":
    add_timeout_to_tests()
