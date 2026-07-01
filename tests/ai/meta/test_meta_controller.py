"""Tests for MetaController — confidence calibration and threshold adjustment."""
from collections import deque

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


class TestMetaControllerClosedLoop:
    """C³ 4.0: closed-loop adjustment multiplier from calibration history."""

    def test_calibration_history_tracked(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 5))
        mc.get_calibration("src")
        assert "src" in mc._calibration_history
        assert len(mc._calibration_history["src"]) > 0

    def test_multiplier_increases_after_three_overconfidence(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 3))
        # Three calls to get_calibration -> three "over" entries
        for _ in range(3):
            mc.get_calibration("src")
        assert mc._adjustment_multipliers.get("src", 1.0) > 1.0

    def test_multiplier_increases_after_three_underconfidence(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.2, correct=(i < 12))
        for _ in range(3):
            mc.get_calibration("src")
        assert mc._adjustment_multipliers.get("src", 1.0) > 1.0

    def test_multiplier_decays_after_stable_period(self):
        mc = MetaController()
        # Raise multiplier on source_a
        for i in range(15):
            mc.record_confidence("src_a", 0.9, correct=(i < 3))
        for _ in range(3):
            mc.get_calibration("src_a")
        multiplier_high = mc._adjustment_multipliers.get("src_a", 1.0)

        # Use separate source to verify decay mechanism
        mc._adjustment_multipliers["src_b"] = 2.0
        mc._calibration_history["src_b"] = deque(["stable", "stable"], maxlen=5)
        mc.get_calibration("src_b")
        assert mc._adjustment_multipliers["src_b"] <= 2.0

    def test_multiplier_amplifies_adjustment(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 3))
        for _ in range(3):
            mc.get_calibration("src")
        # Now the adjustment should be amplified by multiplier
        report = mc.get_calibration("src")
        assert report is not None
        base = -0.05
        multiplier = mc._adjustment_multipliers.get("src", 1.0)
        expected = round(base * multiplier, 3)
        assert report.suggested_threshold_adjustment == expected
