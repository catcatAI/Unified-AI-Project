"""Tests for MetaController — confidence calibration and threshold adjustment."""
import pytest
from ai.meta.meta_controller import MetaController


class TestMetaControllerCore:
    def test_init(self):
        mc = MetaController()
        assert mc._total_samples == 0
        assert mc._window_size == 100

    def test_record_and_stats(self):
        mc = MetaController()
        mc.record_confidence("source_a", 0.9)
        mc.record_confidence("source_a", 0.7)
        stats = mc.get_stats()
        assert stats["total_samples"] == 2
        assert "source_a" in stats["tracked_sources"]

    def test_get_calibration_returns_none_for_few_samples(self):
        mc = MetaController()
        mc.record_confidence("src", 0.8)
        mc.record_confidence("src", 0.6)
        assert mc.get_calibration("src") is None

    def test_get_calibration_without_correctness(self):
        mc = MetaController()
        for _ in range(5):
            mc.record_confidence("src", 0.7)
        report = mc.get_calibration("src")
        assert report is not None
        assert report.sample_count == 5
        assert report.source == "src"

    def test_get_calibration_with_correctness(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 12))
        report = mc.get_calibration("src")
        assert report is not None
        assert report.is_reliable

    def test_threshold_adjustment_overconfidence(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 5))
        adj = mc.get_threshold_adjustment("src")
        assert adj < 0

    def test_threshold_adjustment_underconfidence(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.2, correct=(i < 12))
        adj = mc.get_threshold_adjustment("src")
        assert adj > 0

    def test_default_adjustment(self):
        mc = MetaController()
        adj = mc.get_threshold_adjustment("nonexistent", default=0.1)
        assert adj == 0.1

    def test_summary(self):
        mc = MetaController()
        for _ in range(5):
            mc.record_confidence("s1", 0.8)
        for _ in range(5):
            mc.record_confidence("s2", 0.6)
        summary = mc.get_summary()
        assert "s1" in summary
        assert "s2" in summary

    def test_window_size(self):
        mc = MetaController(window_size=10)
        for _ in range(20):
            mc.record_confidence("src", 0.5)
        assert len(mc._samples["src"]) == 10
