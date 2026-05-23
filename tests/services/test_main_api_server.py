"""Smoke test for apps.backend.src.services.main_api_server."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_main_api_server_imports():
    """Smoke test: apps.backend.src.services.main_api_server imports successfully."""
    from services import main_api_server as main_api_server
    assert main_api_server is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
