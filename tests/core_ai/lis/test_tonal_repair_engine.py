"""Smoke test for apps.backend.src.core_ai.lis.tonal_repair_engine."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_tonal_repair_engine_imports():
    """Smoke test: apps.backend.src.core_ai.lis.tonal_repair_engine imports successfully."""
    from core_ai.lis import tonal_repair_engine as tonal_repair_engine
    assert tonal_repair_engine is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
