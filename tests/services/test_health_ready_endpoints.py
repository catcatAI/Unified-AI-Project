"""Smoke test for apps.backend.src.services.health_ready_endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_health_ready_endpoints_imports():
    """Smoke test: apps.backend.src.services.health_ready_endpoints imports successfully."""
    from services import health_ready_endpoints as health_ready_endpoints
    assert health_ready_endpoints is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
