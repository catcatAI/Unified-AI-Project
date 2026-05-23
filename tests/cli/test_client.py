"""Smoke test for apps.backend.src.cli.client."""
import pytest
import sys
from pathlib import Path

def test_client_imports():
    """Smoke test: apps.backend.src.cli.client imports successfully."""
    from cli import client as client
    assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
