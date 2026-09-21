# -*- coding: utf-8 -*-
"""
Tests for MSBA MetricsCollector.
"""

import pytest
from ai.msba.metrics_collector import MetricsCollector


class TestMetricsCollector:
    def test_creation(self):
        collector = MetricsCollector()
        assert collector.metrics.total_requests == 0

    def test_record_latency(self):
        collector = MetricsCollector()
        collector.record_latency("seed", 5.0)
        collector.record_latency("selection", 10.0)

        summary = collector.get_summary()
        assert summary["total_latency_ms"] == 15.0

    def test_record_request(self):
        collector = MetricsCollector()
        collector.record_request()
        collector.record_request()

        summary = collector.get_summary()
        assert summary["total_requests"] == 2

    def test_cache_hit_rate(self):
        collector = MetricsCollector()
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_miss()

        summary = collector.get_summary()
        assert summary["cache_hit_rate"] == pytest.approx(2 / 3)

    def test_error_rate(self):
        collector = MetricsCollector()
        collector.record_request()
        collector.record_request()
        collector.record_error()

        summary = collector.get_summary()
        assert summary["error_rate"] == pytest.approx(0.5)

    def test_layer_breakdown(self):
        collector = MetricsCollector()
        collector.record_latency("seed", 5.0)
        collector.record_latency("seed", 10.0)
        collector.record_latency("selection", 15.0)

        breakdown = collector.get_layer_breakdown()
        assert "seed" in breakdown
        assert "selection" in breakdown
        assert breakdown["seed"]["avg_ms"] == 7.5

    def test_block_frequency(self):
        collector = MetricsCollector()
        collector.record_block_selection("emotional")
        collector.record_block_selection("emotional")
        collector.record_block_selection("cognitive")

        freq = collector.get_block_frequency()
        assert freq["emotional"] == pytest.approx(2 / 3)
        assert freq["cognitive"] == pytest.approx(1 / 3)

    def test_reset(self):
        collector = MetricsCollector()
        collector.record_request()
        collector.record_latency("test", 1.0)

        collector.reset()

        summary = collector.get_summary()
        assert summary["total_requests"] == 0
        assert summary["total_latency_ms"] == 0.0

    def test_max_records(self):
        collector = MetricsCollector(max_records=5)

        for i in range(10):
            collector.record_latency("test", float(i))

        assert len(collector._latency_records) == 5

    def test_seed_source(self):
        collector = MetricsCollector()
        collector.record_seed_source("math")
        collector.record_seed_source("math")
        collector.record_seed_source("knowledge")

        # No assertion needed, just verify no exception
        summary = collector.get_summary()
        assert summary["total_requests"] == 0
