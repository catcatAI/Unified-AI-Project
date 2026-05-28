"""Smoke test for apps.backend.src.lifecycle_loops."""

import pytest


def test_lifecycle_loops_imports():
    """Smoke test: apps.backend.src.lifecycle_loops imports successfully."""
    import lifecycle_loops
    assert lifecycle_loops is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
