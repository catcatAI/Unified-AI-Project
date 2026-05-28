"""Smoke test for apps.backend.src.lifecycle_loops_simple."""

import pytest


def test_lifecycle_loops_simple_imports():
    """Smoke test: apps.backend.src.lifecycle_loops_simple imports successfully."""
    import lifecycle_loops_simple
    assert lifecycle_loops_simple is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
