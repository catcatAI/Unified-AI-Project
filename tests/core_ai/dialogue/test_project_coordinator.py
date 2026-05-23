"""Smoke test for apps.backend.src.core_ai.dialogue.project_coordinator."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_project_coordinator_imports():
    """Smoke test: apps.backend.src.core_ai.dialogue.project_coordinator imports successfully."""
    from core_ai.dialogue import project_coordinator as project_coordinator
    assert project_coordinator is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
