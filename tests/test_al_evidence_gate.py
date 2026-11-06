"""Tests for the aggregate evidence gate (``scripts/al_evidence_gate.py``).

The gate exists so the whole ladder can be re-run in one command, which only means
something if it can say no. These tests pin the three ways it must refuse: a rung
that reports no control check, a rung whose control check failed, and a rung whose
verdict drifted from the expected string.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_evidence_gate.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_evidence_gate_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_evidence_gate_test"] = module
    spec.loader.exec_module(module)
    return module


def _result(checks, verdict="ok-verdict", **extra):
    payload = {"checks": checks, "verdict": verdict}
    payload.update(extra)
    return payload


class TestRefusal:
    def test_no_control_check_is_not_evidence(self, gate):
        row = gate._evaluate("x", _result({"effect": True}), "ok-verdict")
        assert row["passed"] is False
        assert row["discipline"] == "no-control"

    def test_a_failed_control_fails_the_rung(self, gate):
        row = gate._evaluate(
            "x", _result({"effect": True, "control_is_identical": False}), "ok-verdict"
        )
        assert row["passed"] is False
        assert row["discipline"] == "control-failed"

    def test_a_drifted_verdict_fails_the_rung(self, gate):
        row = gate._evaluate(
            "x", _result({"effect": True, "control_is_identical": True}), "expected"
        )
        assert row["passed"] is False
        assert row["verdict"] == "ok-verdict"

    def test_a_failing_effect_check_fails_the_rung(self, gate):
        row = gate._evaluate(
            "x", _result({"weight_spread": False, "control_is_identical": True}), "ok-verdict"
        )
        assert row["passed"] is False


class TestAcceptance:
    def test_effect_plus_control_passes(self, gate):
        row = gate._evaluate(
            "x", _result({"effect": True, "control_is_identical": True}), "ok-verdict"
        )
        assert row["passed"] is True and row["discipline"] == "ok"

    def test_forgeries_must_fail(self, gate):
        forged = {"forgeries": {"table": {"passed": True}}, "main_ok": True, "verdict": "v"}
        row = gate._evaluate("x", forged, "v")
        assert row["passed"] is False
        assert [c["ok"] for c in row["controls"]] == [False]

    def test_power_cycle_controls_are_the_forgery_errors(self, gate):
        payload = {
            "passed": True,
            "error": 1e-9,
            "forgery_hold_error": 0.2,
            "forgery_reset_error": 0.3,
            "gap_seconds": 3.1,
        }
        row = gate._evaluate("x", payload, "")
        assert row["passed"] is True
        assert len(row["controls"]) == 2


class TestLadderTable:
    def test_every_rung_has_an_expected_verdict(self, gate):
        names = [name for name, _, _, _ in gate.RUNGS]
        assert names == [
            "rhythm-source",
            "power-cycle",
            "phase-effect",
            "c-param",
            "c-logit",
            "c-state",
            "c-learn",
            "c-learn-wired",
        ]
        expected = {name: expected for name, _, expected, _ in gate.RUNGS}
        assert expected["c-learn"] == "phase-decides-what-gets-kept"
        assert expected["c-learn-wired"] == "phase-reaches-learning-in-production"
