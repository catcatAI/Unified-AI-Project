"""Tests for AI dialogue project coordinator."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_ai_dialogue_coordinator_stub():
    pytest.skip("AI dialogue project coordinator test pending full implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])