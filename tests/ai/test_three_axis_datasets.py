"""
Tests for the Three-Axis dataset auto-decision logic.

Covers the auto-download / auto-quantity decision in
``scripts/prepare_three_axis_datasets.py``: hardware tier is an upper bound,
memory budget is the authoritative clamp, and long samples (alpaca) are capped
hard because exact-completions cost grows ~O(sample_len^2).

Pure functions only — no network, no filesystem writes.
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

import pytest
from prepare_three_axis_datasets import (  # noqa: E402
    BUDGET_FRACTION,
    BYTES_PER_CHAR,
    TIER_CAPS,
    decide_plan,
)

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

CAP_2048 = 2048 * 1024 * 1024  # 2 GiB default project cap


class TestTierCaps:
    def test_full_tier_is_ceiling(self):
        plan = decide_plan(
            "high_performance_desktop",
            CAP_2048,
            avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306},
        )
        assert plan["tier"] == "full"
        for key in TIER_CAPS["full"]:
            assert plan["caps"][key] <= TIER_CAPS["full"][key]

    def test_low_power_tier_is_smallest(self):
        plan = decide_plan(
            "low_power_device", CAP_2048, avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306}
        )
        assert plan["tier"] == "small"
        for key in TIER_CAPS["small"]:
            assert plan["caps"][key] <= TIER_CAPS["small"][key]

    def test_unknown_profile_falls_back_to_medium(self):
        plan = decide_plan(
            "unknown", CAP_2048, avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306}
        )
        assert plan["tier"] == "medium"


class TestMemoryClamp:
    def test_short_samples_reach_tier_cap(self):
        # Arithmetic is short and cheap: memory budget is not the binding limit.
        plan = decide_plan(
            "high_performance_desktop",
            CAP_2048,
            avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306},
        )
        assert plan["caps"]["arithmetic"] == TIER_CAPS["full"]["arithmetic"]
        assert plan["caps"]["logic"] == TIER_CAPS["full"]["logic"]

    def test_long_samples_capped_by_memory(self):
        # Alpaca avg 306 bytes at 2000 B/byte, 50% of 2 GiB -> the memory
        # budget clamps the tier cap.
        plan = decide_plan(
            "high_performance_desktop",
            CAP_2048,
            avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306},
        )
        expected = int(CAP_2048 * BUDGET_FRACTION["alpaca"] / BYTES_PER_CHAR["alpaca"] / 306)
        assert plan["caps"]["alpaca"] == expected
        assert plan["caps"]["alpaca"] < TIER_CAPS["full"]["alpaca"]

    def test_smaller_memory_cap_clamps_harder(self):
        cap_small = 512 * 1024 * 1024  # 512 MiB
        plan = decide_plan(
            "high_performance_desktop",
            cap_small,
            avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306},
        )
        assert plan["caps"]["alpaca"] < 2339  # strictly less than 2 GiB result

    def test_budgeted_footprint_stays_within_cap(self):
        plan = decide_plan(
            "high_performance_desktop",
            CAP_2048,
            avg_lens={"arithmetic": 14, "logic": 39, "alpaca": 306},
        )
        estimated = 0
        for key, frac in BUDGET_FRACTION.items():
            n = plan["caps"][key]
            est = n * BYTES_PER_CHAR[key] * {"arithmetic": 14, "logic": 39, "alpaca": 306}[key]
            assert est <= CAP_2048 * frac
            estimated += est
        assert estimated <= CAP_2048  # summed budgets respect the cap


class TestPlanShape:
    def test_plan_is_serialisable_manifest(self):
        plan = decide_plan("laptop_normal", CAP_2048)
        import json

        assert "caps" in json.loads(json.dumps(plan))  # manifest-safe
        assert "rationale" in plan
        assert "tier" in plan
        assert "memory_cap_bytes" in plan

    def test_always_returns_at_least_one_sample(self):
        plan = decide_plan("low_power_device", 1024 * 1024)  # tiny 1 MiB cap
        for key in ("arithmetic", "logic", "alpaca"):
            assert plan["caps"][key] >= 1
