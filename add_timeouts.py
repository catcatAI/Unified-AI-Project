import os
import re

def add_timeout_to_tests(directory="tests"):
    filepath = "tests/core_ai/test_crisis_system.py"
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith("def test_"):
            # Check if the previous line already has a timeout decorator
            if i > 0 and "@pytest.mark.timeout" in lines[i-1]:
                pass
            else:
                new_lines.append("@pytest.mark.timeout(60)\n")
        new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    add_timeout_to_tests()
