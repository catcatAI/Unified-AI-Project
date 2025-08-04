#!/bin/bash
# scripts/run_backend_tests.sh

# This script provides a reliable way to run the backend Python tests.
# It navigates to the correct directory (`apps/backend`) where the
# pytest.ini and pyproject.toml files are located, ensuring that
# pytest runs with the correct configuration and pathing.

echo "--- Running Backend Python Tests ---"

# Navigate to the backend directory from the project root
# The script assumes it is being run from the project root.
cd "$(dirname "$0")/../apps/backend"

# Run pytest
# Pytest will automatically discover tests in the `tests/` directory
# and use the configuration from pytest.ini and pyproject.toml
pytest

echo "--- Backend Python Tests Finished ---"
