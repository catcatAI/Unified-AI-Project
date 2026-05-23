"""Smoke test for apps.backend.src.core_ai.dialogue.project_coordinator_fix."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_project_coordinator_fix_imports():
    """Smoke test: apps.backend.src.core_ai.dialogue.project_coordinator_fix imports successfully."""
    from core_ai.dialogue import project_coordinator_fix as project_coordinator_fix
    assert project_coordinator_fix is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
