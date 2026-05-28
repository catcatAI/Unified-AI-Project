"""Smoke test for apps.backend.src.core_system."""

import pytest


def test_core_system_imports():
    """Smoke test: apps.backend.src.core_system imports successfully."""
    import core_system
    assert core_system is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
