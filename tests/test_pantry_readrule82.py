# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§82 contract tests: which side lost the colour.

Nothing here loads a carrier. The tests pin the registered device (two fitted
probe cells, one anchor cell and one zero-parameter boundary read, the same
two-way forced choice, the same label null) and the arithmetic that turns stored
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
READRULE82 = REPO_ROOT / "scripts" / "probe_pantry_readrule82.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def readrule82():
    return _load_module("pantry_readrule82_under_test", READRULE82)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_readrule82_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(readrule82):
    assert readrule82.ALPHA == 0.005
    assert readrule82.NULL_DRAWS == 400
    assert readrule82.NULL_SEED == 20261125
    assert readrule82.FORCED_FLOOR == 0.5
    assert readrule82.ENTRY_COVERAGE == 0.99
    assert readrule82.ENTRY_COSINE == 0.999
    assert readrule82.REF_TOLERANCE == 2e-9
    assert readrule82.ROSTER_ITEMS == 2
    assert readrule82.BOUNDARY_RULES == ("model", "cosine_unit")


def test_the_anchor_constants_are_s79_and_s81s_measurements(readrule82):
    assert readrule82.ANCHOR79_FORCED == 0.62
    assert readrule82.ANCHOR79_WINS == 248
    assert readrule82.ANCHOR79_N == 400
    assert readrule82.ANCHOR81_WINS == 100


def test_the_probe_hyperparameters_are_s79s(readrule82):
    assert readrule82.PROBE_STEPS == 2000
    assert readrule82.PROBE_BATCH == 64
    assert readrule82.PROBE_LR == 1e-3
    assert readrule82.PROBE_WEIGHT_DECAY == 1e-4
    assert readrule82.PROBE_SEED == 20261121


def test_the_branch_order_is_the_registered_one(readrule82):
    assert readrule82.BRANCH_ORDER == (
        "E0-instrument",
        "C1-state-addresses",
        "C4-write-side-keys-lack-colour",
        "C2-both-sides-carry-colour",
        "C3-query-missing",
    )


def test_the_registered_prediction_is_c3_with_c1_as_the_alternative(readrule82):
    assert readrule82.PREDICTION == "C3-query-missing"
    assert readrule82.PREDICTION_ALTERNATIVE == "C1-state-addresses"
    assert readrule82.PREDICTION in readrule82.BRANCH_ORDER


def test_the_boundary_rules_are_the_two_registered_ones(readrule82):
    assert set(readrule82.RULES) == set(readrule82.BOUNDARY_RULES)
    for text in readrule82.RULES.values():
        assert "q_b" in text


def test_the_stage_says_which_side_lost_the_colour(readrule82):
    assert "key side" in readrule82.STAGE
    assert "query side" in readrule82.STAGE


# --------------------------------------------------------------------------- #
# the gate shapes
# --------------------------------------------------------------------------- #
def _probe_cell(wins, n, ge):
    observed = {"n": n, "forced_correct": wins, "forced": round(wins / n, 6)}
    return {
        "observed": observed,
        "null": {"draws": 400, "seed": 20261125, "ge": ge},
        "p_value": round((1 + ge) / 401, 6),
    }


def test_a_fitted_cell_needs_a_wilson_floor_above_chance(readrule82, split75):
    block = _probe_cell(400, 400, 0)
    block["observed"]["wilson"] = split75.wilson(400, 400)
    assert readrule82.probe_pass(block) is True
    block["observed"]["wilson"] = split75.wilson(200, 400)
    assert readrule82.probe_pass(block) is False


def test_a_fitted_cell_needs_the_permutation_to_fail(readrule82, split75):
    block = _probe_cell(400, 400, 0)
    block["observed"]["wilson"] = split75.wilson(400, 400)
    assert readrule82.probe_pass(block) is True
    block["p_value"] = 0.5
    assert readrule82.probe_pass(block) is False


def test_an_unfitted_read_uses_the_same_gate_shape(readrule82, split75):
    block = {"wilson": split75.wilson(200, 200), "p_value": round(1 / 401, 6)}
    assert readrule82.read_pass(block) is True
    block = {"wilson": split75.wilson(100, 200), "p_value": round(1 / 401, 6)}
    assert readrule82.read_pass(block) is False


# --------------------------------------------------------------------------- #
# the branch precedence
# --------------------------------------------------------------------------- #
def gate(*, instrument=True, entry_key=False, query=False, model=False, unit=False):
    return {
        "I0_instrument": {"pass": instrument},
        "cells": {
            "entry_key": {"pass": entry_key},
            "query": {"pass": query},
            "boundary_query": {
                "model": {"pass": model},
                "cosine_unit": {"pass": unit},
            },
        },
    }


def test_the_five_branches(readrule82):
    assert readrule82.branch(gate(instrument=False, model=True))["id"] == "E0-instrument"
    assert readrule82.branch(gate(entry_key=True, query=True, model=True))["id"] == (
        "C1-state-addresses"
    )
    assert readrule82.branch(gate(entry_key=False, query=True))["id"] == (
        "C4-write-side-keys-lack-colour"
    )
    assert readrule82.branch(gate(entry_key=True, query=True))["id"] == (
        "C2-both-sides-carry-colour"
    )
    assert readrule82.branch(gate(entry_key=True, query=False))["id"] == "C3-query-missing"


def test_the_unit_rule_alone_also_reaches_the_state_branch(readrule82):
    assert readrule82.branch(gate(entry_key=True, query=False, unit=True))["id"] == (
        "C1-state-addresses"
    )


def test_the_instrument_precedes_every_cell(readrule82):
    failure = gate(instrument=False, entry_key=True, query=True, model=True, unit=True)
    assert readrule82.branch(failure)["id"] == "E0-instrument"
    assert "nothing is read" in readrule82.branch(failure)["reading"]


def test_the_state_branch_precedes_the_write_side_one(readrule82):
    assert readrule82.branch(gate(entry_key=False, model=True))["id"] == "C1-state-addresses"


def test_the_write_side_branch_precedes_both_sides(readrule82):
    assert readrule82.branch(gate(entry_key=False, query=True))["id"] == (
        "C4-write-side-keys-lack-colour"
    )


def test_the_branch_readings_name_the_registered_next_step(readrule82):
    assert "boundary query" in readrule82.branch(gate(model=True))["next"]
    assert "write-side" in readrule82.branch(gate(entry_key=False))["next"]
    assert "learned metric" in readrule82.branch(gate(entry_key=True, query=True))["next"]
    assert "where the query comes from" in readrule82.branch(gate(entry_key=True))["next"]


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _boundary_cell(readrule82, split75, *, perfect):
    items = [0, 1, 0, 1]
    if perfect:
        m0, m1 = [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0]
        wins = 4
        ge = 0
    else:
        m0, m1 = [0.0] * 4, [1.0] * 4
        wins = 2
        ge = 400
    n = len(items)
    return {
        "variant": "x",
        "n": n,
        "wins": wins,
        "forced": round(wins / n, 6),
        "wilson": split75.wilson(wins, n),
        "p_value": round((1 + ge) / 401, 6),
        "null": {"draws": 400, "seed": readrule82.NULL_SEED, "ge": ge, "wins": {"mean": 2.0}},
        "m0": m0,
        "m1": m1,
        "items": items,
        "roster_mass": {"mean": 0.5},
        "argmax_hist": {"2": n},
        "argmax_on_roster": 1.0,
    }


def _fitted_cell(readrule82, split75, *, wins, n=400, ge=0):
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
        "null": {"draws": 400, "seed": readrule82.NULL_SEED, "ge": ge, "forced": {"mean": 0.5}},
        "p_value": round((1 + ge) / 401, 6),
        "chance": {"forced": 0.5, "top1": 0.125},
    }


def report(readrule82, split75, *, entry_key_pass=True, query_pass=False, boundary_pass=False):
    entry_key = _fitted_cell(
        readrule82, split75, wins=400 if entry_key_pass else 200, ge=0 if entry_key_pass else 400
    )
    query = _fitted_cell(
        readrule82, split75, wins=400 if query_pass else 200, n=400, ge=0 if query_pass else 400
    )
    value = _fitted_cell(readrule82, split75, wins=248, n=400, ge=0)
    boundary = {
        "model": _boundary_cell(readrule82, split75, perfect=boundary_pass),
        "cosine_unit": _boundary_cell(readrule82, split75, perfect=boundary_pass),
    }
    data = {
        "stage": readrule82.STAGE,
        "corpus": {"train_sessions": 400, "heldout_sessions": 200, "colours": 8},
        "decision": {
            "alpha": readrule82.ALPHA,
            "forced_floor": readrule82.FORCED_FLOOR,
            "null_draws": readrule82.NULL_DRAWS,
            "null_seed": readrule82.NULL_SEED,
            "anchor_tolerance": readrule82.REF_TOLERANCE,
            "anchor79_forced": readrule82.ANCHOR79_FORCED,
            "anchor79_wins": readrule82.ANCHOR79_WINS,
            "anchor79_n": readrule82.ANCHOR79_N,
            "anchor81_wins": readrule82.ANCHOR81_WINS,
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "mode_matches": True,
            "corpus_digests_match": True,
            "alignment": {"pass": True},
            "entry_audit": {"train": {"coverage": 1.0}, "heldout": {"coverage": 1.0}},
            "read_audit": {"train": {"coverage": 1.0}, "heldout": {"coverage": 1.0}},
            "anchor79": {"reproduced": True, "forced": 0.62, "wins": 248},
            "anchor81": {
                "reproduced": True,
                "max_abs_diff": 0.0,
                "mismatches": 0,
                "wins": 100,
                "stored_wins": 100,
            },
        },
        "cells": {
            "entry_key": entry_key,
            "entry_value": value,
            "query": query,
            "boundary_query": boundary,
        },
    }
    data["gates"] = readrule82.gates(data)
    data["branch"] = readrule82.branch(data["gates"])
    data["prediction_hit"] = bool(data["branch"]["id"] == readrule82.PREDICTION)
    return data


def _write(tmp_path, data):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    assert data["branch"]["id"] == "C3-query-missing"
    assert readrule82.check(_write(tmp_path, data)) == []


def test_a_coherent_state_reading_re_derives_to_c1(readrule82, split75, tmp_path):
    data = report(readrule82, split75, boundary_pass=True)
    assert data["branch"]["id"] == "C1-state-addresses"
    assert data["prediction_hit"] is False
    assert readrule82.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_forced_rate(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["cells"]["entry_key"]["observed"]["forced"] = 0.99
    problems = readrule82.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["cells"]["query"]["p_value"] = 0.5
    problems = readrule82.check(_write(tmp_path, data))
    assert any("permutation convention" in problem for problem in problems)


def test_the_check_rejects_a_tampered_boundary_win_count(readrule82, split75, tmp_path):
    data = report(readrule82, split75, boundary_pass=True)
    data["cells"]["boundary_query"]["model"]["wins"] = 3
    problems = readrule82.check(_write(tmp_path, data))
    assert any("win count is not re-derivable" in problem for problem in problems)


def test_the_check_rejects_a_boundary_cell_without_mass_pairs(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["cells"]["boundary_query"]["cosine_unit"]["m1"] = [1.0]
    problems = readrule82.check(_write(tmp_path, data))
    assert any("one pair per read" in problem for problem in problems)


def test_the_check_rejects_a_drifted_entry_value_anchor(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["instrument"]["anchor79"]["reproduced"] = False
    problems = readrule82.check(_write(tmp_path, data))
    assert any("value-to-colour cell is not reproduced" in problem for problem in problems)


def test_the_check_rejects_a_drifted_model_mass_anchor(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["instrument"]["anchor81"]["max_abs_diff"] = 1e-6
    problems = readrule82.check(_write(tmp_path, data))
    assert any("exceed the tolerance" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["branch"]["id"] = "C1-state-addresses"
    problems = readrule82.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_tampered_prediction_hit(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["prediction_hit"] = not data["prediction_hit"]
    problems = readrule82.check(_write(tmp_path, data))
    assert any("prediction_hit does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["instrument"]["read_audit"]["train"]["coverage"] = 0.5
    problems = readrule82.check(_write(tmp_path, data))
    assert any("I0_instrument does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_drifted_decision_constant(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["decision"]["anchor79_forced"] = 0.7375
    problems = readrule82.check(_write(tmp_path, data))
    assert any("decision.anchor79_forced" in problem for problem in problems)


def test_the_check_rejects_a_missing_entry_value_cell(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["cells"]["entry_value"] = {"observed": {"n": 0}}
    problems = readrule82.check(_write(tmp_path, data))
    assert any("entry_value: no observed reads" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(readrule82, split75, tmp_path):
    data = report(readrule82, split75)
    data["stage"] = "§81 something else"
    assert readrule82.check(_write(tmp_path, data)) == ["this is not a §82 report"]
