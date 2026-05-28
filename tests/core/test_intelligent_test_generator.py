"""Smoke test for apps.backend.src.intelligent_test_generator."""

import pytest


def test_intelligent_test_generator_imports():
    """Smoke test: apps.backend.src.intelligent_test_generator imports successfully."""
    import intelligent_test_generator
    assert intelligent_test_generator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
