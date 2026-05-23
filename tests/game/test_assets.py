"""Smoke test for apps.backend.src.game.assets."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_assets_imports():
    """Smoke test: apps.backend.src.game.assets imports successfully."""
    from game import assets as assets
    assert assets is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
