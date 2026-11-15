# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for §75's seen/unseen split and fresh-seed replication.

These pin the parts that must not drift silently: that the split is a partition,
that a cell's null permutes **only that cell's** labels, that the constants are
the §74 constants, that both branch tables have the registered precedence, and
that a stored verdict re-derives from its own numbers. No carrier is loaded and
nothing is trained.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "probe_pantry_split75.py"


def _load():
    spec = importlib.util.spec_from_file_location("probe_pantry_split75", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_split75"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


@pytest.fixture(scope="module")
def composition(probe):
    return probe.load_composition()


# --------------------------------------------------------------------------- #
# the split
# --------------------------------------------------------------------------- #
def test_split_rows_is_a_partition(probe):
    train = [("Alex", "Hana"), ("Alex", "Hana"), ("Ivan", "Lena")]
    held = [
        ("Alex", "Hana"),
        ("Ivan", "Lena"),
        ("Grace", "Judy"),
        ("Grace", "Judy"),
        ("Alex", "Elena"),
    ]
    split = probe.split_rows(held, train)
    assert split["rows"] == 5
    assert split["seen"] == 2
    assert split["unseen"] == 3
    assert sorted(split["seen_rows"] + split["unseen_rows"]) == list(range(5))
    assert split["train_rosters"] == 2
    assert split["unseen_rosters"] == 2
    assert split["unseen_roster_sizes"] == {"Alex+Elena": 1, "Grace+Judy": 2}


def test_split_rows_counts_a_roster_once_per_key_not_per_row(probe):
    train = [("Alex", "Hana")]
    held = [("Hana", "Alex")]  # same pair, different order: a different key
    split = probe.split_rows(held, train)
    assert split["seen"] == 0
    assert split["unseen"] == 1


# --------------------------------------------------------------------------- #
# the cell reading
# --------------------------------------------------------------------------- #
def test_subset_reading_scores_only_that_cells_rows(probe, composition):
    torch.manual_seed(3)
    labels = torch.zeros(9, 6)
    for row in range(9):
        labels[row, torch.randperm(6)[:2]] = 1.0
    # make rows 6..8 exactly right: rank their own two names highest
    logits = torch.zeros(9, 6)
    for row in range(6, 9):
        logits[row, labels[row].bool()] = 5.0
    block = probe.subset_reading(composition, torch, logits, labels, [6, 7, 8], slots=2, draws=25)
    assert block["observed"]["n"] == 3
    assert block["observed"]["exact"] == 1.0
    assert block["chance"]["exact"] == round(1 / 15, 6)
    assert block["null"]["draws"] == 25


def test_subset_reading_refuses_an_empty_cell(probe, composition):
    labels = torch.eye(4)
    with pytest.raises(SystemExit):
        probe.subset_reading(composition, torch, labels, labels, [], slots=2, draws=5)


def test_wilson_interval_contains_the_point_estimate(probe):
    interval = probe.wilson(6, 24)
    assert 0.0 <= interval["low"] < 6 / 24 < interval["high"] <= 1.0
    assert probe.wilson(0, 0) == {"low": 0.0, "high": 0.0}
    assert probe.wilson(24, 24)["high"] == 1.0


# --------------------------------------------------------------------------- #
# registered constants
# --------------------------------------------------------------------------- #
def test_the_registered_alpha_is_reachable(probe):
    assert round(1 / (probe.NULL_DRAWS + 1), 6) < probe.ALPHA


def test_the_constants_are_the_s74_constants(probe, composition):
    assert probe.NULL_DRAWS == composition.NULL_DRAWS
    assert probe.NULL_SEED == composition.NULL_SEED
    assert probe.ALPHA == composition.ALPHA
    assert probe.COMPOSED_OVERLAP_FRACTION == composition.COMPOSED_OVERLAP_FRACTION
    assert round(probe.COMPOSED_OVERLAP_FRACTION * 2, 4) == 1.5


def test_load_composition_fails_loudly_if_a_constant_moves(probe, monkeypatch):
    monkeypatch.setattr(probe, "ALPHA", 0.05)
    with pytest.raises(SystemExit):
        probe.load_composition()


# --------------------------------------------------------------------------- #
# the branch tables
# --------------------------------------------------------------------------- #
def _seen_outcome(probe, *, seen_pass=True, unseen_pass=True, instrument_ok=True, reproduced=True):
    def cell(n, correct, ge):
        observed = {
            "n": n,
            "correct": correct,
            "exact": round(correct / n, 4),
            "overlap_sum": float(correct) * 2,
            "overlap": round(float(correct) * 2 / n, 4),
            "overlap_histogram": {"2": correct, "1": n - correct},
            "wilson": probe.wilson(correct, n),
        }
        null = {
            "draws": probe.NULL_DRAWS,
            "seed": probe.NULL_SEED,
            "exact": {"mean": 0.02, "sd": 0.01, "min": 0.0, "max": 0.04, "p95": 0.03, "p99": 0.04},
            "overlap": {"mean": 0.34, "sd": 0.03, "min": 0.2, "max": 0.5, "p95": 0.4, "p99": 0.45},
            "ge": ge,
            "p_value": round((1 + ge) / (probe.NULL_DRAWS + 1), 6),
        }
        return {
            "observed": observed,
            "null": null,
            "chance": {"exact": 0.015152, "overlap": 0.3333},
        }

    seen_ge = 0 if seen_pass else probe.NULL_DRAWS - 1
    unseen_ge = 0 if unseen_pass else probe.NULL_DRAWS - 1
    readings = {}
    for name in probe.SPLIT_FAMILIES:
        readings[name] = {
            "feature_dim": 1024,
            "pooled": {
                "n": 200,
                "correct": 93,
                "exact": 0.465,
                "overlap_sum": 290.0,
                "overlap": 1.45,
                "overlap_histogram": {"1": 104, "2": 93, "0": 3},
                "wilson": probe.wilson(93, 200),
            },
            "seen": cell(176, 81, seen_ge),
            "unseen": cell(24, 12, unseen_ge),
        }
    outcome = {
        "stage": probe.STAGE_SEEN,
        "source_report": "report.json",
        "reference": "compose74/k2.json",
        "reference_report": "report.json",
        "checkpoint": "carrier.pt",
        "k": 2,
        "dimensions": {"colours": 8, "names": 12},
        "corpus": {
            "train_items": 400,
            "heldout_items": 200,
            "train_digest": "a",
            "heldout_digest": "b",
        },
        "split": {
            "rows": 200,
            "seen": 176,
            "unseen": 24,
            "train_rosters": 57,
            "unseen_rosters": 9,
            "unseen_roster_sizes": {"Grace+Judy": 1},
        },
        "probe": {
            "null_draws": probe.NULL_DRAWS,
            "null_seed": probe.NULL_SEED,
            "alpha": probe.ALPHA,
            "chance": {"exact": 0.015152, "overlap": 0.3333},
        },
        "reproduction": {
            "expected": {"linear_state": 0.465, "linear_values": 0.335},
            "actual": {"linear_state": 0.465, "linear_values": 0.335},
            "equal": reproduced,
        },
        "readings": readings,
        "instrument": {
            "carrier_unchanged": instrument_ok,
            "checkpoint_unchanged": instrument_ok,
            "seconds": 1.0,
        },
    }
    outcome["gates"] = probe.seen_gates(outcome)
    outcome["branch"] = probe.seen_branch(outcome["gates"])
    outcome["instrument_ok"] = bool(outcome["gates"]["N0a_instrument"]["pass"])
    return outcome


def test_seen_branch_precedence_is_fixed(probe):
    assert (
        probe.seen_branch(probe.seen_gates(_seen_outcome(probe)))["id"]
        == "U1-unseen-rosters-answer"
    )

    seen_only = _seen_outcome(probe, unseen_pass=False)
    assert probe.seen_branch(probe.seen_gates(seen_only))["id"] == "U2-seen-rosters-only"

    neither = _seen_outcome(probe, seen_pass=False, unseen_pass=False)
    assert probe.seen_branch(probe.seen_gates(neither))["id"] == "U3-neither-cell-above-null"

    broken = _seen_outcome(probe, instrument_ok=False)
    assert probe.seen_branch(probe.seen_gates(broken))["id"] == "N0-instrument"

    stale = _seen_outcome(probe, reproduced=False)
    assert probe.seen_branch(probe.seen_gates(stale))["id"] == "N0-instrument"


def _fresh_outcome(
    probe,
    composition,
    *,
    in_ge=0,
    held_ge=0,
    lro_ge=0,
    lro_correct=94,
    instrument_ok=True,
    digests=True,
):
    def reading(n, correct, ge, overlap_sum):
        observed = {
            "n": n,
            "correct": correct,
            "exact": round(correct / n, 4),
            "overlap_sum": float(overlap_sum),
            "overlap": round(overlap_sum / n, 4),
            "overlap_histogram": {"2": correct, "1": n - correct},
        }
        null = {
            "draws": probe.NULL_DRAWS,
            "seed": probe.NULL_SEED,
            "exact": {"mean": 0.02, "sd": 0.01, "min": 0.0, "max": 0.05, "p95": 0.03, "p99": 0.05},
            "overlap": {"mean": 0.34, "sd": 0.03, "min": 0.2, "max": 0.5, "p95": 0.4, "p99": 0.45},
            "ge": ge,
            "p_value": round((1 + ge) / (probe.NULL_DRAWS + 1), 6),
        }
        observed["wilson"] = probe.wilson(correct, n)
        return {"observed": observed, "null": null}

    readings = {}
    for name in composition.FAMILIES_ORDER:
        readings[name] = {
            "feature_dim": 1024,
            "in_sample": reading(400, 213, in_ge, 500),
            "heldout": reading(200, 67, held_ge, 258),
            "leave_roster_out": dict(
                reading(400, lro_correct, lro_ge, lro_correct * 2 + 300),
                rosters=57,
                fold_size={"min": 2, "max": 14, "median": 6},
                per_fold=[],
            ),
        }
    outcome = {
        "stage": probe.STAGE_FRESH,
        "source_report": "fresh.json",
        "checkpoint": "fresh.pt",
        "k": 2,
        "dimensions": {"colours": 8, "names": 12},
        "corpus_seed": 20261126,
        "corpus": {
            "train_digest": "c" if digests else None,
            "heldout_digest": "d" if digests else None,
            "train_items": 400,
            "heldout_items": 200,
            "train_rosters": 57,
        },
        "probe": {
            "null_draws": probe.NULL_DRAWS,
            "null_seed": probe.NULL_SEED,
            "alpha": probe.ALPHA,
            "chance": composition.chance_block(2, 12),
            "composition_floor": {
                "overlap_fraction": probe.COMPOSED_OVERLAP_FRACTION,
                "overlap": round(probe.COMPOSED_OVERLAP_FRACTION * 2, 4),
            },
        },
        "reproduction": {"applicable": False, "equal": False, "reason": "fresh corpus"},
        "readings": readings,
        "instrument": {
            "carrier_unchanged": instrument_ok,
            "checkpoint_unchanged": instrument_ok,
            "seconds": 1.0,
        },
    }
    outcome["gates"] = probe.fresh_gates(composition, outcome)
    outcome["branch"] = probe.fresh_branch(outcome["gates"], composition, outcome)
    outcome["instrument_ok"] = bool(outcome["gates"]["N0_instrument"]["pass"])
    return outcome


def test_fresh_branch_precedence_is_fixed(probe, composition):
    outcome = _fresh_outcome(probe, composition)
    assert outcome["branch"]["id"] == "Q3-below-floor-again"

    composed = _fresh_outcome(probe, composition, lro_correct=380)  # overlap 2.65 >= 1.5
    assert probe.fresh_branch(probe.fresh_gates(composition, composed), composition, composed)[
        "id"
    ] == ("Q3-composed-from-names-on-second-seed")

    flat = _fresh_outcome(probe, composition, lro_ge=probe.NULL_DRAWS - 1)
    assert probe.fresh_branch(probe.fresh_gates(composition, flat), composition, flat)["id"] == (
        "Q3-flat-on-second-seed"
    )

    unfitted = _fresh_outcome(probe, composition, in_ge=probe.NULL_DRAWS - 1)
    assert probe.fresh_branch(probe.fresh_gates(composition, unfitted), composition, unfitted)[
        "id"
    ] == ("Q1-no-relative-fit")

    untransferred = _fresh_outcome(probe, composition, held_ge=probe.NULL_DRAWS - 1)
    assert (
        probe.fresh_branch(
            probe.fresh_gates(composition, untransferred), composition, untransferred
        )["id"]
        == "Q2-fit-but-no-transfer"
    )

    broken = _fresh_outcome(probe, composition, instrument_ok=False)
    assert probe.fresh_branch(probe.fresh_gates(composition, broken), composition, broken)[
        "id"
    ] == ("N0-instrument")

    undigested = _fresh_outcome(probe, composition, digests=False)
    assert (
        probe.fresh_branch(probe.fresh_gates(composition, undigested), composition, undigested)[
            "id"
        ]
        == "N0-instrument"
    )


def test_the_fresh_gate_never_claims_s73_reproduction(probe, composition):
    outcome = _fresh_outcome(probe, composition)
    n0 = outcome["gates"]["N0_instrument"]
    assert n0["reproduction_applicable"] is False
    assert outcome["reproduction"]["equal"] is False


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def test_check_accepts_a_self_consistent_seen_report(probe, tmp_path):
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(_seen_outcome(probe)), encoding="utf-8")
    assert probe.check(path) == []


def test_check_accepts_a_self_consistent_fresh_report(probe, composition, tmp_path):
    path = tmp_path / "fresh.json"
    path.write_text(json.dumps(_fresh_outcome(probe, composition)), encoding="utf-8")
    assert probe.check(path) == []


def test_check_rejects_a_stale_seen_branch(probe, tmp_path):
    outcome = _seen_outcome(probe)
    outcome["split"]["unseen"] = 0
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("empty" in item or "add up" in item for item in probe.check(path))


def test_check_rejects_a_wilson_interval_that_does_not_follow(probe, tmp_path):
    outcome = _seen_outcome(probe)
    outcome["readings"]["linear_state"]["unseen"]["observed"]["wilson"] = {"low": 0.0, "high": 1.0}
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("wilson" in item for item in probe.check(path))


def test_check_rejects_a_p_value_that_does_not_follow(probe, tmp_path):
    outcome = _seen_outcome(probe)
    outcome["readings"]["linear_values"]["seen"]["null"]["p_value"] = 0.0001
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("p_value does not follow" in item for item in probe.check(path))


def test_check_rejects_a_seen_report_that_does_not_reproduce_s74(probe, tmp_path):
    outcome = _seen_outcome(probe, reproduced=False)
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert any("reproduce" in item for item in probe.check(path))


def test_check_rejects_a_report_from_another_stage(probe, tmp_path):
    outcome = _seen_outcome(probe)
    outcome["stage"] = "§74 which reading does the roster cell support"
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    assert probe.check(path) == ["this is not a §75 report"]
