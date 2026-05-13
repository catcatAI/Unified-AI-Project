"""Tests for resource awareness service."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_resource_awareness_stub():
    pytest.skip("Resource awareness service test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])