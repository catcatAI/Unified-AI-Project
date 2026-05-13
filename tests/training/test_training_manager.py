"""Tests for training manager."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_training_manager_stub():
    pytest.skip("Training manager test pending full implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])