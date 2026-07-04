"""
Basic smoke tests — verify project structure and environment.
"""

import os
import time

import pytest


def test_project_apps_directory_exists():
    """Verify apps directory exists at project root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(os.path.dirname(current_dir))
    assert os.path.isdir(os.path.join(project_dir, "apps")), "apps/ directory should exist"


def test_project_tests_directory_exists():
    """Verify tests directory exists at project root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(os.path.dirname(current_dir))
    assert os.path.isdir(os.path.join(project_dir, "tests")), "tests/ directory should exist"


@pytest.mark.slow()
def test_slow_example():
    """Slow test example — skipped in fast test mode."""
    t0 = time.time()
    time.sleep(0.1)
    elapsed = time.time() - t0
    assert elapsed >= 0.09, f"Sleep was only {elapsed:.3f}s"


def test_environment_variables():
    """Verify env var parsing produces correct boolean."""
    testing_env = os.getenv("TESTING", "false").lower() == "true"
    assert isinstance(testing_env, bool)
    assert testing_env is False, "TESTING env var should default to false when not set"


if __name__ == "__main__":
    pytest.main([__file__])
