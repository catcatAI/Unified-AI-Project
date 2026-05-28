"""Smoke test for apps.backend.src.security_improvements."""

import pytest


def test_security_improvements_imports():
    """Smoke test: apps.backend.src.security_improvements imports successfully."""
    import security_improvements
    assert security_improvements is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
