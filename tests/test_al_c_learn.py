"""Tests for the C-learn gate (``scripts/al_c_learn.py``).

The claim under test is narrow and checkable: with the same pairs, the same order
and the same ``lr``, the internal phase's plasticity gain decides how strongly the
pair is laid down, and an unwired caller (no ``plasticity``, ``1.0``, or a
malformed value) produces bit-identical weights.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_c_learn.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_c_learn_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_learn_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(gate):
    return gate.run()


class TestPlasticity:
    def test_default_matches_explicit_one(self, gate):
        core = gate._train([1.0])
        plain = gate._core()
        for src, tgt in gate.STREAM:
            plain.hebbian_update(
                {src: 1.0},
                {tgt: 1.0},
                lr=gate.LR,
                target_strength=gate.TARGET_STRENGTH,
                weight_decay=0.0,
            )
        assert gate._max_pointwise(gate._weights(core), gate._weights(plain)) == 0.0

    def test_malformed_gain_is_neutral(self, gate):
        neutral = gate._weights(gate._train([1.0]))
        for bad in (float("nan"), float("inf"), 0.0, -1.0, None, True):
            assert gate._max_pointwise(gate._weights(gate._train([bad])), neutral) == 0.0

    def test_high_gain_keeps_more_than_low_gain(self, gate):
        low = gate._train([0.4])
        high = gate._train([1.6])
        assert gate._mean_pair_weight(high) > gate._mean_pair_weight(low) + 0.3
        assert gate._consolidated(high) > gate._consolidated(low)

    def test_weights_are_ordered_by_gain(self, gate):
        means = [gate._mean_pair_weight(gate._train([gain])) for gain in (0.4, 0.7, 1.0, 1.3, 1.6)]
        assert means == sorted(means)

    def test_a_schedule_repeats_bit_for_bit(self, gate):
        schedule = gate._real_schedule(gate.natural_period())
        first = gate._weights(gate._train(schedule))
        second = gate._weights(gate._train(schedule))
        assert gate._max_pointwise(first, second) == 0.0


class TestVerdict:
    def test_all_checks_pass(self, report):
        assert report["checks"] == {name: True for name in report["checks"]}
        assert report["admissible"] is True
        assert report["verdict"] == "phase-decides-what-gets-kept"

    def test_control_is_exact(self, report):
        assert report["control_max_delta"] == 0.0
        assert report["bad_gain_max_delta"] == 0.0
        assert report["mid_control_gain"] == 1.0

    def test_eight_phases_reach_both_extremes(self, report):
        gains = [row["gain"] for row in report["rows"]]
        assert len(gains) == 8
        assert min(gains) < 0.5 and max(gains) > 1.5
        assert report["rho_mean_weight"] > 0.9
