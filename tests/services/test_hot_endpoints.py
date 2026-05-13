"""Tests for hot reload endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_hot_endpoints_stub():
    pytest.skip("Hot reload endpoint test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])