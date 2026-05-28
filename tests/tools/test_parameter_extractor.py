"""Smoke test for apps.backend.src.core.tools.parameter_extractor."""
import pytest

def test_parameter_extractor_imports():
    """Smoke test: apps.backend.src.core.tools.parameter_extractor imports successfully."""
    from core.tools import parameter_extractor as parameter_extractor
    assert parameter_extractor is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
