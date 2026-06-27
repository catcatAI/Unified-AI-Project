"""Smoke test for apps.backend.src.services.main_api_server."""
import pytest


def test_main_api_server_imports():
    """Smoke test: apps.backend.src.services.main_api_server imports successfully."""
    from services import main_api_server as main_api_server
    assert main_api_server.__name__ == 'services.main_api_server'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
