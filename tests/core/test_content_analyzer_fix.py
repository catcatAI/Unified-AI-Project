"""Smoke test for apps.backend.src.content_analyzer_fix."""

import pytest


def test_content_analyzer_fix_imports():
    """Smoke test: apps.backend.src.content_analyzer_fix imports successfully."""
    import content_analyzer_fix
    assert content_analyzer_fix is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
