"""Smoke test for apps.backend.src.game.npcs."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_npcs_imports():
    """Smoke test: apps.backend.src.game.npcs imports successfully."""
    from game import npcs as npcs
    assert npcs is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
