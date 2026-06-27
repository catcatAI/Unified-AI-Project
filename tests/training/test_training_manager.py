"""Smoke test for apps.backend.src.training_manager."""
import pytest


def test_training_manager_imports():
    """Smoke test: apps.backend.src.training_manager imports successfully."""
    import training_manager as training_manager
    assert training_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
