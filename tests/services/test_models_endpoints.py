"""Smoke test for apps.backend.src.services.models_endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_models_endpoints_imports():
    """Smoke test: apps.backend.src.services.models_endpoints imports successfully."""
    from services import models_endpoints as models_endpoints
    assert models_endpoints is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
