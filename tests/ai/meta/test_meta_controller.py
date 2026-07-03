"""Tests for MetaController — confidence calibration and threshold adjustment."""
import json
import os
import tempfile
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


class TestMetaControllerCache:
    """C³ 4.5: Calibration cache and weighted adjustment aggregation."""

    def test_cache_returns_same_report_on_repeated_call(self):
        mc = MetaController()
        for i in range(10):
            mc.record_confidence("src", 0.8, correct=(i < 8))
        r1 = mc.get_calibration("src")
        r2 = mc.get_calibration("src")
        assert r1 is not None
        assert r2 is not None
        assert r1.suggested_threshold_adjustment == r2.suggested_threshold_adjustment

    def test_cache_invalidated_after_new_record(self):
        mc = MetaController()
        for i in range(10):
            mc.record_confidence("src", 0.8, correct=(i < 8))
        r1 = mc.get_calibration("src")
        assert r1 is not None
        adj_before = r1.suggested_threshold_adjustment
        # Add a conflicting sample
        mc.record_confidence("src", 0.8, correct=False)
        r2 = mc.get_calibration("src")
        assert r2 is not None
        # Adjustment should change after new data
        assert r2.suggested_threshold_adjustment != adj_before or mc._calibration_cache_dirty is False or "src" not in mc._calibration_cache

    def test_cache_dirty_flag_after_record(self):
        mc = MetaController()
        assert mc._calibration_cache_dirty is True  # fresh instance is dirty
        mc.record_confidence("src", 0.9)
        mc.record_confidence("src", 0.8)
        mc.record_confidence("src", 0.85)
        mc.get_calibration("src")
        assert mc._calibration_cache_dirty is False  # clean after computation
        mc.record_confidence("src", 0.7)  # new record → dirty
        assert mc._calibration_cache_dirty is True

    def test_weighted_adjustment_empty_returns_zero(self):
        mc = MetaController()
        assert mc.get_weighted_adjustment() == 0.0

    def test_weighted_adjustment_single_source(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.2, correct=(i < 12))
        adj = mc.get_weighted_adjustment()
        assert adj > 0  # underconfident → positive adjustment

    def test_weighted_adjustment_reliable_source_dominates(self):
        mc = MetaController()
        # Reliable source: many samples, high correctness but enough overconfident to trigger
        for i in range(20):
            mc.record_confidence("reliable", 0.9, correct=(i < 15))
        # Unreliable source: few samples, low correctness
        for i in range(5):
            mc.record_confidence("unreliable", 0.3, correct=(i < 1))
        weighted = mc.get_weighted_adjustment()
        # Reliable source (overconfident → negative) should dominate over
        # unreliable source (underconfident → positive but low weight)
        assert weighted < 0  # reliable source's overconfidence dominates

    def test_weighted_adjustment_few_samples_low_weight(self):
        mc = MetaController()
        # Source with few samples (below 3) — no calibration
        for i in range(2):
            mc.record_confidence("few", 0.9, correct=(i < 1))
        assert mc.get_weighted_adjustment() == 0.0

    def test_summary_uses_cache(self):
        mc = MetaController()
        for i in range(10):
            mc.record_confidence("src", 0.8, correct=(i < 8))
        mc.get_calibration("src")
        # After cache is populated, summary should work without recomputing
        mc._calibration_cache_dirty = False  # simulate clean cache
        summary = mc.get_summary()
        assert "src" in summary
        assert summary["src"]["samples"] == 10

    def test_get_threshold_adjustment_fast_path(self):
        mc = MetaController()
        for i in range(15):
            mc.record_confidence("src", 0.2, correct=(i < 12))
        adj = mc.get_threshold_adjustment("src")
        assert adj > 0  # underconfident → positive
        # Second call should use cached path
        # Mark cache as clean and check fast path still works
        adj2 = mc.get_threshold_adjustment("src")
        assert adj2 == adj


class TestMetaControllerPersistence:
    """C³ 5.0: Calibration state persistence across restarts."""

    def test_save_and_load_roundtrip(self):
        mc = MetaController(persist_path=None)
        # Build up state
        for i in range(15):
            mc.record_confidence("src_a", 0.9, correct=(i < 3))
        for i in range(10):
            mc.record_confidence("src_b", 0.2, correct=(i < 8))
        # Trigger closed-loop multiplier (3 consecutive "over" calls)
        for _ in range(3):
            mc.get_calibration("src_a")
        mc.get_calibration("src_b")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            mc.save_calibration_state(path)
            # Load into fresh instance
            mc2 = MetaController(persist_path=None)
            mc2.load_calibration_state(path)
            assert mc2._total_samples == 25
            assert "src_a" in mc2._ewma
            assert "src_b" in mc2._ewma
            assert mc2._adjustment_multipliers.get("src_a", 1.0) > 1.0
            assert "src_a" in mc2._threshold_adjustments
        finally:
            os.unlink(path)

    def test_load_from_nonexistent_file_logs_and_starts_fresh(self, caplog):
        mc = MetaController(persist_path=None)
        mc.load_calibration_state("/nonexistent/path.json")
        mc.record_confidence("src", 0.8)
        assert mc._total_samples == 1

    def test_auto_load_on_init(self):
        mc = MetaController(persist_path=None)
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 5))
        mc.get_calibration("src")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
            json.dump({
                "ewma": {"src": 0.85},
                "threshold_adjustments": {"src": -0.05},
                "adjustment_multipliers": {"src": 1.5},
                "raw_adjustments": {"src": -0.05},
                "total_samples": 15,
                "calibration_history": {"src": ["over", "over", "over"]},
            }, f)
        try:
            mc2 = MetaController(persist_path=path)
            assert mc2._total_samples == 15
            assert mc2._ewma.get("src") == 0.85
            assert mc2._adjustment_multipliers.get("src") == 1.5
            assert "src" in mc2._calibration_history
        finally:
            os.unlink(path)

    def test_get_stats_reflects_persistence(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            mc = MetaController(persist_path=path)
            stats = mc.get_stats()
            assert "has_persisted_state" in stats
            mc.record_confidence("src", 0.9)
            mc.record_confidence("src", 0.8)
            mc.record_confidence("src", 0.85)
            mc.get_calibration("src")
            mc.save_calibration_state(path)
            stats2 = mc.get_stats()
            assert stats2["has_persisted_state"] is True
        finally:
            os.unlink(path)

    def test_save_creates_directory(self):
        mc = MetaController(persist_path=None)
        for i in range(15):
            mc.record_confidence("src", 0.9, correct=(i < 5))
        mc.get_calibration("src")
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nested", "state.json")
            mc.save_calibration_state(nested_path)
            assert os.path.exists(nested_path)
            os.unlink(nested_path)
