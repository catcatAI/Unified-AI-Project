# -*- coding: utf-8 -*-
"""
Tests for MSBA PerformanceProfiler.
"""

import time

import pytest
from ai.msba.performance_profiler import PerformanceProfiler


class TestPerformanceProfiler:
    def test_creation(self):
        profiler = PerformanceProfiler()
        assert profiler.history_size == 100

    def test_layer_timing(self):
        profiler = PerformanceProfiler()
        start = profiler.start_layer("seed")
        time.sleep(0.001)
        elapsed = profiler.end_layer("seed", start)
        assert elapsed > 0

    def test_total_timing(self):
        profiler = PerformanceProfiler()
        start = profiler.start_total()
        time.sleep(0.001)
        elapsed = profiler.end_total(start)
        assert elapsed > 0

    def test_layer_stats(self):
        profiler = PerformanceProfiler()
        for _ in range(5):
            start = profiler.start_layer("hit")
            profiler.end_layer("hit", start)

        stats = profiler.get_layer_stats()
        assert "hit" in stats
        assert stats["hit"]["count"] == 5
        assert stats["hit"]["avg_ms"] >= 0

    def test_total_stats(self):
        profiler = PerformanceProfiler()
        for _ in range(3):
            start = profiler.start_total()
            profiler.end_total(start)

        stats = profiler.get_total_stats()
        assert stats["count"] == 3
        assert stats["avg_ms"] >= 0

    def test_bottlenecks(self):
        profiler = PerformanceProfiler()
        profiler._bottleneck_counts["hit"] = 5

        bottlenecks = profiler.get_bottlenecks()
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["layer"] == "hit"
        assert bottlenecks[0]["over_budget_count"] == 5

    def test_suggest_optimizations(self):
        profiler = PerformanceProfiler()
        profiler._bottleneck_counts["seed"] = 10

        suggestions = profiler.suggest_optimizations()
        assert len(suggestions) > 0

    def test_reset(self):
        profiler = PerformanceProfiler()
        start = profiler.start_layer("seed")
        profiler.end_layer("seed", start)
        profiler.reset()
        stats = profiler.get_layer_stats()
        assert len(stats) == 0

    def test_percentile(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert PerformanceProfiler._percentile(data, 50) == 3.0
        assert PerformanceProfiler._percentile(data, 95) == 5.0
        assert PerformanceProfiler._percentile([], 50) == 0.0
