"""Tests for AI Virtual Input Service."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_service_stub():
    pytest.skip("AI virtual input service test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])