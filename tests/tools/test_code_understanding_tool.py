"""Smoke test for apps.backend.src.core.tools.code_understanding_tool."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_code_understanding_tool_imports():
    """Smoke test: apps.backend.src.core.tools.code_understanding_tool imports successfully."""
    from core.tools import code_understanding_tool as code_understanding_tool
    assert code_understanding_tool is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
