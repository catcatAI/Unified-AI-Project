"""Tests for C-state (``core/life/al_snn_modulation.py`` + GARDEN ``forward``).

Two halves. The pure half pins the modulation law: neutral at mid-cycle, symmetric
at the extremes, and exactly 1.0 when unobserved so an unwired caller behaves
bit-identically. The model half pins that the modulation actually reaches the
SNN's internal excitability -- the same input, the same weights, a different spike
pattern -- and that an absent or malformed modulation changes nothing.
"""

from __future__ import annotations

import pytest

from ai.garden.snn_core import TensorSNNCore
from core.life.al_snn_modulation import MAX_MULTIPLIER, MIN_MULTIPLIER, modulate

CHAIN = ("seed", "a", "b", "c", "d")


class TestLaw:
    def test_midpoint_is_neutral(self):
        assert modulate(0.5).threshold_multiplier == 1.0

    def test_extremes_are_symmetric(self):
        low = modulate(0.0).threshold_multiplier
        high = modulate(1.0).threshold_multiplier
        assert low + high == pytest.approx(2.0)
        assert low > 1.0 > high

    @pytest.mark.parametrize("bad", [None, True, "nope", float("nan"), float("inf")])
    def test_unobserved_is_exactly_neutral(self, bad):
        mod = modulate(bad)
        assert mod.threshold_multiplier == 1.0 and mod.source is None

    def test_clamped(self):
        assert modulate(0.0, span=5.0).threshold_multiplier == MAX_MULTIPLIER
        assert modulate(1.0, span=5.0).threshold_multiplier == MIN_MULTIPLIER

    def test_provenance(self):
        assert modulate(0.9).source == "core.life.al_oscillator"
        assert modulate(0.9).as_dict()["activation"] == 0.9


def _core(weight: float = 0.6) -> TensorSNNCore:
    core = TensorSNNCore(leak=0.5, threshold=0.6, timesteps=12, decay=0.9, device="cpu")
    for left, right in zip(CHAIN, CHAIN[1:]):
        core.add_relation(left, right, weight=weight)
    return core


class TestModelCoupling:
    INPUT = {"seed": 1.0}

    def test_without_modulation_nothing_changes(self):
        core = _core()
        assert core.forward(self.INPUT) == core.forward(self.INPUT, {})

    def test_a_trough_phase_stops_the_propagation(self):
        core = _core()
        baseline = core.forward(self.INPUT)
        assert baseline  # 基線有概念擴散
        quiet = core.forward(self.INPUT, {"al_modulation": modulate(0.0).as_dict()})
        assert quiet == {}

    def test_the_input_is_identical_in_both_calls(self):
        core = _core()
        before = dict(self.INPUT)
        core.forward(self.INPUT, {"al_modulation": modulate(0.0).as_dict()})
        assert self.INPUT == before

    @pytest.mark.parametrize("bad", [None, "x", -1.0, 0.0])
    def test_malformed_modulation_is_neutral(self, bad):
        core = _core()
        baseline = core.forward(self.INPUT)
        assert (
            core.forward(self.INPUT, {"al_modulation": {"threshold_multiplier": bad}}) == baseline
        )

    def test_crossover_moves_with_the_weights(self):
        """切換點隨輸入電流移動 → 它長自動力學，不是寫死的 if。"""
        points = []
        for weight in (0.5, 0.75):
            core = _core(weight)
            lo, hi = 0.0, 1.0
            for _ in range(12):
                mid = 0.5 * (lo + hi)
                if core.forward(self.INPUT, {"al_modulation": modulate(mid).as_dict()}):
                    hi = mid
                else:
                    lo = mid
            points.append(0.5 * (lo + hi))
        assert points[1] < points[0] - 0.1
