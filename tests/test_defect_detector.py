"""Tests for defect detector."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_defect_detector_stub():
    pytest.skip("Defect detector test pending full implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])