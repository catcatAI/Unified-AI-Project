"""Smoke test for apps.backend.src.intelligent_test_generator."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_intelligent_test_generator_imports():
    """Smoke test: apps.backend.src.intelligent_test_generator imports successfully."""
    import intelligent_test_generator as intelligent_test_generator
    assert intelligent_test_generator is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
