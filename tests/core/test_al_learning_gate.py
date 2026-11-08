"""Tests for the C-learn plasticity gate (``core/life/al_learning_gate.py``).

The gate's value is that an unwired caller behaves exactly as before: mid-cycle is
1.0, anything malformed collapses to 1.0, and only the two extremes move the
effective learning rate. ``sanitize_gain`` is the model-side backstop for values
that arrive from outside the module.
"""

from __future__ import annotations

import pytest
from core.life.al_learning_gate import (
    MAX_GAIN,
    MIN_GAIN,
    learning_gain,
    sanitize_gain,
)


class TestLaw:
    def test_midpoint_is_neutral(self):
        assert learning_gain(0.5).gain == 1.0

    def test_extremes_are_symmetric(self):
        low = learning_gain(0.0).gain
        high = learning_gain(1.0).gain
        assert low + high == pytest.approx(2.0)
        assert low < 1.0 < high

    @pytest.mark.parametrize("bad", [None, True, "nope", float("nan"), float("inf")])
    def test_unobserved_is_exactly_neutral(self, bad):
        gain = learning_gain(bad)
        assert gain.gain == 1.0 and gain.activation is None and gain.source is None

    def test_clamped(self):
        assert learning_gain(0.0, span=9.0).gain == MIN_GAIN
        assert learning_gain(1.0, span=9.0).gain == MAX_GAIN

    def test_provenance(self):
        gain = learning_gain(0.9)
        assert gain.source == "core.life.al_oscillator"
        assert gain.as_dict()["activation"] == 0.9


class TestSanitize:
    @pytest.mark.parametrize("raw", [None, True, "x", float("nan"), float("inf"), 0.0, -2.0])
    def test_bad_values_become_neutral(self, raw):
        assert sanitize_gain(raw) == 1.0

    def test_good_values_pass_through(self):
        assert sanitize_gain(1.6) == pytest.approx(1.6)
        assert sanitize_gain(0.4) == pytest.approx(0.4)
