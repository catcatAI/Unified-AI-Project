"""Smoke test for apps.backend.src.performance_benchmark."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_performance_benchmark_imports():
    """Smoke test: apps.backend.src.performance_benchmark imports successfully."""
    import performance_benchmark as performance_benchmark
    assert performance_benchmark is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
