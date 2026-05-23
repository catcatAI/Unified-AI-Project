"""Smoke test for apps.backend.src.core_system."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_core_system_imports():
    """Smoke test: apps.backend.src.core_system imports successfully."""
    import core_system as core_system
    assert core_system is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
