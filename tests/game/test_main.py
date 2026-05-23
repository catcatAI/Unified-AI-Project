"""Smoke test for apps.backend.src.game.main."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_main_imports():
    """Smoke test: apps.backend.src.game.main imports successfully."""
    from game import main as main
    assert main is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
