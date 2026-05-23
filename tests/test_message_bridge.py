"""Smoke test for apps.backend.src.message_bridge."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_message_bridge_imports():
    """Smoke test: apps.backend.src.message_bridge imports successfully."""
    import message_bridge as message_bridge
    assert message_bridge is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
