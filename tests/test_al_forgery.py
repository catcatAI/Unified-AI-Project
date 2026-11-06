"""Tests for the AL anti-forgery gate (scripts/al_forgery.py).

The gate exists to stop a capability table from being read as a provenance
table, so what is pinned here is the gate's own discrimination:

1. an independent reimplementation of the rule passes every rung — that is the
   behavioural ceiling, and stating it is the point. If this ever failed, the
   "behaviour separates real from fake" claim would be true, and it is not;
2. a per-call decay (the diary-entry fake) is caught by the sampling rung even
   though it looks right at one message per day;
3. a rung whose ablation does *not* break it is reported as
   ``mechanism-not-load-bearing``, not as admissible;
4. a fake whose error can saturate to zero must not be able to pass — the
   regression that made the first version of the gate report r1 for
   ``call_clock`` as 0.0.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_forgery.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _load("al_forgery_test", SCRIPT)


def test_an_independent_reimplementation_passes_every_rung(gate):
    """Same rule, different code: behaviour cannot tell them apart."""
    clone = gate.CloneModel()
    rng = np.random.default_rng(2)
    assert gate.ladder.rung_semigroup([clone], rng)["clone"] <= gate.TOL
    assert gate.ladder.rung_sampling([clone], rng)["clone"] <= gate.TOL
    assert gate.ladder.rung_attractor([clone], rng)["clone"] <= gate.TOL
    assert gate.ladder.rung_inner_dt([clone], rng)["clone"] <= gate.TOL
    assert gate.ladder.rung_outer_dt([clone], rng)["clone"] <= gate.TOL


def test_per_call_decay_is_caught_by_the_sampling_rung(gate):
    call = gate.CallClockForgery()
    assert gate.ladder.rung_sampling([call], np.random.default_rng(4))["call_clock"] > gate.TOL


def test_a_rung_whose_ablation_does_not_break_it_is_not_admissible(gate):
    row = gate._row(
        {"al": 0.0, "clone": 0.0, "copy": 0.4, "const": 0.3},
        {"table_noise": 0.2, "call_clock": 0.2, "imitate": 0.2},
        ablated=0.0,  # removing the mechanism changed nothing
    )
    assert row["verdict"] == "mechanism-not-load-bearing"


def test_control_passing_blocks_admissibility(gate):
    row = gate._row(
        {"al": 0.0, "clone": 0.0, "copy": 0.0, "const": 0.3},
        {"table_noise": 0.2, "call_clock": 0.2, "imitate": 0.2},
        ablated=0.3,
    )
    assert row["verdict"] == "control-passes"
    assert row["controls_passing"] == ["copy"]


def test_a_fake_that_saturates_cannot_pass(gate):
    """Stateless echo: no accumulated state to decay to an accidental 0.0."""
    fake = gate.TableNoiseForgery()
    err = gate.ladder.rung_semigroup([fake], np.random.default_rng(6))["table_noise"]
    assert err > gate.TOL
    # Two calls on the same fake must not be confounded by its own history.
    st = gate.ar.AffectState(0.8, 0.8, 0.0)
    first = fake.step(st, 5.0).arousal
    second = fake.step(st, 5.0).arousal
    assert abs(first - second) < 0.2  # noise, not decay
