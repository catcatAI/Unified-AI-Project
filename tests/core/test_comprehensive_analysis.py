"""Smoke test for apps.backend.src.comprehensive_analysis."""

import pytest


def test_comprehensive_analysis_imports():
    """Smoke test: apps.backend.src.comprehensive_analysis imports successfully."""
    import comprehensive_analysis
    assert comprehensive_analysis is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
