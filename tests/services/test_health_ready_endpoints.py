"""Tests for health/ready endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_health_ready_stub():
    pytest.skip("Health ready endpoint test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])