"""Smoke test for apps.backend.src.llm_timeout."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_llm_timeout_imports():
    """Smoke test: apps.backend.src.llm_timeout imports successfully."""
    import llm_timeout as llm_timeout
    assert llm_timeout is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
