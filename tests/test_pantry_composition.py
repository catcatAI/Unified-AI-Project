# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for §74's relative-admissibility probe.

These pin the parts that must not drift silently: the permutation convention,
the registered constants (including that ``ALPHA`` is reachable at
``NULL_DRAWS``), the fixed branch precedence, and the fact that a stored verdict
re-derives from its own numbers. No carrier is loaded and nothing is trained.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "probe_pantry_composition.py"


def _load():
    spec = importlib.util.spec_from_file_location("probe_pantry_composition", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_composition"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def test_score_set_counts_exact_and_partial_overlap(probe):
    targets = torch.tensor([[1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 1.0]])
    # row 0: ranks units 0 and 1 -> both right; row 1: ranks 1 and 2 -> one right
    logits = torch.tensor([[3.0, 2.0, 1.0, 0.0], [9.0, 3.0, 2.0, 0.0]])
    block = probe.score_set(logits, targets, 2)
    assert block["n"] == 2
    assert block["correct"] == 1
    assert block["exact"] == 0.5
    assert block["overlap_sum"] == 3.0
    assert block["overlap"] == 1.5
    assert block["overlap_histogram"] == {"1": 1, "2": 1}


def test_score_set_histogram_always_sums_to_n(probe):
    torch.manual_seed(7)
    targets = torch.zeros(9, 6)
    for row in range(9):
        targets[row, torch.randperm(6)[:2]] = 1.0
    block = probe.score_set(torch.randn(9, 6), targets, 2)
    assert sum(block["overlap_histogram"].values()) == block["n"]


def test_chance_block_is_the_label_set_and_the_blind_overlap(probe):
    block = probe.chance_block(2, 12)
    assert block["exact"] == round(1 / 66, 6)
    assert block["overlap"] == round(2 * 2 / 12, 4)
    five = probe.chance_block(5, 12)
    assert five["exact"] == round(1 / 792, 6)
    assert five["overlap"] == round(5 * 5 / 12, 4)


# --------------------------------------------------------------------------- #
# the null machinery
# --------------------------------------------------------------------------- #
def test_permute_rows_is_seeded_and_a_bijection(probe):
    labels = torch.eye(6)
    first = probe.permute_rows(torch, labels, 11)
    again = probe.permute_rows(torch, labels, 11)
    other = probe.permute_rows(torch, labels, 12)
    assert torch.equal(first, again)
    assert not torch.equal(first, other)
    assert sorted(first.sum(dim=0).tolist()) == sorted(labels.sum(dim=0).tolist())
    assert float(first.sum()) == float(labels.sum())


def test_null_block_follows_the_permutation_convention(probe):
    draws = [
        {"exact": 0.02, "overlap": 0.3},
        {"exact": 0.10, "overlap": 0.5},
        {"exact": 0.30, "overlap": 0.7},
    ]
    block = probe.null_block({"exact": 0.20, "overlap": 0.4}, draws)
    assert block["ge"] == 1
    assert block["p_value"] == round((1 + 1) / (3 + 1), 6)
    assert block["exact"]["max"] == 0.30
    assert block["overlap"]["min"] == 0.3


def test_null_block_counts_a_tie_as_not_beaten(probe):
    draws = [{"exact": 0.50, "overlap": 1.0}]
    block = probe.null_block({"exact": 0.50, "overlap": 1.0}, draws)
    assert block["ge"] == 1
    assert block["p_value"] == round((1 + 1) / (1 + 1), 6)
    assert block["p_value"] == 1.0


def test_the_registered_alpha_is_reachable_at_the_registered_draw_count(probe):
    """A gate that cannot fire is the §73 W2 defect; this is the guard against it."""
    smallest = round(1 / (probe.NULL_DRAWS + 1), 6)
    assert smallest < probe.ALPHA


def test_composition_floor_is_three_quarters_of_k(probe):
    assert round(probe.COMPOSED_OVERLAP_FRACTION * 2, 4) == 1.5
    assert round(probe.COMPOSED_OVERLAP_FRACTION * 5, 4) == 3.75


# --------------------------------------------------------------------------- #
# gates and the branch table
# --------------------------------------------------------------------------- #
def _null(probe, ge=0):
    return {
        "draws": probe.NULL_DRAWS,
        "seed": probe.NULL_SEED,
        "exact": {"mean": 0.05, "sd": 0.01, "min": 0.0, "max": 0.09, "p95": 0.07, "p99": 0.08},
        "overlap": {"mean": 0.34, "sd": 0.02, "min": 0.2, "max": 0.5, "p95": 0.4, "p99": 0.45},
        "ge": ge,
        "p_value": round((1 + ge) / (probe.NULL_DRAWS + 1), 6),
    }


def _reading(probe, n, correct, overlap_sum, histogram, ge=0):
    return {
        "observed": {
            "n": n,
            "correct": correct,
            "exact": round(correct / n, 4),
            "overlap_sum": float(overlap_sum),
            "overlap": round(overlap_sum / n, 4),
            "overlap_histogram": histogram,
        },
        "null": _null(probe, ge),
    }


def _outcome(probe, *, composed_overlap=482, leaves_rosters=57):
    k = 2
    in_observed = _reading(probe, 400, 213, 500, {"0": 10, "1": 300, "2": 90})
    held = _reading(probe, 200, 67, 241, {"0": 20, "1": 120, "2": 60})
    lro = _reading(probe, 400, 94, composed_overlap, {"0": 60, "1": 240, "2": 100})
    lro.update(
        {
            "rosters": leaves_rosters,
            "fold_size": {"min": 2, "max": 14, "median": 6},
            "per_fold": [{"roster": ["a", "b"], "n": 6, "correct": 1, "overlap": 1.17}],
        }
    )
    readings = {}
    for name in probe.FAMILIES_ORDER:
        readings[name] = {
            "feature_dim": 1024,
            "in_sample": json.loads(json.dumps(in_observed)),
            "heldout": json.loads(json.dumps(held)),
            "leave_roster_out": json.loads(json.dumps(lro)),
        }
    outcome = {
        "stage": "§74 which reading does the roster cell support",
        "source_report": "report.json",
        "source_cell": "write73/k2.json",
        "checkpoint": "carrier.pt",
        "k": k,
        "dimensions": {"colours": 8, "names": 12},
        "corpus": {"train_items": 400, "heldout_items": 200, "train_rosters": 57},
        "probe": {
            "null_draws": probe.NULL_DRAWS,
            "null_seed": probe.NULL_SEED,
            "alpha": probe.ALPHA,
            "chance": probe.chance_block(k, 12),
            "composition_floor": {
                "overlap_fraction": probe.COMPOSED_OVERLAP_FRACTION,
                "overlap": round(probe.COMPOSED_OVERLAP_FRACTION * k, 4),
            },
        },
        "reproduction": {
            "expected": {"linear_values": {"in_sample": 0.5325, "heldout": 0.335}},
            "actual": {"linear_values": {"in_sample": 0.5325, "heldout": 0.335}},
            "equal": True,
        },
        "readings": readings,
        "instrument": {"carrier_unchanged": True, "checkpoint_unchanged": True, "seconds": 1.0},
    }
    outcome["gates"] = probe.gates(outcome)
    outcome["branch"] = probe.branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["N0_instrument"]["pass"])
    return outcome


def test_every_arm_passes_q1_and_q2_at_the_minimum_p(probe):
    gate = probe.gates(_outcome(probe))
    for name in probe.FAMILIES_ORDER:
        assert gate["Q1_relative_fit"]["arms"][name]["pass"] is True
        assert gate["Q2_transfer"]["arms"][name]["pass"] is True


def test_the_composition_gate_needs_the_overlap_floor_not_only_the_null(probe):
    below = probe.gates(_outcome(probe, composed_overlap=140))  # 0.35 mean overlap
    assert below["Q3_composed_from_names"]["any"] is False
    above = probe.gates(_outcome(probe, composed_overlap=700))  # 1.75 mean overlap
    assert above["Q3_composed_from_names"]["any"] is True


def test_branch_precedence_is_fixed(probe):
    outcome = _outcome(probe)
    assert probe.branch(outcome["gates"])["id"] == "Q2-transfer-below-the-composition-floor"

    broken = _outcome(probe)
    broken["instrument"]["carrier_unchanged"] = False
    assert probe.branch(probe.gates(broken))["id"] == "N0-instrument"

    unfitted = _outcome(probe)
    for name in probe.FAMILIES_ORDER:
        unfitted["readings"][name]["in_sample"]["null"]["ge"] = probe.NULL_DRAWS - 1
        unfitted["readings"][name]["in_sample"]["null"]["p_value"] = round(
            (1 + probe.NULL_DRAWS - 1) / (probe.NULL_DRAWS + 1), 6
        )
    assert probe.branch(probe.gates(unfitted))["id"] == "Q1-no-relative-fit"

    untransferred = _outcome(probe)
    for name in probe.FAMILIES_ORDER:
        untransferred["readings"][name]["heldout"]["null"]["ge"] = probe.NULL_DRAWS - 1
        untransferred["readings"][name]["heldout"]["null"]["p_value"] = round(
            (1 + probe.NULL_DRAWS - 1) / (probe.NULL_DRAWS + 1), 6
        )
    assert probe.branch(probe.gates(untransferred))["id"] == "Q2-fit-but-no-transfer"

    composed = _outcome(probe, composed_overlap=700)
    assert probe.branch(probe.gates(composed))["id"] == "Q3-composed-from-names"


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def test_check_accepts_a_self_consistent_report(probe, tmp_path):
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(_outcome(probe)), encoding="utf-8")
    assert probe.check(path) == []


def test_check_rejects_a_stale_branch(probe, tmp_path):
    outcome = _outcome(probe)
    outcome["readings"]["linear_values"]["leave_roster_out"]["observed"]["overlap"] = 1.75
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("stale" in item for item in probe.check(path))


def test_check_rejects_a_p_value_that_does_not_follow_from_its_draws(probe, tmp_path):
    outcome = _outcome(probe)
    outcome["readings"]["linear_state"]["heldout"]["null"]["p_value"] = 0.0001
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("p_value does not follow" in item for item in probe.check(path))


def test_check_rejects_a_gate_that_does_not_follow_from_the_readings(probe, tmp_path):
    outcome = _outcome(probe)
    outcome["gates"]["Q2_transfer"]["any"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("stored gates do not follow" in item for item in probe.check(path))


def test_check_rejects_a_report_that_does_not_reproduce_the_source_cell(probe, tmp_path):
    outcome = _outcome(probe)
    outcome["reproduction"]["equal"] = False
    outcome["gates"] = probe.gates(outcome)
    outcome["branch"] = probe.branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["N0_instrument"]["pass"])
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    problems = probe.check(path)
    assert any("do not reproduce" in item for item in problems)


def test_check_rejects_a_report_from_another_stage(probe, tmp_path):
    outcome = _outcome(probe)
    outcome["stage"] = "§70 which readout family reaches the roster"
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert probe.check(path) == ["this is not a §74 report"]
