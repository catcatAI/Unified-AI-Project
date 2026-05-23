"""Smoke test for apps.backend.src.core_ai.context.context_system."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_context_system_imports():
    """Smoke test: apps.backend.src.core_ai.context.context_system imports successfully."""
    from core_ai.context import context_system as context_system
    assert context_system is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
