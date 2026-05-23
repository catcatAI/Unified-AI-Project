"""Smoke test for apps.backend.src.services.llm_interface."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_llm_interface_imports():
    """Smoke test: apps.backend.src.services.llm_interface imports successfully."""
    from services import llm_interface as llm_interface
    assert llm_interface is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
