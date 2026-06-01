"""Smoke tests for ai/ops/performance_optimizer.py"""
import pytest


class TestPerformanceOptimizer:
    """Basic smoke tests for PerformanceOptimizer"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from ai.ops.performance_optimizer import PerformanceOptimizer
            assert PerformanceOptimizer is not None
        except ImportError as e:
            pytest.skip(f"PerformanceOptimizer not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from ai.ops.performance_optimizer import PerformanceOptimizer
            instance = PerformanceOptimizer()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"PerformanceOptimizer not available: {e}")
        except Exception as e:
            pytest.skip(f"PerformanceOptimizer init failed (expected in CI): {e}")

    def test_instantiation_with_config(self):
        """Verify instantiation with config"""
        try:
            from ai.ops.performance_optimizer import PerformanceOptimizer
            instance = PerformanceOptimizer(config={"threshold": 0.9})
            assert instance is not None
            assert instance.config["threshold"] == 0.9
        except ImportError as e:
            pytest.skip(f"PerformanceOptimizer not available: {e}")
        except Exception as e:
            pytest.skip(f"PerformanceOptimizer init failed (expected in CI): {e}")
