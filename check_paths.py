import os
import sys

# Replicate the same logic as in the test file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"SRC_DIR: {SRC_DIR}")
print(f"PROJECT_ROOT.replace: {PROJECT_ROOT.replace(chr(92), chr(92)+chr(92))}")  # Using chr(92) for backslash