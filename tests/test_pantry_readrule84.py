# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§84 contract tests: taking the read at the question boundary and holding it.

Nothing here loads a carrier. The tests pin the registered device (two arms, one
zero-parameter forced-choice cell, the same label null, a fit pre-condition, a
query-identity check and the no-regression cells) and the arithmetic that turns
stored readings into a branch, so a tampered or stale report is refused without
a checkpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
READRULE84 = REPO_ROOT / "scripts" / "probe_pantry_readrule84.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def readrule84():
    return _load_module("pantry_readrule84_under_test", READRULE84)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_readrule84_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(readrule84):
    assert readrule84.ALPHA == 0.005
    assert readrule84.NULL_DRAWS == 400
    assert readrule84.NULL_SEED == 20261125
    assert readrule84.FORCED_FLOOR == 0.5
    assert readrule84.REF_TOLERANCE == 2e-9
    assert readrule84.ROSTER_ITEMS == 2
    assert readrule84.RULES == ("model", "cosine_unit")
    assert readrule84.PRIMARY_RULE == "model"


def test_the_budget_is_s83s_and_the_read_point_is_the_only_change(readrule84):
    assert readrule84.CONTROL_PARAMS == 168150
    assert readrule84.CONTROL_STEPS == 10000
    assert readrule84.FIT_FLOOR == 0.90
    assert "read_at" not in readrule84.BUDGET_KEYS
    assert "address" in readrule84.BUDGET_KEYS
    assert "write_slots" in readrule84.BUDGET_KEYS


def test_the_instrument_anchor_is_s82s_boundary_query_column(readrule84):
    assert readrule84.CONTROL_WINS == {"model": 100, "cosine_unit": 101}
    assert "question boundary" in readrule84.RULES_TEXT["model"]
    assert "cosine" not in readrule84.RULES_TEXT["model"]


def test_the_branch_order_is_the_registered_one(readrule84):
    assert readrule84.BRANCH_ORDER == (
        "E0-instrument",
        "Q0-fit-fails",
        "Q2-pass-but-regression",
        "Q1-read-at-question-works",
        "Q3-fits-but-no-gain",
    )


def test_the_registered_prediction_is_q3_with_q0_as_the_alternative(readrule84):
    assert readrule84.PREDICTION == "Q3-fits-but-no-gain"
    assert readrule84.PREDICTION_ALTERNATIVE == "Q0-fit-fails"
    assert readrule84.PREDICTION != readrule84.PREDICTION_ALTERNATIVE


def test_the_stage_is_the_question_boundary_question(readrule84):
    assert "question boundary" in readrule84.STAGE
    assert "held" in readrule84.STAGE


# --------------------------------------------------------------------------- #
# the query identity
# --------------------------------------------------------------------------- #
class _Tensor:
    """The tiny slice of a tensor `query_identity` touches."""

    def __init__(self, values):
        self.values = list(values)

    def detach(self):
        return self

    def cpu(self):
        return self

    def __sub__(self, other):
        return _Tensor([left - right for left, right in zip(self.values, other.values)])

    def abs(self):
        return _Tensor([abs(value) for value in self.values])

    def max(self):
        return max(self.values) if self.values else 0.0

    def __eq__(self, other):
        return _Tensor([float(left == right) for left, right in zip(self.values, other.values)])

    def all(self):
        return all(bool(value) for value in self.values)


def _query_row(session_id, values):
    return {"session_id": session_id, "query": _Tensor(values)}


def test_query_identity_passes_when_the_query_is_unchanged(readrule84):
    token = [_query_row("a", [1.0, 2.0]), _query_row("b", [3.0, 4.0])]
    question = [_query_row("a", [1.0, 2.0]), _query_row("b", [3.0, 4.0])]
    identity = readrule84.query_identity(token, question)
    assert identity["pass"] is True
    assert identity["mismatches"] == 0
    assert identity["compared"] == 2


def test_query_identity_fails_when_the_projection_input_moved(readrule84):
    token = [_query_row("a", [1.0, 2.0])]
    question = [_query_row("a", [1.0, 2.0001])]
    identity = readrule84.query_identity(token, question)
    assert identity["pass"] is False
    assert identity["mismatches"] == 1
    assert identity["max_abs_diff"] > 0.0


def test_query_identity_fails_when_a_session_is_missing(readrule84):
    token = [_query_row("a", [1.0])]
    identity = readrule84.query_identity(token, [])
    assert identity["pass"] is False
    assert identity["compared"] == 0


# --------------------------------------------------------------------------- #
# the cells and their gates
# --------------------------------------------------------------------------- #
def _cell(split75, *, wins, n=4, ge=0, scale=1.0):
    items = [index % 2 for index in range(n)]
    m0, m1 = [], []
    for index, item in enumerate(items):
        correct_first = index < wins
        if item == 0:
            m0.append(1.0 if correct_first else 0.0)
            m1.append(0.0 if correct_first else 1.0)
        else:
            m0.append(0.0 if correct_first else 1.0)
            m1.append(1.0 if correct_first else 0.0)
    return {
        "variant": "x",
        "n": n,
        "wins": wins,
        "forced": round(wins / n, 6),
        "wilson": split75.wilson(wins, n),
        "p_value": round((1 + ge) / 401, 6),
        "null": {"draws": 400, "seed": 20261125, "ge": ge, "wins": {"mean": 2.0}},
        "m0": m0,
        "m1": m1,
        "items": items,
        "roster_mass": {"mean": 1.0 * scale},
        "argmax_hist": {"2": n},
        "argmax_on_roster": 1.0,
    }


def _fitted(split75, *, wins, n=400, ge=0):
    observed = {
        "n": n,
        "forced_correct": wins,
        "forced": round(wins / n, 6),
        "wilson": split75.wilson(wins, n),
        "top1": round(wins / n, 6),
        "top1_correct": wins,
    }
    return {
        "observed": observed,
        "null": {"draws": 400, "seed": 20261125, "ge": ge, "forced": {"mean": 0.5}},
        "p_value": round((1 + ge) / 401, 6),
        "chance": {"forced": 0.5, "top1": 0.125},
    }


def _control_cells(readrule84, split75, *, wins=100):
    return {
        "model": _cell(split75, wins=wins, n=200, ge=100, scale=1.0),
        "cosine_unit": _cell(split75, wins=101, n=200, ge=220, scale=0.180198),
    }


def _anchor82(readrule84, split75):
    cells = _control_cells(readrule84, split75)
    return {
        "stage": "§82 is the missing colour on the key side, the query side, or neither?",
        "cells": {
            "boundary_query": {
                variant: {
                    "m0": cells[variant]["m0"],
                    "m1": cells[variant]["m1"],
                    "items": cells[variant]["items"],
                    "wins": cells[variant]["wins"],
                    "roster_mass": cells[variant]["roster_mass"],
                }
                for variant in readrule84.RULES
            }
        },
    }


def _identity(pass_=True):
    return {
        "compared": 200,
        "mismatches": 0 if pass_ else 1,
        "max_abs_diff": 0.0 if pass_ else 1e-6,
        "tolerance": 2e-9,
        "pass": pass_,
    }


# --------------------------------------------------------------------------- #
# the branch
# --------------------------------------------------------------------------- #
def _gates(*, instrument_pass=True, fit_pass=True, treatment_pass=True, regression_pass=True):
    return {
        "I0_instrument": {"pass": instrument_pass},
        "fit": {"pass": fit_pass},
        "treatment": {
            "model": {"pass": treatment_pass},
            "cosine_unit": {"pass": treatment_pass},
        },
        "no_regression": {"pass": regression_pass},
    }


def test_the_instrument_precedes_every_cell(readrule84):
    gate = _gates(instrument_pass=False)
    assert readrule84.branch(gate)["id"] == "E0-instrument"


def test_the_fit_precondition_precedes_the_read(readrule84):
    gate = _gates(fit_pass=False, treatment_pass=True)
    branch = readrule84.branch(gate)
    assert branch["id"] == "Q0-fit-fails"
    assert "did not fit" in branch["reading"]


def test_a_passing_read_without_regression_is_q2(readrule84):
    gate = _gates(treatment_pass=True, regression_pass=False)
    assert readrule84.branch(gate)["id"] == "Q2-pass-but-regression"


def test_a_passing_read_with_regression_is_q1(readrule84):
    gate = _gates(treatment_pass=True, regression_pass=True)
    branch = readrule84.branch(gate)
    assert branch["id"] == "Q1-read-at-question-works"
    assert "question" in branch["reading"]


def test_a_failing_read_is_q3(readrule84):
    gate = _gates(treatment_pass=False, regression_pass=True)
    assert readrule84.branch(gate)["id"] == "Q3-fits-but-no-gain"


def test_the_descriptive_rule_does_not_carry_the_decision(readrule84):
    gate = _gates(treatment_pass=False)
    gate["treatment"]["cosine_unit"]["pass"] = True
    assert readrule84.branch(gate)["id"] == "Q3-fits-but-no-gain"


# --------------------------------------------------------------------------- #
# the instrument gate
# --------------------------------------------------------------------------- #
def report(
    readrule84,
    split75,
    *,
    instrument_pass=True,
    fit_pass=True,
    treatment_pass=False,
    regression_pass=True,
    query_identity_pass=True,
):
    fit_exact = 0.99 if fit_pass else 0.40
    cells = _control_cells(readrule84, split75)
    if treatment_pass:
        treatment = {
            "model": _cell(split75, wins=150, n=200, ge=0),
            "cosine_unit": _cell(split75, wins=150, n=200, ge=0),
        }
    else:
        treatment = {
            "model": _cell(split75, wins=100, n=200, ge=400),
            "cosine_unit": _cell(split75, wins=101, n=200, ge=220),
        }
    entry_wins = 300 if regression_pass else 200
    entry_ge = 0 if regression_pass else 400
    anchor = readrule84.load_readrule83().anchor_control(cells, _anchor82(readrule84, split75))
    if not instrument_pass:
        anchor["pass"] = False
        anchor["model"]["mismatches"] = 1
    data = {
        "stage": readrule84.STAGE,
        "corpus": {"train_sessions": 400, "heldout_sessions": 200, "colours": 8},
        "decision": {
            "alpha": readrule84.ALPHA,
            "forced_floor": readrule84.FORCED_FLOOR,
            "null_draws": readrule84.NULL_DRAWS,
            "null_seed": readrule84.NULL_SEED,
            "anchor_tolerance": readrule84.REF_TOLERANCE,
            "primary_rule": readrule84.PRIMARY_RULE,
            "control_wins": dict(readrule84.CONTROL_WINS),
            "fit_floor": readrule84.FIT_FLOOR,
            "control_steps": readrule84.CONTROL_STEPS,
            "control_params": readrule84.CONTROL_PARAMS,
        },
        "fit": {
            "train_fit_subset_exact": fit_exact,
            "floor": readrule84.FIT_FLOOR,
            "pass": fit_exact >= readrule84.FIT_FLOOR,
        },
        "instrument": {
            "control_unchanged": True,
            "control_checkpoint_unchanged": True,
            "same_corpus": True,
            "same_budget": True,
            "budget": {"differences": []},
            "same_start": True,
            "start": {"differences": []},
            "treatment_is_the_read_rule": True,
            "alignment": {"pass": True},
            "control_anchor": anchor,
            "query_identity": _identity(query_identity_pass),
        },
        "control": cells,
        "treatment": treatment,
        "no_regression": {
            "entry_key": _fitted(split75, wins=entry_wins, ge=entry_ge),
            "entry_value": _fitted(split75, wins=entry_wins, ge=entry_ge),
        },
    }
    data["gates"] = readrule84.gates(data)
    data["branch"] = readrule84.branch(data["gates"])
    data["prediction_hit"] = bool(data["branch"]["id"] == readrule84.PREDICTION)
    return data


def test_the_instrument_requires_the_same_start_and_the_same_budget(readrule84, split75):
    data = report(readrule84, split75)
    assert readrule84.gates(data)["I0_instrument"]["pass"] is True
    for term in ("same_start", "same_budget", "same_corpus", "treatment_is_the_read_rule"):
        tampered = report(readrule84, split75)
        tampered["instrument"][term] = False
        assert readrule84.gates(tampered)["I0_instrument"]["pass"] is False, term


def test_the_instrument_requires_the_query_identity(readrule84, split75):
    data = report(readrule84, split75, query_identity_pass=False)
    assert readrule84.gates(data)["I0_instrument"]["pass"] is False


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _write(tmp_path, data):
    path = tmp_path / "k4.json"
    path.write_text(
        json.dumps(data, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return path


def test_a_coherent_report_passes_the_check(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    assert data["branch"]["id"] == "Q3-fits-but-no-gain"
    assert data["prediction_hit"] is True
    assert readrule84.check(_write(tmp_path, data)) == []


def test_a_passing_read_coherence_re_derives_to_q1(readrule84, split75, tmp_path):
    data = report(readrule84, split75, treatment_pass=True)
    assert data["branch"]["id"] == "Q1-read-at-question-works"
    assert data["prediction_hit"] is False
    assert readrule84.check(_write(tmp_path, data)) == []


def test_a_fit_miss_re_derives_to_q0(readrule84, split75, tmp_path):
    data = report(readrule84, split75, fit_pass=False)
    assert data["branch"]["id"] == "Q0-fit-fails"
    assert readrule84.check(_write(tmp_path, data)) == []


def test_a_passing_read_with_regression_re_derives_to_q2(readrule84, split75, tmp_path):
    data = report(readrule84, split75, treatment_pass=True, regression_pass=False)
    assert data["branch"]["id"] == "Q2-pass-but-regression"
    assert readrule84.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_treatment_win_count(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["treatment"]["model"]["wins"] = 199
    problems = readrule84.check(_write(tmp_path, data))
    assert any("win count" in problem for problem in problems)


def test_the_check_rejects_a_tampered_forced_rate(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["treatment"]["model"]["forced"] = 0.99
    problems = readrule84.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["treatment"]["model"]["p_value"] = 0.0001
    problems = readrule84.check(_write(tmp_path, data))
    assert any("p_value" in problem for problem in problems)


def test_the_check_rejects_a_tampered_entry_cell(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["no_regression"]["entry_key"]["observed"]["forced_correct"] = 399
    problems = readrule84.check(_write(tmp_path, data))
    assert any("no_regression.entry_key" in problem for problem in problems)


def test_the_check_rejects_a_drifted_control_anchor(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["instrument"]["control_anchor"]["model"]["mismatches"] = 3
    problems = readrule84.check(_write(tmp_path, data))
    assert any("§82's model masses disagree" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(readrule84, split75, tmp_path):
    data = report(readrule84, split75, instrument_pass=False)
    problems = readrule84.check(_write(tmp_path, data))
    assert any("is not reproduced" in problem for problem in problems)


def test_the_check_rejects_an_inconsistent_query_identity(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["instrument"]["query_identity"]["pass"] = True
    data["instrument"]["query_identity"]["mismatches"] = 2
    problems = readrule84.check(_write(tmp_path, data))
    assert any("query identity" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["branch"] = {"id": "Q1-read-at-question-works", "reading": "x", "next": "y"}
    problems = readrule84.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_tampered_prediction_hit(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["prediction_hit"] = False
    problems = readrule84.check(_write(tmp_path, data))
    assert any("prediction_hit" in problem for problem in problems)


def test_the_check_rejects_a_drifted_decision_constant(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["decision"]["alpha"] = 0.05
    problems = readrule84.check(_write(tmp_path, data))
    assert any("decision.alpha" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(readrule84, split75, tmp_path):
    data = report(readrule84, split75)
    data["stage"] = "§83 does the read point, retrained at the same budget, make the read address?"
    problems = readrule84.check(_write(tmp_path, data))
    assert problems == ["this is not a §84 report"]
