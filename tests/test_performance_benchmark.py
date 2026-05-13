"""Tests for performance benchmark."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))


def test_performance_benchmark_stub():
    pytest.skip("Performance benchmark test pending full implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])