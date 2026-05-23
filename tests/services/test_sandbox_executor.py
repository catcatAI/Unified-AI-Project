"""Smoke test for apps.backend.src.services.sandbox_executor."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_sandbox_executor_imports():
    """Smoke test: apps.backend.src.services.sandbox_executor imports successfully."""
    from services import sandbox_executor as sandbox_executor
    assert sandbox_executor is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
