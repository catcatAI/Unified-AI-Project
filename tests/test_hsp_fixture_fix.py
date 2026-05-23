"""Smoke test for apps.backend.src.hsp_fixture_fix."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_hsp_fixture_fix_imports():
    """Smoke test: apps.backend.src.hsp_fixture_fix imports successfully."""
    import hsp_fixture_fix as hsp_fixture_fix
    assert hsp_fixture_fix is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
