# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§83 contract tests: retraining the read at the evidence boundary.

Nothing here loads a carrier. The tests pin the registered device (two arms, one
zero-parameter forced-choice cell, the same label null, a fit pre-condition and a
no-regression check on §79's entry cells) and the arithmetic that turns stored
readings into a branch, so a tampered or stale report is refused without a
checkpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
READRULE83 = REPO_ROOT / "scripts" / "probe_pantry_readrule83.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def readrule83():
    return _load_module("pantry_readrule83_under_test", READRULE83)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_readrule83_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(readrule83):
    assert readrule83.ALPHA == 0.005
    assert readrule83.NULL_DRAWS == 400
    assert readrule83.NULL_SEED == 20261125
    assert readrule83.FORCED_FLOOR == 0.5
    assert readrule83.REF_TOLERANCE == 2e-9
    assert readrule83.ROSTER_ITEMS == 2
    assert readrule83.RULES == ("model", "cosine_unit")
    assert readrule83.PRIMARY_RULE == "model"


def test_the_budget_is_s77s_and_the_read_point_is_the_only_change(readrule83):
    assert readrule83.CONTROL_PARAMS == 168150
    assert readrule83.CONTROL_STEPS == 10000
    assert readrule83.FIT_FLOOR == 0.90
    assert "read_at" not in readrule83.BUDGET_KEYS
    assert "address" in readrule83.BUDGET_KEYS
    assert "write_slots" in readrule83.BUDGET_KEYS


def test_the_probe_hyperparameters_are_s79s(readrule83):
    assert readrule83.PROBE_STEPS == 2000
    assert readrule83.PROBE_BATCH == 64
    assert readrule83.PROBE_LR == 1e-3
    assert readrule83.PROBE_WEIGHT_DECAY == 1e-4
    assert readrule83.PROBE_SEED == 20261121


def test_the_control_anchor_is_s82s_boundary_query_column(readrule83):
    assert readrule83.CONTROL_WINS == {"model": 100, "cosine_unit": 101}
    assert readrule83.RULES_TEXT["model"].startswith("softmax(exp(scale)")
    assert "cosine" not in readrule83.RULES_TEXT["model"]


def test_the_branch_order_is_the_registered_one(readrule83):
    assert readrule83.BRANCH_ORDER == (
        "E0-instrument",
        "T0-fit-fails",
        "T2-pass-but-regression",
        "T1-read-at-boundary-works",
        "T3-no-gain",
    )


def test_the_registered_prediction_is_t1_with_t3_as_the_alternative(readrule83):
    assert readrule83.PREDICTION == "T1-read-at-boundary-works"
    assert readrule83.PREDICTION_ALTERNATIVE == "T3-no-gain"
    assert readrule83.PREDICTION != readrule83.PREDICTION_ALTERNATIVE


def test_the_stage_is_the_read_point_question(readrule83):
    assert "read point" in readrule83.STAGE
    assert "address" in readrule83.STAGE


# --------------------------------------------------------------------------- #
# the cells and their gates
# --------------------------------------------------------------------------- #
def _boundary_cell(split75, *, wins, n=4, ge=0, scale=1.0):
    items = [index % 2 for index in range(n)]
    # `wins` is derived from the masses; build the masses the win count describes
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
        "null": {"draws": 400, "seed": readrule83_seed(), "ge": ge, "wins": {"mean": 2.0}},
        "m0": m0,
        "m1": m1,
        "items": items,
        "roster_mass": {"mean": 1.0 * scale},
        "argmax_hist": {"2": n},
        "argmax_on_roster": 1.0,
    }


def readrule83_seed():
    return 20261125


def _fitted_cell(split75, *, wins, n=400, ge=0):
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
        "null": {"draws": 400, "seed": readrule83_seed(), "ge": ge, "forced": {"mean": 0.5}},
        "p_value": round((1 + ge) / 401, 6),
        "chance": {"forced": 0.5, "top1": 0.125},
    }


def test_a_boundary_cell_needs_a_wilson_floor_above_chance(readrule83, split75):
    assert readrule83._cell_block(_boundary_cell(split75, wins=4, ge=0))["pass"] is True
    # 2/4 with a perfect null is still not above chance
    assert readrule83._cell_block(_boundary_cell(split75, wins=2, ge=0))["pass"] is False


def test_a_boundary_cell_needs_the_permutation_to_fail(readrule83, split75):
    block = readrule83._cell_block(_boundary_cell(split75, wins=4, ge=400))
    assert block["wilson_low"] > 0.5
    assert block["p_value"] == round(401 / 401, 6)
    assert block["pass"] is False


def test_an_entry_cell_uses_the_same_gate_shape(readrule83, split75):
    passing = readrule83._entry_block(_fitted_cell(split75, wins=300, ge=0))
    assert passing["pass"] is True
    failing = readrule83._entry_block(_fitted_cell(split75, wins=300, ge=400))
    assert failing["pass"] is False
    assert readrule83._entry_block(_fitted_cell(split75, wins=200, ge=0))["pass"] is False


def test_the_fit_gate_is_the_registered_floor(readrule83):
    assert readrule83._fit_block({"results": {"train_fit_subset": {"exact": 0.90}}})["pass"]
    assert not readrule83._fit_block({"results": {"train_fit_subset": {"exact": 0.89}}})["pass"]
    assert not readrule83._fit_block({"results": {}})["pass"]
    assert readrule83._fit_block({"results": {"train_fit": {"exact": 0.95}}})[
        "pass"
    ]  # legacy key is the same subset at or below the cap


def test_the_fit_block_refuses_a_report_whose_own_gate_disagrees(readrule83):
    with pytest.raises(SystemExit):
        readrule83._fit_block(
            {
                "results": {"train_fit_subset": {"exact": 0.50}},
                "gates": {"G1_fits_the_subset": True},
            }
        )


# --------------------------------------------------------------------------- #
# the control anchor
# --------------------------------------------------------------------------- #
def _control_cells(readrule83, split75, *, wins=100, mass=1.0):
    return {
        "model": _boundary_cell(split75, wins=wins, n=200, ge=100, scale=mass),
        "cosine_unit": _boundary_cell(split75, wins=101, n=200, ge=220, scale=0.180198),
    }


def _anchor82(readrule83, split75):
    cells = _control_cells(readrule83, split75)
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
                for variant in readrule83.RULES
            }
        },
    }


def test_the_control_anchor_reproduces_s82_read_for_read(readrule83, split75):
    cells = _control_cells(readrule83, split75)
    anchor = readrule83.anchor_control(cells, _anchor82(readrule83, split75))
    assert anchor["pass"] is True
    assert anchor["model"]["wins"] == 100
    assert anchor["cosine_unit"]["wins"] == 101
    assert anchor["model"]["max_abs_diff"] == 0.0


def test_the_control_anchor_rejects_a_drifted_mass(readrule83, split75):
    cells = _control_cells(readrule83, split75)
    cells["model"]["m0"] = [value + 1e-6 for value in cells["model"]["m0"]]
    anchor = readrule83.anchor_control(cells, _anchor82(readrule83, split75))
    assert anchor["pass"] is False
    assert anchor["model"]["mismatches"] > 0
    assert anchor["model"]["max_abs_diff"] > readrule83.REF_TOLERANCE


def test_the_control_anchor_rejects_a_drifted_win_count(readrule83, split75):
    cells = _control_cells(readrule83, split75, wins=99)
    anchor = readrule83.anchor_control(cells, _anchor82(readrule83, split75))
    assert anchor["pass"] is False
    assert anchor["model"]["wins"] == 99


def test_the_control_anchor_rejects_a_win_count_that_is_not_the_registered_one(readrule83, split75):
    """A reproduced but different number is still not §82's cell."""
    cells = _control_cells(readrule83, split75)
    reference = _anchor82(readrule83, split75)
    reference["cells"]["boundary_query"]["model"]["wins"] = 102
    anchor = readrule83.anchor_control(cells, reference)
    assert anchor["pass"] is False
    assert anchor["model"]["registered_wins"] == 100


def test_the_control_anchor_refuses_a_different_heldout_set(readrule83, split75):
    cells = _control_cells(readrule83, split75)
    reference = _anchor82(readrule83, split75)
    reference["cells"]["boundary_query"]["model"]["items"] = [0, 1]
    with pytest.raises(SystemExit):
        readrule83.anchor_control(cells, reference)


# --------------------------------------------------------------------------- #
# the branch
# --------------------------------------------------------------------------- #
def _gates(
    readrule83,
    split75,
    *,
    instrument_pass=True,
    fit_pass=True,
    treatment_pass=True,
    regression_pass=True,
):
    return {
        "I0_instrument": {
            "pass": instrument_pass,
            "control_unchanged": True,
            "control_checkpoint_unchanged": True,
            "same_corpus": True,
            "same_budget": True,
            "budget": {"differences": []},
            "same_start": True,
            "start": {"differences": []},
            "treatment_is_the_read_rule": True,
            "alignment_pass": True,
            "control_anchor_reproduced": True,
        },
        "fit": {"pass": fit_pass},
        "treatment": {
            "model": {"pass": treatment_pass},
            "cosine_unit": {"pass": treatment_pass},
        },
        "no_regression": {"pass": regression_pass},
    }


def test_the_instrument_precedes_every_cell(readrule83, split75):
    gate = _gates(readrule83, split75, instrument_pass=False)
    assert readrule83.branch(gate)["id"] == "E0-instrument"


def test_the_fit_precondition_precedes_the_read(readrule83, split75):
    gate = _gates(readrule83, split75, fit_pass=False, treatment_pass=True)
    branch = readrule83.branch(gate)
    assert branch["id"] == "T0-fit-fails"
    assert "did not fit" in branch["reading"]


def test_a_passing_read_without_regression_is_t2(readrule83, split75):
    gate = _gates(readrule83, split75, treatment_pass=True, regression_pass=False)
    assert readrule83.branch(gate)["id"] == "T2-pass-but-regression"


def test_a_passing_read_with_regression_is_t1(readrule83, split75):
    gate = _gates(readrule83, split75, treatment_pass=True, regression_pass=True)
    branch = readrule83.branch(gate)
    assert branch["id"] == "T1-read-at-boundary-works"
    assert "same store" in branch["reading"]


def test_a_failing_read_is_t3(readrule83, split75):
    gate = _gates(readrule83, split75, treatment_pass=False, regression_pass=True)
    assert readrule83.branch(gate)["id"] == "T3-no-gain"


def test_the_descriptive_rule_does_not_carry_the_decision(readrule83, split75):
    """Only ``model`` is the gate; the unit rule is reported beside it."""
    gate = _gates(readrule83, split75, treatment_pass=False)
    gate["treatment"]["cosine_unit"]["pass"] = True
    assert readrule83.branch(gate)["id"] == "T3-no-gain"


def test_the_instrument_requires_the_same_start_and_the_same_budget(readrule83, split75):
    data = report(readrule83, split75)
    assert readrule83.gates(data)["I0_instrument"]["pass"] is True
    for term in ("same_start", "same_budget", "same_corpus", "treatment_is_the_read_rule"):
        tampered = report(readrule83, split75)
        tampered["instrument"][term] = False
        assert readrule83.gates(tampered)["I0_instrument"]["pass"] is False, term


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def report(
    readrule83,
    split75,
    *,
    instrument_pass=True,
    fit_pass=True,
    treatment_pass=True,
    regression_pass=True,
):
    fit_exact = 0.99 if fit_pass else 0.40
    cells = _control_cells(readrule83, split75)
    if treatment_pass:
        treatment = {
            "model": _boundary_cell(split75, wins=150, n=200, ge=0),
            "cosine_unit": _boundary_cell(split75, wins=150, n=200, ge=0),
        }
    else:
        treatment = {
            "model": _boundary_cell(split75, wins=100, n=200, ge=400),
            "cosine_unit": _boundary_cell(split75, wins=101, n=200, ge=220),
        }
    entry_wins = 300 if regression_pass else 200
    entry_ge = 0 if regression_pass else 400
    data = {
        "stage": readrule83.STAGE,
        "corpus": {"train_sessions": 400, "heldout_sessions": 200, "colours": 8},
        "decision": {
            "alpha": readrule83.ALPHA,
            "forced_floor": readrule83.FORCED_FLOOR,
            "null_draws": readrule83.NULL_DRAWS,
            "null_seed": readrule83.NULL_SEED,
            "anchor_tolerance": readrule83.REF_TOLERANCE,
            "primary_rule": readrule83.PRIMARY_RULE,
            "control_wins": dict(readrule83.CONTROL_WINS),
            "fit_floor": readrule83.FIT_FLOOR,
            "control_steps": readrule83.CONTROL_STEPS,
            "control_params": readrule83.CONTROL_PARAMS,
        },
        "fit": {
            "train_fit_subset_exact": fit_exact,
            "floor": readrule83.FIT_FLOOR,
            "pass": fit_exact >= readrule83.FIT_FLOOR,
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
            "control_anchor": readrule83.anchor_control(cells, _anchor82(readrule83, split75)),
        },
        "control": cells,
        "treatment": treatment,
        "no_regression": {
            "entry_key": _fitted_cell(split75, wins=entry_wins, ge=entry_ge),
            "entry_value": _fitted_cell(split75, wins=entry_wins, ge=entry_ge),
        },
    }
    if not instrument_pass:
        data["instrument"]["control_anchor"]["pass"] = False
        data["instrument"]["control_anchor"]["model"]["mismatches"] = 1
    data["gates"] = readrule83.gates(data)
    data["branch"] = readrule83.branch(data["gates"])
    data["prediction_hit"] = bool(data["branch"]["id"] == readrule83.PREDICTION)
    return data


def _write(tmp_path, data):
    path = tmp_path / "k3.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    assert data["branch"]["id"] == "T1-read-at-boundary-works"
    assert data["prediction_hit"] is True
    assert readrule83.check(_write(tmp_path, data)) == []


def test_a_failing_read_re_derives_to_t3(readrule83, split75, tmp_path):
    data = report(readrule83, split75, treatment_pass=False)
    assert data["branch"]["id"] == "T3-no-gain"
    assert data["prediction_hit"] is False
    assert readrule83.check(_write(tmp_path, data)) == []


def test_a_fit_miss_re_derives_to_t0(readrule83, split75, tmp_path):
    data = report(readrule83, split75, fit_pass=False)
    assert data["branch"]["id"] == "T0-fit-fails"
    assert readrule83.check(_write(tmp_path, data)) == []


def test_a_passing_read_with_regression_re_derives_to_t2(readrule83, split75, tmp_path):
    data = report(readrule83, split75, regression_pass=False)
    assert data["branch"]["id"] == "T2-pass-but-regression"
    assert readrule83.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_treatment_win_count(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["treatment"]["model"]["wins"] = 199
    problems = readrule83.check(_write(tmp_path, data))
    assert any("win count" in problem for problem in problems)


def test_the_check_rejects_a_tampered_forced_rate(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["treatment"]["model"]["forced"] = 0.99
    problems = readrule83.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["treatment"]["model"]["p_value"] = 0.0001
    problems = readrule83.check(_write(tmp_path, data))
    assert any("p_value" in problem for problem in problems)


def test_the_check_rejects_a_tampered_entry_cell(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["no_regression"]["entry_key"]["observed"]["forced_correct"] = 399
    problems = readrule83.check(_write(tmp_path, data))
    assert any("no_regression.entry_key" in problem for problem in problems)


def test_the_check_rejects_a_drifted_control_anchor(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["instrument"]["control_anchor"]["model"]["mismatches"] = 3
    problems = readrule83.check(_write(tmp_path, data))
    assert any("§82's model masses disagree" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(readrule83, split75, tmp_path):
    data = report(readrule83, split75, instrument_pass=False)
    problems = readrule83.check(_write(tmp_path, data))
    assert any("is not reproduced" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["branch"] = {"id": "T3-no-gain", "reading": "x", "next": "y"}
    problems = readrule83.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_tampered_prediction_hit(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["prediction_hit"] = False
    problems = readrule83.check(_write(tmp_path, data))
    assert any("prediction_hit" in problem for problem in problems)


def test_the_check_rejects_a_drifted_decision_constant(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["decision"]["alpha"] = 0.05
    problems = readrule83.check(_write(tmp_path, data))
    assert any("decision.alpha" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(readrule83, split75, tmp_path):
    data = report(readrule83, split75)
    data["stage"] = "§82 is the missing colour on the key side, the query side, or neither?"
    problems = readrule83.check(_write(tmp_path, data))
    assert problems == ["this is not a §83 report"]
