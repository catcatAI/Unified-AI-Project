"""Smoke test for apps.backend.src.integration.agent_collaboration."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_agent_collaboration_imports():
    """Smoke test: apps.backend.src.integration.agent_collaboration imports successfully."""
    from integration import agent_collaboration as agent_collaboration
    assert agent_collaboration is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
