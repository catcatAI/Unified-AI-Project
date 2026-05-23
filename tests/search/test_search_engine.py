"""Smoke test for apps.backend.src.search.search_engine."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_search_engine_imports():
    """Smoke test: apps.backend.src.search.search_engine imports successfully."""
    from search import search_engine as search_engine
    assert search_engine is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
