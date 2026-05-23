"""Smoke test for apps.backend.src.cli.error_handler."""
import pytest
import sys
from pathlib import Path

def test_error_handler_imports():
    """Smoke test: apps.backend.src.cli.error_handler imports successfully."""
    from cli import error_handler as error_handler
    assert error_handler is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
