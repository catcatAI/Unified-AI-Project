"""Smoke test for apps.backend.src.services.hsp_endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_hsp_endpoints_imports():
    """Smoke test: apps.backend.src.services.hsp_endpoints imports successfully."""
    from services import hsp_endpoints as hsp_endpoints
    assert hsp_endpoints is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
