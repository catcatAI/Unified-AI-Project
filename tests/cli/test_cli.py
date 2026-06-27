"""Smoke test for apps.backend.src.cli.cli."""
import sys
from pathlib import Path

import pytest


def test_cli_imports():
    """Smoke test: apps.backend.src.cli.cli imports successfully."""
    from cli import cli as cli
    assert cli is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
