#!/bin/bash
# scripts/generate_requirements.sh

# This script generates the requirements.txt and requirements-dev.txt files
# from the single source of truth: apps/backend/pyproject.toml.
# This ensures that the dependency files are always in sync with the project definition.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Generating Python requirements files from pyproject.toml ---"

# Define the path to the backend directory relative to the script location
BACKEND_DIR="$(dirname "$0")/../apps/backend"

# --- Generate requirements.txt (for production) ---
echo "\n[1/2] Generating requirements.txt for production..."
pip-compile \
    --resolver=backtracking \
    --output-file="$BACKEND_DIR/requirements.txt" \
    "$BACKEND_DIR/pyproject.toml"
echo "SUCCESS: requirements.txt has been generated."

# --- Generate requirements-dev.txt (for development and testing) ---
echo "\n[2/2] Generating requirements-dev.txt for development..."
pip-compile \
    --resolver=backtracking \
    --extra=testing \
    --output-file="$BACKEND_DIR/requirements-dev.txt" \
    "$BACKEND_DIR/pyproject.toml"
echo "SUCCESS: requirements-dev.txt has been generated."

# Add pip-tools to the dev requirements manually since it's needed to run this script
# but isn't part of the project's own dependencies.
echo "\n# --- Build/Dependency Tools ---" >> "$BACKEND_DIR/requirements-dev.txt"
echo "pip-tools" >> "$BACKEND_DIR/requirements-dev.txt"
echo "Added pip-tools to requirements-dev.txt"


echo "\n--- Requirement file generation complete. ---"
echo "Please review the generated files and commit them to version control."
