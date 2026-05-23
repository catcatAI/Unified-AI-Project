"""Smoke test for apps.backend.src.services.audio_service."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_audio_service_imports():
    """Smoke test: apps.backend.src.services.audio_service imports successfully."""
    from services import audio_service as audio_service
    assert audio_service is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
