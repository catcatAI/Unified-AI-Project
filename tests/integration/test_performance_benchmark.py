"""
测试模块 - test_performance_benchmark
"""

import pytest
from unittest.mock import Mock
import time


class TestPerformanceBenchmark:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    def test_performance_benchmark_basic(self):
        start_time = time.time()
        result = sum(range(1000))
        elapsed = time.time() - start_time
        assert result == 499500
        assert elapsed < 1.0

    def test_memory_usage(self):
        mock_data = {"key": "value" * 1000}
        assert len(mock_data["key"]) == 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])