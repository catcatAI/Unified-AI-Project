"""Smoke test for apps.backend.src.core.tools.translation_model."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_translation_model_imports():
    """Smoke test: apps.backend.src.core.tools.translation_model imports successfully."""
    from core.tools import translation_model as translation_model
    assert translation_model is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
