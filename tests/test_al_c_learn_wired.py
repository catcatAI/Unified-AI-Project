"""Tests for the production wiring of C-learn (``scripts/al_c_learn_wired.py``).

`al_c_learn.py` proves the model method responds to a plasticity gain. This gate
checks the path the live chat actually takes -- ``GARDENEngine.learn_from_interaction``
and ``learn_batch`` -- and, just as importantly, that a broken or garbage rhythm
source leaves learning exactly where it was.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_c_learn_wired.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_c_learn_wired_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_learn_wired_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(gate):
    return gate.run()


class TestGate:
    def test_all_checks_pass(self, report):
        assert report["checks"] == {name: True for name in report["checks"]}
        assert report["verdict"] == "phase-reaches-learning-in-production"

    def test_the_two_paths_both_respond(self, report):
        assert report["single_path"]["max_weight_delta"] > 1e-9
        assert report["batch_path"]["max_weight_delta"] > 1e-9

    def test_control_and_repeat_are_exact(self, report):
        assert report["control_max_delta"] == 0.0
        assert report["repeat_max_delta"] == 0.0

    def test_delta_ratio_matches_the_gain_ratio(self, report):
        single = report["single_path"]
        assert (
            abs(single["delta_ratio"] - single["expected_ratio"]) / single["expected_ratio"] < 0.2
        )


class TestEngineWiring:
    def test_summary_reports_the_plasticity_it_used(self, gate):
        gate.set_rhythm_tracker(gate._FixedRhythm(0.98))
        try:
            engine = gate._engine()
            summary = engine.learn_from_interaction(
                "the ferry left the pier", "the ferry left the pier before dawn"
            )
        finally:
            gate.set_rhythm_tracker(None)
        assert summary["plasticity"] == pytest.approx(1.58, abs=0.01)

    def test_a_broken_source_stays_neutral(self, gate):
        gate.set_rhythm_tracker(gate._BrokenRhythm())
        try:
            engine = gate._engine()
            assert engine._plasticity_gain() == 1.0
        finally:
            gate.set_rhythm_tracker(None)
