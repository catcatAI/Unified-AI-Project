"""Smoke test for apps.backend.src.security_improvements."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_security_improvements_imports():
    """Smoke test: apps.backend.src.security_improvements imports successfully."""
    import security_improvements as security_improvements
    assert security_improvements is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
