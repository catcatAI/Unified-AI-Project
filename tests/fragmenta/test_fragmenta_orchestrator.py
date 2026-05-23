"""Smoke test for apps.backend.src.fragmenta.fragmenta_orchestrator."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_fragmenta_orchestrator_imports():
    """Smoke test: apps.backend.src.fragmenta.fragmenta_orchestrator imports successfully."""
    from fragmenta import fragmenta_orchestrator as fragmenta_orchestrator
    assert fragmenta_orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
