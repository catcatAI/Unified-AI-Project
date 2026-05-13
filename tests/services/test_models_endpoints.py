"""Tests for models endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_models_endpoints_stub():
    pytest.skip("Models endpoint test pending implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])