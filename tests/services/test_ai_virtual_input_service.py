"""Smoke test for apps.backend.src.services.ai_virtual_input_service."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_ai_virtual_input_service_imports():
    """Smoke test: apps.backend.src.services.ai_virtual_input_service imports successfully."""
    from services import ai_virtual_input_service as ai_virtual_input_service
    assert ai_virtual_input_service.__name__ == 'services.ai_virtual_input_service'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
