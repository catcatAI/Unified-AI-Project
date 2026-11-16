# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§79 contract tests: one entry's own value -> name pairing, read on held-out.

Nothing here loads a carrier. The tests pin the registered device (a per-entry
linear probe, a within-session two-way forced choice, the permutation null) and
the arithmetic that turns stored counts into a branch, so a tampered or stale
report is refused without a trained checkpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
PAIR79 = REPO_ROOT / "scripts" / "probe_pantry_pair79.py"
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
def pair79():
    return _load_module("pantry_pair79_under_test", PAIR79)


@pytest.fixture(scope="module")
def split75():
    return _load_module("pantry_pair79_split75_under_test", SPLIT75)


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_registered_constants(pair79):
    assert pair79.FEATURES == ("v", "k", "h")
    assert pair79.PRIMARY_FEATURE == "v"
    assert pair79.PROBE_STEPS == 2000
    assert pair79.NULL_DRAWS == 400
    assert pair79.NULL_SEED == 20261125
    assert pair79.PROBE_SEED == 20261121
    assert pair79.ALPHA == 0.005
    assert pair79.FORCED_FLOOR == 0.5
    assert pair79.ROSTER_ITEMS == 2
    assert pair79.ENTRY_COVERAGE == 0.99
    assert pair79.ENTRY_COSINE == 0.999


def test_the_branch_order_is_the_registered_one(pair79):
    assert pair79.BRANCH_ORDER == (
        "E0-instrument",
        "D1-entry-carries-owner",
        "D4-owner-only",
        "D2-key-only",
        "D3-entry-lacks-owner",
    )


def test_the_anchor_is_section_77s_stored_treatment_cells(pair79):
    if not SECTION_77.exists():
        pytest.skip("§77's report is not in this checkout")
    stored = json.loads(SECTION_77.read_text(encoding="utf-8"))
    cells = stored["arms"]["treatment"]["readings"]["linear_values"]
    for which in ("in_sample", "heldout", "leave_roster_out"):
        observed = cells[which]["observed"]
        assert pair79.REFERENCE[which]["exact"] == pytest.approx(observed["exact"])
        assert pair79.REFERENCE[which]["overlap"] == pytest.approx(observed["overlap"])


# --------------------------------------------------------------------------- #
# the forced choice
# --------------------------------------------------------------------------- #
def _logits():
    return torch.tensor(
        [
            [5.0, 0.0, 0.0, 1.0],  # own 0 > partner 1; partner 1 not in the top 2
            [2.0, 0.0, 5.0, 1.0],  # own 1 < partner 2 (wrong); top 2 = {2, 0}
            [0.0, 1.0, 5.0, 2.0],  # own 2 > partner 3
            [3.0, 0.0, 1.0, 5.0],  # own 3 > partner 0
        ]
    )


def test_forced_block_counts_own_and_partner(pair79, split75):
    own = torch.tensor([0, 1, 2, 3])
    partner = torch.tensor([1, 2, 3, 0])
    block = pair79.forced_block(torch, split75, _logits(), own, partner)
    assert block["n"] == 4
    assert block["forced_correct"] == 3
    assert block["forced"] == pytest.approx(0.75)
    assert block["top1_correct"] == 3
    assert block["own_top2"] == pytest.approx(0.75)
    assert block["partner_top2"] == pytest.approx(0.75)
    assert block["wilson"]["low"] < 0.75 < block["wilson"]["high"]


def test_the_forced_choice_is_a_strict_comparison(pair79, split75):
    logits = torch.tensor([[1.0, 1.0], [0.0, 2.0]])
    block = pair79.forced_block(torch, split75, logits, torch.tensor([0, 0]), torch.tensor([1, 1]))
    # row 0 ties -> not a win; row 1 prefers the partner -> not a win either
    assert block["forced_correct"] == 0
    assert block["forced"] == 0.0


def test_the_permutation_convention(pair79):
    assert pair79.permutation_p(0, 400) == 0.002494
    assert pair79.permutation_p(400, 400) == 1.0
    assert pair79.permutation_p(1, 400) == pytest.approx(2 / 401, abs=1e-6)


def test_the_readout_gate_needs_both_the_interval_and_the_null(pair79):
    assert pair79.readout_pass({"observed": {"wilson": {"low": 0.55}}, "p_value": 0.002494})
    assert not pair79.readout_pass({"observed": {"wilson": {"low": 0.49}}, "p_value": 0.002494})
    assert not pair79.readout_pass({"observed": {"wilson": {"low": 0.55}}, "p_value": 0.5})


# --------------------------------------------------------------------------- #
# the branch precedence
# --------------------------------------------------------------------------- #
def gate(pair79, *, instrument=True, name=False, colour=False):
    return {
        "I0_instrument": {"pass": instrument},
        "P_name": {"pass": name},
        "P_colour": {"pass": colour},
    }


def test_the_five_branches(pair79):
    assert pair79.branch(gate(pair79, instrument=False, name=True, colour=True))["id"] == (
        "E0-instrument"
    )
    assert pair79.branch(gate(pair79, name=True, colour=True))["id"] == ("D1-entry-carries-owner")
    assert pair79.branch(gate(pair79, name=True, colour=False))["id"] == "D4-owner-only"
    assert pair79.branch(gate(pair79, name=False, colour=True))["id"] == "D2-key-only"
    assert pair79.branch(gate(pair79, name=False, colour=False))["id"] == ("D3-entry-lacks-owner")


def test_the_instrument_precedes_every_readout(pair79):
    failure = gate(pair79, instrument=False, name=True, colour=True)
    assert pair79.branch(failure)["id"] == "E0-instrument"
    assert "nothing is read" in pair79.branch(failure)["reading"]


# --------------------------------------------------------------------------- #
# the entry audit
# --------------------------------------------------------------------------- #
def entry(session, slot, *, cos_v=1.0, cos_k=1.0, norm_v=1.0, gate=0.5):
    return {
        "session_id": session,
        "slot": slot,
        "cos_v": cos_v,
        "cos_k": cos_k,
        "norm_v": norm_v,
        "gate": gate,
    }


def test_the_audit_counts_a_landed_write(pair79):
    records = [entry("a", 1), entry("a", 2), entry("b", 1), entry("b", 2)]
    block = pair79.audit_block(records)
    assert block["entries"] == 4
    assert block["sessions"] == 2
    assert block["coverage"] == 1.0
    assert block["pass"] is True


def test_a_reused_slot_fails_the_audit(pair79):
    records = [entry("a", 1), entry("a", 1)]
    block = pair79.audit_block(records)
    assert block["coverage"] == 0.0
    assert block["pass"] is False
    assert block["failures"]


def test_a_weak_cosine_fails_the_audit(pair79):
    records = [entry("a", 1, cos_v=0.5), entry("a", 2)]
    block = pair79.audit_block(records)
    assert block["coverage"] == 0.0
    assert block["pass"] is False


# --------------------------------------------------------------------------- #
# the item <-> label alignment
# --------------------------------------------------------------------------- #
def roster_session(session_id, text, mapping):
    return {
        "session_id": session_id,
        "session_meta": {"roster_turn": 0},
        "turns": [
            {
                "user_input": text,
                "asserts": [{"kind": "roster", "value": mapping}],
            }
        ],
    }


def test_alignment_accepts_the_mapped_text(pair79):
    display = {"grey": "灰色", "orange": "橘色"}
    session = roster_session(
        "s1",
        "今天值班表上寫著：灰色是 Elena、橘色是 Ivan。",
        {"grey": "Elena", "orange": "Ivan"},
    )
    block = pair79.alignment(display, [session])
    assert block["pass"] is True
    assert block["bad"] == 0


def test_alignment_rejects_swapped_labels(pair79):
    display = {"grey": "灰色", "orange": "橘色"}
    session = roster_session(
        "s1",
        "今天值班表上寫著：灰色是 Elena、橘色是 Ivan。",
        {"grey": "Ivan", "orange": "Elena"},
    )
    block = pair79.alignment(display, [session])
    assert block["pass"] is False
    # both items now name the wrong person for their colour
    assert block["bad"] == 2


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _observed(n, correct, top1_correct):
    return {
        "n": n,
        "forced_correct": correct,
        "forced": round(correct / n, 6),
        "top1_correct": top1_correct,
        "top1": round(top1_correct / n, 6),
        "own_top2": 0.8,
        "partner_top2": 0.2,
        "wilson": {"low": 0.8, "high": 0.9},
    }


def _readout(n, correct, top1_correct):
    return {
        "observed": _observed(n, correct, top1_correct),
        "null": {
            "draws": 400,
            "seed": 20261125,
            "ge": 0,
            "forced": {"mean": 0.5},
            "top1": {"mean": 0.08},
        },
        "p_value": 0.002494,
        "chance": {"forced": 0.5, "top1": 0.08},
    }


def report(pair79, *, name_correct=340, colour_correct=250):
    readouts = {
        feature: {
            "name": _readout(400, name_correct, name_correct),
            "colour": _readout(400, colour_correct, colour_correct),
            "position": {"n": 400, "correct": 400, "top1": 1.0, "chance": 0.5},
        }
        for feature in pair79.FEATURES
    }
    data = {
        "stage": pair79.STAGE,
        "k": 2,
        "corpus_seed": 20261127,
        "corpus": {"train_sessions": 400, "heldout_sessions": 200},
        "entries": {"train": 800, "heldout": 400, "per_session": 2},
        "probe": {
            "features": list(pair79.FEATURES),
            "primary_feature": pair79.PRIMARY_FEATURE,
            "steps": pair79.PROBE_STEPS,
            "null_draws": pair79.NULL_DRAWS,
            "null_seed": pair79.NULL_SEED,
            "alpha": pair79.ALPHA,
            "forced_floor": pair79.FORCED_FLOOR,
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "mode_matches": True,
            "corpus_digests_match": True,
            "alignment": {"pass": True},
            "entry_audit": {
                "train": {"coverage": 1.0},
                "heldout": {"coverage": 1.0},
            },
            "bridge": {
                "reproduced": True,
                "actual": json.loads(json.dumps(pair79.REFERENCE)),
            },
        },
        "readouts": readouts,
    }
    data["gates"] = pair79.gates(data)
    data["branch"] = pair79.branch(data["gates"])
    return data


def _write(tmp_path, data):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(pair79, tmp_path):
    data = report(pair79)
    assert data["branch"]["id"] == "D1-entry-carries-owner"
    assert pair79.check(_write(tmp_path, data)) == []


def test_the_check_rejects_a_tampered_forced_rate(pair79, tmp_path):
    data = report(pair79)
    data["readouts"]["v"]["name"]["observed"]["forced"] = 0.99
    problems = pair79.check(_write(tmp_path, data))
    assert any("forced rate" in problem for problem in problems)


def test_the_check_rejects_a_tampered_p_value(pair79, tmp_path):
    data = report(pair79)
    data["readouts"]["v"]["name"]["p_value"] = 0.5
    problems = pair79.check(_write(tmp_path, data))
    assert any("permutation convention" in problem for problem in problems)


def test_the_check_rejects_a_tampered_branch(pair79, tmp_path):
    data = report(pair79)
    data["branch"]["id"] = "D2-key-only"
    problems = pair79.check(_write(tmp_path, data))
    assert any("branch does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_drifted_bridge(pair79, tmp_path):
    data = report(pair79)
    data["instrument"]["bridge"]["actual"]["heldout"]["exact"] = 0.56
    problems = pair79.check(_write(tmp_path, data))
    assert any("bridge does not reproduce" in problem for problem in problems)


def test_the_check_rejects_a_wrong_entry_count(pair79, tmp_path):
    data = report(pair79)
    data["entries"]["train"] = 799
    problems = pair79.check(_write(tmp_path, data))
    assert any("entry count" in problem for problem in problems)


def test_the_check_rejects_a_failed_instrument(pair79, tmp_path):
    data = report(pair79)
    data["instrument"]["entry_audit"]["train"]["coverage"] = 0.5
    problems = pair79.check(_write(tmp_path, data))
    assert any("I0_instrument does not re-derive" in problem for problem in problems)


def test_the_check_rejects_a_foreign_report(pair79, tmp_path):
    data = report(pair79)
    data["stage"] = "§78 something else"
    assert pair79.check(_write(tmp_path, data)) == ["this is not a §79 report"]
