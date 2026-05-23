"""Smoke test for apps.backend.src.services.hot_endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_hot_endpoints_imports():
    """Smoke test: apps.backend.src.services.hot_endpoints imports successfully."""
    from services import hot_endpoints as hot_endpoints
    assert hot_endpoints is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
