"""Smoke test for apps.backend.src.lifecycle_loops_simple."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_lifecycle_loops_simple_imports():
    """Smoke test: apps.backend.src.lifecycle_loops_simple imports successfully."""
    import lifecycle_loops_simple as lifecycle_loops_simple
    assert lifecycle_loops_simple is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
