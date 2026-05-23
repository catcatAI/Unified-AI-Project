"""Smoke test for apps.backend.src.defect_detector."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_defect_detector_imports():
    """Smoke test: apps.backend.src.defect_detector imports successfully."""
    import defect_detector as defect_detector
    assert defect_detector is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
