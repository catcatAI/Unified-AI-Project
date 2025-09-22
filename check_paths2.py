import os
import sys

# Replicate the same logic as in the test file
test_file_path = r'D:\Projects\Unified-AI-Project\apps\backend\tests\integration\test_end_to_end_project_flow.py'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(test_file_path), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

print(f"test_file_path: {test_file_path}")
print(f"os.path.dirname(test_file_path): {os.path.dirname(test_file_path)}")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"SRC_DIR: {SRC_DIR}")
print(f"PROJECT_ROOT.replace: {PROJECT_ROOT.replace(chr(92), chr(92)+chr(92))}")  # Using chr(92) for backslash