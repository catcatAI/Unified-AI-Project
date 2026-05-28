"""Smoke test for apps.backend.src.fragmenta.fragmenta_orchestrator."""
import pytest

def test_fragmenta_orchestrator_imports():
    """Smoke test: apps.backend.src.fragmenta.fragmenta_orchestrator imports successfully."""
    from fragmenta import fragmenta_orchestrator as fragmenta_orchestrator
    assert fragmenta_orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
