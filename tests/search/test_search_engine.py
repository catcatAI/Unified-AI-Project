"""Tests for search engine."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_search_engine_stub():
    pytest.skip("Search engine test pending full implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])