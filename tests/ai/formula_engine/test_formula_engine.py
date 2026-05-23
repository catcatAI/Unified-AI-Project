"""Smoke test for apps.backend.src.core_ai.formula_engine.formula_engine."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_formula_engine_imports():
    """Smoke test: apps.backend.src.core_ai.formula_engine.formula_engine imports successfully."""
    from core_ai.formula_engine import formula_engine as formula_engine
    assert formula_engine is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
