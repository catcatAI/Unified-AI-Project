"""Smoke test for apps.backend.src.core.tools.logic_model."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_logic_model_imports():
    """Smoke test: apps.backend.src.core.tools.logic_model imports successfully."""
    from core.tools import logic_model as logic_model
    assert logic_model is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
