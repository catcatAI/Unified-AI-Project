# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§81 contract tests: the same reads under three read rules.

Nothing here loads a carrier. The tests pin the registered device (three rules
that differ only in what they normalise, the same two-way forced choice, the
same label null, the train-only twin swap, the query re-pairing) and the
arithmetic that turns stored readings into a branch, so a tampered or stale
report is refused without a checkpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
READRULE81 = REPO_ROOT / "scripts" / "probe_pantry_readrule81.py"
ADDRESS80 = REPO_ROOT / "scripts" / "probe_pantry_address80.py"
COMPOSITION = REPO_ROOT / "scripts" / "probe_pantry_composition.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def readrule81():
    return _load_module("pantry_readrule81_under_test", READRULE81)


@pytest.fixture(scope="module")
def composition():
    return _load_module("pantry_readrule81_composition_under_test", COMPOSITION)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_readrule81_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(readrule81):
    assert readrule81.ALPHA == 0.005
    assert readrule81.NULL_DRAWS == 400
    assert readrule81.NULL_SEED == 20261125
    assert readrule81.FORCED_FLOOR == 0.5
    assert readrule81.SW_MOVE_FLOOR == 0.01
    assert readrule81.ENTRY_COVERAGE == 0.99
    assert readrule81.ENTRY_COSINE == 0.999
    assert readrule81.REF_TOLERANCE == 2e-9
    assert readrule81.ROSTER_ITEMS == 2
    assert readrule81.VARIANTS == ("model", "cosine", "cosine_unit")


def test_the_branch_order_is_the_registered_one(readrule81):
    assert readrule81.BRANCH_ORDER == (
        "E0-instrument",
        "N1-norm-race-is-the-limit",
        "N2-saturation-is-the-limit",
        "N3-keys-do-not-address",
    )


def test_the_three_rules_differ_only_in_normalisation(readrule81):
    keys = torch.tensor([[3.0, 0.0], [0.0, 1.0]])
    query = torch.tensor([1.0, 0.0])
    scale = torch.tensor(4.0)
    model = readrule81.rule_weights(torch, keys, query, scale, "model")
    cosine = readrule81.rule_weights(torch, keys, query, scale, "cosine")
    unit = readrule81.rule_weights(torch, keys, query, scale, "cosine_unit")
    assert model[0] > cosine[0] > unit[0]
    assert float(model.sum()) == pytest.approx(1.0, abs=1e-6)
    assert float(cosine.sum()) == pytest.approx(1.0, abs=1e-6)
    assert float(unit.sum()) == pytest.approx(1.0, abs=1e-6)


def test_the_cosine_rule_ignores_a_rescaled_key(readrule81):
    query = torch.tensor([1.0, 0.5])
    scale = torch.tensor(4.0)
    small = readrule81.rule_weights(
        torch, torch.tensor([[1.0, 0.0], [0.0, 2.0]]), query, scale, "cosine"
    )
    large = readrule81.rule_weights(
        torch, torch.tensor([[7.0, 0.0], [0.0, 9.0]]), query, scale, "cosine"
    )
    assert torch.allclose(small, large, atol=1e-6)


def test_the_unit_rule_ignores_the_learned_scale(readrule81):
    keys = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    query = torch.tensor([1.0, 0.2])
    first = readrule81.rule_weights(torch, keys, query, torch.tensor(4.0), "cosine_unit")
    second = readrule81.rule_weights(torch, keys, query, torch.tensor(9.0), "cosine_unit")
    assert torch.allclose(first, second, atol=1e-9)


def test_an_unknown_rule_is_refused(readrule81):
    with pytest.raises(SystemExit):
        readrule81.rule_weights(torch, torch.ones(2, 2), torch.ones(2), torch.tensor(1.0), "dot")


# --------------------------------------------------------------------------- #
# the scored cell, built from keys and a query
# --------------------------------------------------------------------------- #
def record(
    item,
    first_norm,
    second_norm,
    *,
    structure="s",
    twin=False,
    query=(1.0, 0.0),
    axis2=(0.0, 1.0),
):
    keys = torch.zeros(16, 2)
    keys[1] = torch.tensor([float(first_norm), 0.0])
    keys[2] = torch.tensor(
        [float(second_norm) * float(axis2[0]), float(second_norm) * float(axis2[1])]
    )
    values = torch.zeros(16, 2)
    return {
        "session_id": structure,
        "structure": structure,
        "twin": twin,
        "item": item,
        "slots": [1, 2],
        "keys": keys,
        "values": values,
        "query": torch.tensor([float(query[0]), float(query[1])]),
        "v_roster": torch.zeros(2, 2),
        "key_norms": [float(first_norm), float(second_norm)],
    }


def _fixed_slot_records():
    return [record(item, 1.0, 100.0, axis2=(1.0, 0.0)) for item in (0, 1, 0, 1)]


def test_a_fixed_slot_read_scores_exactly_chance(readrule81, composition, split75):
    block = readrule81.address_block(
        torch, split75, composition, _fixed_slot_records(), torch.tensor(4.0), "model"
    )
    assert block["n"] == 4
    assert block["wins"] == 2
    assert block["forced"] == 0.5
    assert block["argmax_hist"] == {"2": 4}
    assert block["argmax_on_roster"] == 1.0
    assert block["null"]["ge"] == 400
    assert block["p_value"] == pytest.approx(1.0)


def test_a_read_that_picks_the_needed_entry_wins(readrule81, composition, split75):
    records = []
    for item in (0, 1) * 20:
        records.append(
            record(item, 100.0, 1.0, axis2=(1.0, 0.0))
            if item == 0
            else record(item, 1.0, 100.0, axis2=(1.0, 0.0))
        )
    block = readrule81.address_block(
        torch, split75, composition, records, torch.tensor(4.0), "model"
    )
    assert block["wins"] == 40
    assert block["forced"] == 1.0
    assert block["null"]["ge"] == 0
    assert block["p_value"] == round(1 / 401, 6)


def test_the_forced_choice_is_a_strict_comparison(readrule81, composition, split75):
    tie = record(0, 1.0, 1.0, axis2=(1.0, 0.0))
    assert torch.equal(tie["keys"][1], tie["keys"][2])
    block = readrule81.address_block(
        torch,
        split75,
        composition,
        [tie, record(1, 1.0, 1.0, axis2=(1.0, 0.0))],
        torch.tensor(4.0),
        "model",
    )
    assert block["wins"] == 0


# --------------------------------------------------------------------------- #
# the mechanism control: twin swap
# --------------------------------------------------------------------------- #
def test_swap_is_zero_when_the_read_is_a_fixed_slot(readrule81):
    left = record(0, 1.0, 100.0, structure="a", axis2=(1.0, 0.0))
    right = record(1, 1.0, 100.0, structure="a", axis2=(1.0, 0.0))
    block = readrule81.swap_block(torch, [left, right], torch.tensor(4.0), "model")
    assert block["pairs"] == 1
    assert block["tw"]["mean"] == 0.0
    assert block["moves"] is False


def test_swap_is_one_when_the_read_follows_the_needed_entry(readrule81):
    left = record(0, 100.0, 1.0, structure="a", axis2=(1.0, 0.0))
    right = record(1, 1.0, 100.0, structure="a", axis2=(1.0, 0.0))
    block = readrule81.swap_block(torch, [left, right], torch.tensor(4.0), "model")
    assert block["tw"]["mean"] > 0.99
    assert block["moves"] is True


def test_swap_refuses_twins_that_do_not_flip_the_needed_entry(readrule81):
    left = record(0, 1.0, 100.0, structure="a", axis2=(1.0, 0.0))
    right = record(0, 1.0, 100.0, structure="a", axis2=(1.0, 0.0))
    block = readrule81.swap_block(torch, [left, right], torch.tensor(4.0), "model")
    assert block["pairs"] == 0
    assert block["moves"] is False
    assert block["failures"]


# --------------------------------------------------------------------------- #
# the query re-pairing
# --------------------------------------------------------------------------- #
def test_the_query_re_pairing_keeps_a_fixed_slot_winning(readrule81, composition, split75):
    records = [record(item, 1.0, 100.0, axis2=(1.0, 0.0)) for item in (0, 1, 0, 1)]
    block = readrule81.query_block(
        torch, split75, composition, records, torch.tensor(4.0), "model", draws=20
    )
    assert block["wins"] == 2
    assert block["null"]["ge"] == 20


def test_the_query_re_pairing_costs_a_query_driven_read(readrule81, composition, split75):
    records = []
    for _ in range(10):
        records.append(record(0, 1.0, 1.0, query=(1.0, 0.0)))
        records.append(record(1, 1.0, 1.0, query=(0.0, 1.0)))
    block = readrule81.query_block(
        torch, split75, composition, records, torch.tensor(4.0), "model", draws=20
    )
    assert block["wins"] == 20
    assert block["null"]["ge"] == 0
    assert block["p_value"] == round(1 / 21, 6)


# --------------------------------------------------------------------------- #
# the anchor: the model rule is §80's stored read
# --------------------------------------------------------------------------- #
def _anchor_payload(readrule81, reads=2):
    return {
        "stage": readrule81.ADDRESS.STAGE,
        "address": {
            "n": reads,
            "wins": 1,
            "m0": [0.0] * reads,
            "m1": [1.0] * reads,
            "items": [0, 1][:reads],
        },
    }


def test_the_anchor_accepts_an_identical_read(readrule81):
    records = [record(item, 1.0, 100.0, axis2=(1.0, 0.0)) for item in (0, 1)]
    block = readrule81.anchor_block(torch, records, torch.tensor(4.0), _anchor_payload(readrule81))
    assert block["reproduced"] is True
    assert block["mismatches"] == 0
    assert block["wins"] == block["stored_wins"]


def test_the_anchor_refuses_a_different_mass(readrule81):
    records = [record(item, 1.0, 1.0, axis2=(1.0, 0.0)) for item in (0, 1)]
    block = readrule81.anchor_block(torch, records, torch.tensor(4.0), _anchor_payload(readrule81))
    assert block["reproduced"] is False
    assert block["mismatches"] == 2


def test_the_anchor_refuses_a_different_held_out_set(readrule81):
    records = [record(0, 1.0, 100.0, axis2=(1.0, 0.0))]
    with pytest.raises(SystemExit):
        readrule81.anchor_block(torch, records, torch.tensor(4.0), _anchor_payload(readrule81))


# --------------------------------------------------------------------------- #
# the branch precedence
# --------------------------------------------------------------------------- #
def gate(*, instrument=True, model=False, cosine=False, unit=False):
    return {
        "I0_instrument": {"pass": instrument},
        "cells": {
            "model": {"pass": model},
            "cosine": {"pass": cosine},
            "cosine_unit": {"pass": unit},
        },
    }


def test_the_four_branches(readrule81):
    assert readrule81.branch(gate(instrument=False, cosine=True))["id"] == "E0-instrument"
    assert readrule81.branch(gate(cosine=True))["id"] == "N1-norm-race-is-the-limit"
    assert readrule81.branch(gate(unit=True))["id"] == "N2-saturation-is-the-limit"
    assert readrule81.branch(gate())["id"] == "N3-keys-do-not-address"


def test_the_norm_branch_wins_when_both_rules_pass(readrule81):
    assert readrule81.branch(gate(cosine=True, unit=True))["id"] == "N1-norm-race-is-the-limit"


def test_the_instrument_precedes_every_cell(readrule81):
    failure = gate(instrument=False, cosine=True, unit=True)
    assert readrule81.branch(failure)["id"] == "E0-instrument"
    assert "nothing is read" in readrule81.branch(failure)["reading"]


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _cell(readrule81, *, m0, m1, items, ge, wins):
    return {
        "variant": "x",
        "n": len(items),
        "wins": wins,
        "forced": round(wins / len(items), 6),
        "wilson": {"low": 0.9, "high": 0.99} if wins == len(items) else {"low": 0.1, "high": 0.9},
        "p_value": round((1 + ge) / 401, 6),
        "null": {"draws": 400, "seed": readrule81.NULL_SEED, "ge": ge, "wins": {"mean": 1.0}},
        "m0": m0,
        "m1": m1,
        "items": items,
        "roster_mass": {"mean": 1.0},
        "argmax_hist": {"2": len(items)},
        "argmax_on_roster": 1.0,
    }


def report(readrule81, *, cosine_perfect=False):
    items = [0, 1, 0, 1]
    fixed = _cell(readrule81, m0=[0.0] * 4, m1=[1.0] * 4, items=items, ge=400, wins=2)
    perfect = _cell(
        readrule81,
        m0=[1.0, 0.0, 1.0, 0.0],
        m1=[0.0, 1.0, 0.0, 1.0],
        items=items,
        ge=0,
        wins=4,
    )
    data = {
        "stage": readrule81.STAGE,
        "corpus": {"train_sessions": 400, "heldout_sessions": 4},
        "reads": {"train": 400, "heldout": 4, "per_session": 1},
        "decision": {
            "alpha": readrule81.ALPHA,
            "forced_floor": readrule81.FORCED_FLOOR,
            "null_draws": readrule81.NULL_DRAWS,
            "null_seed": readrule81.NULL_SEED,
            "swap_move_floor": readrule81.SW_MOVE_FLOOR,
            "anchor_tolerance": readrule81.REF_TOLERANCE,
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "mode_matches": True,
            "corpus_digests_match": True,
            "read_audit": {"train": {"coverage": 1.0}, "heldout": {"coverage": 1.0}},
            "anchor": {
                "reproduced": True,
                "max_abs_diff": 0.0,
                "mismatches": 0,
                "wins": 2,
                "stored_wins": 2,
            },
        },
        "address": {
            "model": fixed,
            "cosine": perfect if cosine_perfect else fixed,
            "cosine_unit": fixed,
        },
        "swap": {
            variant: {
                "variant": variant,
                "pairs": 1,
                "tw": {"mean": 0.0},
                "roster_tw": {"mean": 0.0},
                "distances": [0.0],
                "moves": False,
            }
            for variant in readrule81.VARIANTS
        },
        "query": {
            variant: {"variant": variant, "n": 4, "wins": 2, "forced": 0.5, "p_value": 1.0}
            for variant in readrule81.VARIANTS
        },
    }
    data["gates"] = readrule81.gates(data)
    data["branch"] = readrule81.branch(data["gates"])
    return data


def _write(tmp_path, data):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(readrule81, tmp_path):
    data = report(readrule81)
    assert data["branch"]["id"] == "N3-keys-do-not-address"
    assert readrule81.check(_write(tmp_path, data)) == []


def test_a_passing_cosine_cell_re_derives_to_the_norm_branch(readrule81, tmp_path):
    data = report(readrule81, cosine_perfect=True)
    assert data["branch"]["id"] == "N1-norm-race-is-the-limit"
    assert readrule81.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_forced_rate(readrule81, tmp_path):
    data = report(readrule81)
    data["address"]["model"]["forced"] = 0.99
    problems = readrule81.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(readrule81, tmp_path):
    data = report(readrule81)
    data["address"]["cosine"]["p_value"] = 0.5
    problems = readrule81.check(_write(tmp_path, data))
    assert any("permutation convention" in problem for problem in problems)


def test_the_check_rejects_a_tampered_swap(readrule81, tmp_path):
    data = report(readrule81)
    data["swap"]["model"]["tw"]["mean"] = 0.5
    problems = readrule81.check(_write(tmp_path, data))
    assert any("mean of its pairs" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(readrule81, tmp_path):
    data = report(readrule81)
    data["branch"]["id"] = "N1-norm-race-is-the-limit"
    problems = readrule81.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_drifted_anchor(readrule81, tmp_path):
    data = report(readrule81)
    data["instrument"]["anchor"]["max_abs_diff"] = 1e-6
    problems = readrule81.check(_write(tmp_path, data))
    assert any("does not reproduce §80" in problem for problem in problems)


def test_the_check_rejects_a_wrong_read_count(readrule81, tmp_path):
    data = report(readrule81)
    data["reads"]["heldout"] = 3
    problems = readrule81.check(_write(tmp_path, data))
    assert any("held-out read count" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(readrule81, tmp_path):
    data = report(readrule81)
    data["instrument"]["read_audit"]["train"]["coverage"] = 0.5
    problems = readrule81.check(_write(tmp_path, data))
    assert any("I0_instrument does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(readrule81, tmp_path):
    data = report(readrule81)
    data["stage"] = "§80 something else"
    assert readrule81.check(_write(tmp_path, data)) == ["this is not a §81 report"]
