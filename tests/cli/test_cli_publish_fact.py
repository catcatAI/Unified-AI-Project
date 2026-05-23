"""Smoke test for apps.backend.src.cli.cli_publish_fact."""
import pytest
import sys
from pathlib import Path

def test_cli_publish_fact_imports():
    """Smoke test: apps.backend.src.cli.cli_publish_fact imports successfully."""
    from cli import cli_publish_fact as cli_publish_fact
    assert cli_publish_fact is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
