"""Smoke test for apps.backend.src.services.vision_service."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_vision_service_imports():
    """Smoke test: apps.backend.src.services.vision_service imports successfully."""
    from services import vision_service as vision_service
    assert vision_service is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
