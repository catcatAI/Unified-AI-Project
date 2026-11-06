"""Tests for the C-logit channel (``core/life/al_logit_bias.py``).

The module is pure: token ids in, offsets out. The tests pin the properties the
claim rests on -- zero at the midpoint (so "no preference" and "mid-cycle" agree),
symmetric at the extremes, unobserved on bad input, and no mutation of the caller's
scores (a subtle way to make a measurement lie).
"""

from __future__ import annotations

import pytest

from core.life.al_logit_bias import DEFAULT_STRENGTH, apply_to, phase_bias

ENERGY = (11, 12)
CALM = (21, 22)


def test_midpoint_is_exactly_zero():
    bias = phase_bias(0.5, ENERGY, CALM)
    assert set(bias.biases) == set(ENERGY) | set(CALM)
    assert all(v == 0.0 for v in bias.biases.values())


def test_extremes_are_symmetric_and_opposite():
    low = phase_bias(0.0, ENERGY, CALM)
    high = phase_bias(1.0, ENERGY, CALM)
    for token in ENERGY:
        assert low.biases[token] == pytest.approx(-DEFAULT_STRENGTH)
        assert high.biases[token] == pytest.approx(DEFAULT_STRENGTH)
        assert low.biases[token] == pytest.approx(-high.biases[token])
    for token in CALM:
        assert low.biases[token] == pytest.approx(DEFAULT_STRENGTH)
        assert high.biases[token] == pytest.approx(-DEFAULT_STRENGTH)


@pytest.mark.parametrize("bad", [None, True, "not-a-number", float("nan")])
def test_bad_activation_is_unobserved(bad):
    bias = phase_bias(bad, ENERGY, CALM)
    assert bias.is_empty and bias.source is None
    assert bias.as_dict()["max_abs"] == 0.0


def test_activation_is_clamped():
    assert phase_bias(7.0, ENERGY, []).activation == 1.0
    assert phase_bias(-3.0, ENERGY, []).activation == 0.0


def test_apply_does_not_mutate_the_input():
    scores = [0.0] * 30
    out = apply_to(scores, phase_bias(1.0, ENERGY, CALM))
    assert scores == [0.0] * 30
    assert out[11] == pytest.approx(DEFAULT_STRENGTH)
    assert out[21] == pytest.approx(-DEFAULT_STRENGTH)
    assert out[0] == 0.0


def test_out_of_range_ids_are_ignored():
    out = apply_to([0.0, 0.0], phase_bias(1.0, (99,), ()))
    assert out == [0.0, 0.0]
    assert phase_bias(1.0, (99,), ()).biases[99] == pytest.approx(DEFAULT_STRENGTH)


def test_provenance_and_determinism():
    a = phase_bias(0.82, ENERGY, CALM)
    b = phase_bias(0.82, ENERGY, CALM)
    assert a == b
    payload = a.as_dict()
    assert payload["source"] == "core.life.al_oscillator"
    assert payload["max_abs"] == pytest.approx(0.64 * DEFAULT_STRENGTH, rel=1e-3)
