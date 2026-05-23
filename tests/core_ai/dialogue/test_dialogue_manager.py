"""Smoke test for apps.backend.src.core_ai.dialogue.dialogue_manager."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_dialogue_manager_imports():
    """Smoke test: apps.backend.src.core_ai.dialogue.dialogue_manager imports successfully."""
    from core_ai.dialogue import dialogue_manager as dialogue_manager
    assert dialogue_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
