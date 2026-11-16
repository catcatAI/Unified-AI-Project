# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§80 contract tests: the model's own read at the question turn.

Nothing here loads a carrier. The tests pin the registered device (a two-way
forced choice of the model's own attention, the held-out label-permutation null,
the train-only twin swap control) and the arithmetic that turns stored readings
into a branch, so a tampered or stale report is refused without a checkpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDRESS80 = REPO_ROOT / "scripts" / "probe_pantry_address80.py"
COMPOSITION = REPO_ROOT / "scripts" / "probe_pantry_composition.py"
SPLIT75 = REPO_ROOT / "scripts" / "probe_pantry_split75.py"
SECTION_77 = REPO_ROOT / "data" / "pantry_stage" / "item77" / "k2.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def address80():
    return _load_module("pantry_address80_under_test", ADDRESS80)


@pytest.fixture(scope="module")
def composition():
    return _load_module("pantry_address80_composition_under_test", COMPOSITION)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_address80_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(address80):
    assert address80.PROBE_STEPS == 2000
    assert address80.PROBE_BATCH == 64
    assert address80.PROBE_LR == 1e-3
    assert address80.PROBE_WEIGHT_DECAY == 1e-4
    assert address80.PROBE_SEED == 20261121
    assert address80.NULL_DRAWS == 400
    assert address80.NULL_SEED == 20261125
    assert address80.ALPHA == 0.005
    assert address80.FORCED_FLOOR == 0.5
    assert address80.SW_SLOT_FLOOR == 0.01
    assert address80.ROSTER_ITEMS == 2
    assert address80.ENTRY_COVERAGE == 0.99
    assert address80.ENTRY_COSINE == 0.999
    assert address80.BRIDGE_TOLERANCE == 1e-9


def test_the_branch_order_is_the_registered_one(address80):
    assert address80.BRANCH_ORDER == (
        "E0-instrument",
        "H3-read-addresses",
        "H1-read-ignores-query",
        "H2-read-uses-query-but-wrong",
    )


def test_the_anchor_is_section_77s_stored_treatment_cells(address80):
    if not SECTION_77.exists():
        pytest.skip("§77's report is not in this checkout")
    stored = json.loads(SECTION_77.read_text(encoding="utf-8"))
    cells = stored["arms"]["treatment"]["readings"]["linear_values"]
    for which in ("in_sample", "heldout", "leave_roster_out"):
        observed = cells[which]["observed"]
        assert observed["exact"] == pytest.approx(address80.REFERENCE[which]["exact"])
        assert observed["overlap"] == pytest.approx(address80.REFERENCE[which]["overlap"])


# --------------------------------------------------------------------------- #
# the read: slots come from the item plan, not from a constant
# --------------------------------------------------------------------------- #
class _FakeTrainer:
    def __init__(self, counts, slots=16):
        self._counts = counts
        self.slots = slots

    def item_end_positions(self, tokens):
        return list(range(self._counts[len(tokens)]))


def test_roster_slots_follow_the_items_written_before(address80):
    trainer = _FakeTrainer({1: 1, 2: 2, 3: 1})
    turns = [[1], [1, 2], [1]]
    assert address80.roster_slots(trainer, turns, roster=1, slots=16) == [1, 2]


def test_roster_slots_refuse_a_wraparound(address80):
    trainer = _FakeTrainer({1: 1, 2: 2, 3: 1})
    with pytest.raises(SystemExit):
        address80.roster_slots(trainer, [[1], [1, 2], [1]], roster=1, slots=2)


# --------------------------------------------------------------------------- #
# the scored cell: two-way forced choice of attention mass
# --------------------------------------------------------------------------- #
def record(item, weights, *, slots=(1, 2), structure="s", twin=False):
    weights = torch.as_tensor(weights, dtype=torch.float32)
    return {
        "session_id": structure,
        "structure": structure,
        "twin": twin,
        "item": item,
        "slots": list(slots),
        "weights": weights,
        "roster_mass": round(float(weights[list(slots)].sum()), 6),
        "argmax": int(weights.argmax()),
        "key_norms": [1.0, 2.0],
    }


def _fixed_slot_records():
    weights = [0.0] * 16
    weights[2] = 1.0
    return [record(item, weights) for item in (0, 1, 0, 1)]


def test_a_fixed_slot_read_scores_exactly_chance(address80, composition, split75):
    block = address80.address_block(torch, split75, composition, _fixed_slot_records())
    assert block["n"] == 4
    assert block["wins"] == 2
    assert block["forced"] == 0.5
    assert block["roster_mass"]["mean"] == 1.0
    assert block["argmax_hist"] == {"2": 4}
    # every permutation of a balanced label vector keeps two wins
    assert block["null"]["ge"] == 400
    assert block["p_value"] == pytest.approx(1.0)


def test_a_read_that_picks_the_needed_entry_wins(address80, composition, split75):
    records = []
    for item in (0, 1) * 20:
        weights = [0.0] * 16
        weights[[1, 2][item]] = 1.0
        records.append(record(item, weights))
    block = address80.address_block(torch, split75, composition, records)
    assert block["wins"] == 40
    assert block["forced"] == 1.0
    assert block["null"]["ge"] == 0
    assert block["p_value"] == round(1 / 401, 6)


def test_the_forced_choice_is_a_strict_comparison(address80, composition, split75):
    weights = [0.0] * 16
    weights[1] = 0.5
    weights[2] = 0.5
    block = address80.address_block(
        torch, split75, composition, [record(0, weights), record(1, weights)]
    )
    assert block["wins"] == 0


# --------------------------------------------------------------------------- #
# the mechanism control: twin swap
# --------------------------------------------------------------------------- #
def test_swap_is_zero_when_the_read_is_a_fixed_slot(address80):
    weights = [0.0] * 16
    weights[2] = 1.0
    block = address80.swap_block(
        torch, [record(0, weights, structure="a"), record(1, weights, structure="a")]
    )
    assert block["pairs"] == 1
    assert block["tw"]["mean"] == 0.0
    assert block["slot_fixed"] is True


def test_swap_is_one_when_the_read_follows_the_needed_entry(address80):
    first = [0.0] * 16
    first[1] = 1.0
    second = [0.0] * 16
    second[2] = 1.0
    block = address80.swap_block(
        torch,
        [record(0, first, structure="a"), record(1, second, structure="a")],
    )
    assert block["tw"]["mean"] == 1.0
    assert block["slot_fixed"] is False


def test_swap_refuses_twins_that_do_not_flip_the_needed_entry(address80):
    weights = [0.0] * 16
    weights[2] = 1.0
    block = address80.swap_block(
        torch, [record(0, weights, structure="a"), record(0, weights, structure="a")]
    )
    assert block["pairs"] == 0
    assert block["slot_fixed"] is False
    assert block["failures"]


# --------------------------------------------------------------------------- #
# the read-boundary audit
# --------------------------------------------------------------------------- #
def _read_record(session, values, slots=(1, 2)):
    return {
        "session_id": session,
        "slots": list(slots),
        "v_roster": torch.stack([torch.as_tensor(value, dtype=torch.float32) for value in values]),
    }


def _entry(session, slot, value):
    return {"session_id": session, "slot": slot, "v": torch.as_tensor(value, dtype=torch.float32)}


def test_the_read_audit_accepts_the_same_entries(address80):
    records = [_read_record("a", [[1.0, 0.0], [0.0, 1.0]])]
    entries = [_entry("a", 1, [1.0, 0.0]), _entry("a", 2, [0.0, 1.0])]
    block = address80.read_audit(torch, records, entries)
    assert block["coverage"] == 1.0
    assert block["pass"] is True
    assert block["cosine"]["min"] == pytest.approx(1.0)


def test_the_read_audit_rejects_an_overwritten_slot(address80):
    records = [_read_record("a", [[1.0, 0.0], [0.0, 1.0]])]
    entries = [_entry("a", 1, [1.0, 0.0]), _entry("a", 2, [1.0, 0.0])]
    block = address80.read_audit(torch, records, entries)
    assert block["coverage"] == 0.0
    assert block["pass"] is False


# --------------------------------------------------------------------------- #
# the branch precedence
# --------------------------------------------------------------------------- #
def gate(*, instrument=True, address=False, swap=True):
    return {
        "I0_instrument": {"pass": instrument},
        "A_address": {"pass": address},
        "S_swap": {"pass": swap},
    }


def test_the_four_branches(address80):
    assert address80.branch(gate(instrument=False, address=True))["id"] == "E0-instrument"
    assert address80.branch(gate(address=True))["id"] == "H3-read-addresses"
    assert address80.branch(gate(address=False, swap=True))["id"] == "H1-read-ignores-query"
    assert address80.branch(gate(address=False, swap=False))["id"] == (
        "H2-read-uses-query-but-wrong"
    )


def test_the_instrument_precedes_every_readout(address80):
    failure = gate(instrument=False, address=True, swap=True)
    assert address80.branch(failure)["id"] == "E0-instrument"
    assert "nothing is read" in address80.branch(failure)["reading"]


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def report(address80):
    address = {
        "n": 4,
        "wins": 2,
        "forced": 0.5,
        "wilson": {"low": 0.1500, "high": 0.8500},
        "p_value": 1.0,
        "null": {"draws": 400, "seed": 20261125, "ge": 400},
        "m0": [0.0, 0.0, 0.0, 0.0],
        "m1": [1.0, 1.0, 1.0, 1.0],
        "items": [0, 1, 0, 1],
        "roster_mass": {"mean": 1.0},
        "argmax_hist": {"2": 4},
        "key_norms": {"slot_first": {"median": 2.6}, "slot_second": {"median": 9.8}},
    }
    data = {
        "stage": address80.STAGE,
        "corpus": {"train_sessions": 400, "heldout_sessions": 200},
        "reads": {"train": 400, "heldout": 200, "per_session": 1},
        "probe": {
            "steps": address80.PROBE_STEPS,
            "seed": address80.PROBE_SEED,
            "null_draws": address80.NULL_DRAWS,
            "null_seed": address80.NULL_SEED,
            "alpha": address80.ALPHA,
            "forced_floor": address80.FORCED_FLOOR,
            "swap_floor": address80.SW_SLOT_FLOOR,
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "mode_matches": True,
            "corpus_digests_match": True,
            "alignment": {"pass": True},
            "read_audit": {
                "train": {"coverage": 1.0},
                "heldout": {"coverage": 1.0},
            },
            "bridge": {
                "reproduced": True,
                "actual": json.loads(json.dumps(address80.REFERENCE)),
            },
        },
        "address": address,
        "swap": {
            "pairs": 1,
            "tw": {"mean": 0.0},
            "roster_tw": {"mean": 0.0},
            "distances": [0.0],
            "slot_fixed": True,
            "floor": address80.SW_SLOT_FLOOR,
        },
    }
    data["gates"] = address80.gates(data)
    data["branch"] = address80.branch(data["gates"])
    return data


def _write(tmp_path, data):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(address80, tmp_path):
    data = report(address80)
    assert data["branch"]["id"] == "H1-read-ignores-query"
    assert address80.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_forced_rate(address80, tmp_path):
    data = report(address80)
    data["address"]["forced"] = 0.99
    problems = address80.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(address80, tmp_path):
    data = report(address80)
    data["address"]["p_value"] = 0.5
    problems = address80.check(_write(tmp_path, data))
    assert any("permutation convention" in problem for problem in problems)


def test_the_check_rejects_a_tampered_swap(address80, tmp_path):
    data = report(address80)
    data["swap"]["tw"]["mean"] = 0.5
    problems = address80.check(_write(tmp_path, data))
    assert any("mean of its pairs" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(address80, tmp_path):
    data = report(address80)
    data["branch"]["id"] = "H3-read-addresses"
    problems = address80.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_drifted_bridge(address80, tmp_path):
    data = report(address80)
    data["instrument"]["bridge"]["actual"]["heldout"]["exact"] = 0.56
    problems = address80.check(_write(tmp_path, data))
    assert any("bridge does not reproduce" in problem for problem in problems)


def test_the_check_rejects_a_wrong_read_count(address80, tmp_path):
    data = report(address80)
    data["reads"]["train"] = 399
    problems = address80.check(_write(tmp_path, data))
    assert any("training read count" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(address80, tmp_path):
    data = report(address80)
    data["instrument"]["read_audit"]["train"]["coverage"] = 0.5
    problems = address80.check(_write(tmp_path, data))
    assert any("I0_instrument does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(address80, tmp_path):
    data = report(address80)
    data["stage"] = "§79 something else"
    assert address80.check(_write(tmp_path, data)) == ["this is not a §80 report"]
