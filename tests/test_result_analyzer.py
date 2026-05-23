"""Smoke test for apps.backend.src.result_analyzer."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_result_analyzer_imports():
    """Smoke test: apps.backend.src.result_analyzer imports successfully."""
    import result_analyzer as result_analyzer
    assert result_analyzer is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
