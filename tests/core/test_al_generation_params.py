"""Tests for C-param modulation (``core/life/al_generation_params.py``).

The module is the first place where AL state reaches a generation request, so the
tests pin the three properties the claim depends on: no rhythm means bit-identical
parameters, the swing is bounded and symmetric, and bad values count as unobserved
rather than as "at the trough" (a 0.0 activation must lower the temperature; a
string must change nothing).
"""

from __future__ import annotations

import pytest
from core.life.al_generation_params import (
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
    TEMPERATURE_SWING,
    TOKENS_MAX,
    TOKENS_MIN,
    _activation,
    modulate,
)


class _Snap:
    def __init__(self, rhythm):
        self.rhythm = rhythm


def test_absent_rhythm_is_bit_identical():
    out = modulate(0.7, 512, _Snap(None))
    assert (out.temperature, out.max_tokens, out.applied, out.source) == (0.7, 512, {}, None)


def test_activation_moves_both_parameters():
    cold = modulate(0.7, 512, _Snap({"activation": 0.0, "phase": 0.0}))
    hot = modulate(0.7, 512, _Snap({"activation": 1.0, "phase": 0.5}))
    assert cold.temperature == pytest.approx(0.7 - TEMPERATURE_SWING)
    assert hot.temperature == pytest.approx(0.7 + TEMPERATURE_SWING)
    assert cold.max_tokens < 512 < hot.max_tokens


def test_midpoint_is_neutral():
    out = modulate(0.7, 512, _Snap({"activation": 0.5}))
    assert out.temperature == pytest.approx(0.7)
    assert out.max_tokens == 512


def test_clamped_to_the_same_bounds_as_routing():
    out = modulate(TEMPERATURE_MAX, TOKENS_MAX, _Snap({"activation": 1.0}))
    assert out.temperature == TEMPERATURE_MAX
    assert out.max_tokens <= TOKENS_MAX
    low = modulate(TEMPERATURE_MIN, TOKENS_MIN, _Snap({"activation": 0.0}))
    assert low.temperature == TEMPERATURE_MIN
    assert low.max_tokens >= TOKENS_MIN


@pytest.mark.parametrize("bad", ["not-a-number", None, True, float("nan"), float("inf")])
def test_bad_activation_is_unobserved(bad):
    assert _activation(_Snap({"activation": bad})) is None
    out = modulate(0.7, 512, _Snap({"activation": bad}))
    assert out.temperature == 0.7 and out.max_tokens == 512


def test_provenance_is_recorded():
    out = modulate(0.7, 512, _Snap({"activation": 0.9}))
    assert out.source == "core.life.al_oscillator"
    assert out.applied["activation"] == 0.9
    assert out.applied["temperature_delta"] == pytest.approx(out.temperature - 0.7, abs=1e-4)
    assert set(out.as_dict()) == {"temperature", "max_tokens", "applied", "source"}


def test_deterministic():
    a = modulate(0.8, 700, _Snap({"activation": 0.33}))
    b = modulate(0.8, 700, _Snap({"activation": 0.33}))
    assert a == b
