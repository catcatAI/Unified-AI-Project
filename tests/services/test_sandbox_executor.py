"""Tests for sandbox executor."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_sandbox_executor_stub():
    pytest.skip("Sandbox executor test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])