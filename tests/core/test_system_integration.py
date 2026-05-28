"""Smoke test for apps.backend.src.system_integration."""

import pytest


def test_system_integration_imports():
    """Smoke test: apps.backend.src.system_integration imports successfully."""
    import system_integration
    assert system_integration is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
