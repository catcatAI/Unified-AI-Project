"""Tests for HSPAdvancedPerformanceOptimizer and HSPAdvancedPerformanceEnhancer."""
import pytest
from core.hsp.advanced_performance_optimizer import (
    HSPAdvancedPerformanceEnhancer,
    HSPAdvancedPerformanceOptimizer,
)


class TestHSPAdvancedPerformanceEnhancer:
    def test_init_defaults(self):
        enh = HSPAdvancedPerformanceEnhancer()
        assert enh.config == {}
        assert enh.enabled is True

    def test_init_with_config(self):
        enh = HSPAdvancedPerformanceEnhancer(config={"opt": True}, enabled=False)
        assert enh.config["opt"] is True
        assert enh.enabled is False


class TestHSPAdvancedPerformanceOptimizer:
    def test_init_default(self):
        opt = HSPAdvancedPerformanceOptimizer()
        assert opt.config == {}
        assert isinstance(opt.enhancer, HSPAdvancedPerformanceEnhancer)

    def test_init_with_config(self):
        opt = HSPAdvancedPerformanceOptimizer(config={"key": 1})
        assert opt.config["key"] == 1

    def test_optimize_passthrough(self):
        opt = HSPAdvancedPerformanceOptimizer()
        assert opt.optimize("hello") == "hello"
        assert opt.optimize(42) == 42
        assert opt.optimize(None) is None

    def test_optimize_dict(self):
        opt = HSPAdvancedPerformanceOptimizer()
        data = {"a": 1}
        assert opt.optimize(data) is data
