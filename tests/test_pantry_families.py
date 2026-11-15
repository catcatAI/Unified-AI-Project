# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for §70's readout probe.

These pin the parts that must not drift silently: the capacity-free structure
test, the fixed floors, the branch precedence, and the fact that a stored verdict
re-derives from its own numbers. No carrier is loaded and nothing is trained.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "probe_pantry_families.py"


def _load():
    spec = importlib.util.spec_from_file_location("probe_pantry_families", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_families"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


# --------------------------------------------------------------------------- #
# the family and its transform
# --------------------------------------------------------------------------- #
def test_quad_doubles_the_width_and_squares(probe):
    features = torch.tensor([[1.0, -2.0], [0.5, 3.0]])
    out = probe.quad(features)
    assert out.shape == (2, 4)
    assert torch.equal(out[:, :2], features)
    assert torch.allclose(out[:, 2:], features * features)


def test_transform_only_touches_the_nonlinear_family(probe):
    features = torch.randn(5, 3)
    assert torch.equal(probe.transform("linear_state", features), features)
    assert torch.equal(probe.transform("linear_values", features), features)
    assert probe.transform("nonlinear_quad", features).shape == (5, 6)


def test_feature_view_reads_the_store_for_the_values_arm(probe):
    views = {"state": torch.zeros(2, 4), "values": torch.ones(2, 8)}
    assert torch.equal(probe.feature_view("linear_values", views), views["values"])
    assert torch.equal(probe.feature_view("linear_state", views), views["state"])
    assert torch.equal(probe.feature_view("nonlinear_quad", views), views["state"])


# --------------------------------------------------------------------------- #
# the AUC arithmetic
# --------------------------------------------------------------------------- #
def test_auc_from_ranks_is_one_when_every_same_pair_is_nearest():
    # Ranks are over similarity (-distance), so the 3 nearest pairs hold the top
    # three ranks of 12, and every different pair is farther away.
    ranksum = 10 + 11 + 12
    assert probe_auc(ranksum, 3, 9) == pytest.approx(1.0)


def test_auc_from_ranks_is_half_when_ranks_are_average():
    # Every same pair holds the middle rank of a tie-free ordering.
    same, diff = 3, 9
    ranksum = 5 + 6 + 7
    assert probe_auc(ranksum, same, diff) == pytest.approx(0.5, abs=0.12)


def probe_auc(ranksum, same, diff):
    return _load().auc_from_ranks(ranksum, same, diff)


def test_auc_from_ranks_refuses_a_degenerate_split():
    assert math.isnan(_load().auc_from_ranks(0.0, 0, 10))
    assert math.isnan(_load().auc_from_ranks(0.0, 10, 0))


# --------------------------------------------------------------------------- #
# the structure test
# --------------------------------------------------------------------------- #
def _two_cluster_features(seed: int = 7, per_cluster: int = 40) -> torch.Tensor:
    """Two tight cones around different directions: cosine makes this separable."""
    generator = torch.Generator().manual_seed(seed)
    first = torch.zeros(8)
    first[0] = 4.0
    second = torch.zeros(8)
    second[1] = 4.0
    left = torch.randn(per_cluster, 8, generator=generator) * 0.05 + first
    right = torch.randn(per_cluster, 8, generator=generator) * 0.05 + second
    return torch.cat([left, right], dim=0)


def test_structure_test_separates_two_rosters(probe):
    features = _two_cluster_features()
    rosters = [("a", "b")] * 40 + [("c", "d")] * 40
    block = probe.structure_test(torch, features, rosters, permutations=50, seed=11)
    assert block["auc"] == pytest.approx(1.0)
    assert block["p_value"] == pytest.approx(1.0 / 51.0, abs=1e-4)
    assert block["same_pairs"] == 2 * (40 * 39 // 2)
    assert block["distinct_rosters"] == 2


def test_structure_test_is_order_free(probe):
    sessions = [
        {"environment": {"actors": ["a", "b"]}},
        {"environment": {"actors": ["b", "a"]}},
        {"environment": {"actors": ["c", "d"]}},
    ]
    keys = probe.roster_keys(sessions)
    assert keys[0] == keys[1] == ("a", "b")
    assert keys[2] == ("c", "d")
    assert len(set(keys)) == 2


def test_structure_test_finds_nothing_in_a_shuffle(probe):
    """Rosters unrelated to the geometry must not clear the alpha floor."""
    generator = torch.Generator().manual_seed(3)
    features = torch.randn(80, 8, generator=generator)
    rosters = [(f"n{index % 4}",) for index in range(80)]
    block = probe.structure_test(torch, features, rosters, permutations=200, seed=5)
    assert 0.3 <= block["auc"] <= 0.7
    assert block["p_value"] > 0.001
    assert block["distinct_rosters"] == 4
    assert block["same_pairs"] > 0


def test_structure_gate_needs_both_the_effect_and_the_alpha(probe):
    heldout = {
        "auc": 0.70,
        "p_value": 0.002,
        "same_pairs": 10,
        "diff_pairs": 10,
        "distinct_rosters": 3,
    }
    assert probe.structure_gate({"auc": 0.7}, heldout)["transfers"] is False
    heldout["p_value"] = 0.001
    assert probe.structure_gate({"auc": 0.7}, heldout)["transfers"] is True
    heldout["auc"] = 0.6499
    assert probe.structure_gate({"auc": 0.7}, heldout)["transfers"] is False


# --------------------------------------------------------------------------- #
# the registered constants
# --------------------------------------------------------------------------- #
def test_registered_floors_are_pinned(probe):
    assert probe.READABLE_FLOOR == 0.95
    assert probe.TRANSFER_FLOOR == 0.50
    assert probe.CAPACITY_MAX == 0.50
    assert probe.STRUCTURE_AUC_FLOOR == 0.65
    assert probe.STRUCTURE_ALPHA == 0.001
    assert probe.STRUCTURE_PERMUTATIONS == 1000
    assert probe.FAMILIES == ("linear_state", "linear_values", "nonlinear_quad")


# --------------------------------------------------------------------------- #
# a synthetic report: gates, branch and the mechanical re-check
# --------------------------------------------------------------------------- #
def _scored(in_sample: float, capacity: float, in_dist: float, held: float, n: int = 200):
    return {
        "in_sample": {"n": 400, "correct": int(round(in_sample * 400)), "exact": in_sample},
        "heldout": {"n": n, "correct": int(round(held * n)), "exact": held},
        "capacity": {
            "n": 400,
            "correct": int(round(capacity * 400)),
            "exact": capacity,
            "labels_changed": 0.98,
            "permutation_is_bijection": True,
            "seed": 1,
        },
        "in_distribution": {"n": 400, "correct": int(round(in_dist * 400)), "exact": in_dist},
    }


def _structure_block(probe, separated: bool) -> dict:
    if separated:
        features = _two_cluster_features(seed=9, per_cluster=40)
        rosters = [("a", "b")] * 40 + [("c", "d")] * 40
    else:
        generator = torch.Generator().manual_seed(9)
        features = torch.randn(80, 8, generator=generator)
        rosters = [(f"n{index % 4}",) for index in range(80)]
    return probe.structure_test(torch, features, rosters, permutations=1000, seed=13)


def _report(
    probe,
    *,
    separated: bool = True,
    values_in: float = 0.4975,
    nonlinear_in: float = 0.9375,
    nonlinear_cap: float = 0.5650,
) -> dict:
    arms = {
        "linear_state": _scored(0.7700, 0.2500, 0.4725, 0.2850),
        "linear_values": _scored(values_in, 0.1650, 0.2625, 0.1400),
        "nonlinear_quad": _scored(nonlinear_in, nonlinear_cap, 0.2800, 0.3150),
    }
    controls = {
        name: {
            "in_sample": {"n": 400, "correct": 400, "exact": 1.0},
            "heldout": {"n": 400, "correct": 400, "exact": 1.0},
            "capacity": {
                "n": 400,
                "correct": 60,
                "exact": 0.15,
                "labels_changed": 0.99,
                "permutation_is_bijection": True,
                "seed": 1,
            },
        }
        for name in probe.FAMILIES
    }
    structure = {
        "train": _structure_block(probe, separated),
        "heldout": _structure_block(probe, separated),
    }
    return {
        "k": 2,
        "dimensions": {"colours": 8, "names": 12},
        "turns": {"roster": 1, "evidence": 2, "answer": 3},
        "arms": arms,
        "positive_controls": controls,
        "structure": structure,
        "majority_baselines": {
            "roster": {"prediction": [1, 1] + [0] * 10, "correct": 3, "n": 200, "exact": 0.015}
        },
        "reproduction": {
            "reference": "data/pantry_stage/slots69/k2.json",
            "expected": {
                "in_sample": 0.7700,
                "capacity": 0.2500,
                "in_distribution": 0.4725,
                "heldout": 0.2850,
            },
            "actual": {
                "in_sample": 0.7700,
                "capacity": 0.2500,
                "in_distribution": 0.4725,
                "heldout": 0.2850,
            },
            "equal": True,
        },
        "instrument": {"carrier_unchanged": True, "checkpoint_unchanged": True},
    }


def test_gates_read_the_registered_floors(probe):
    gate = probe.gates(_report(probe))
    assert gate["H0_instrument"]["pass"] is True
    assert gate["H1_linear_state_reproduces_§69"]["pass"] is True
    assert gate["H2_store_values_are_readable"]["readable"] is False
    assert gate["H3_nonlinear_is_admissible"]["readable"] is False
    assert gate["H3_nonlinear_is_admissible"]["capacity_limited"] is True
    assert gate["H5_store_values_transfer"]["transfers"] is False
    assert gate["H6_nonlinear_transfers"]["transfers"] is False


def test_branch_takes_the_first_matching_reading(probe):
    report = _report(probe)
    assert probe.branch(probe.gates(report))["id"] == "B3-roster-present-but-not-fittable"

    broken = _report(probe)
    broken["instrument"]["carrier_unchanged"] = False
    assert probe.branch(probe.gates(broken))["id"] == "B0-instrument"

    values_hold = _report(probe, values_in=0.97)
    values_hold["arms"]["linear_values"]["heldout"] = {"n": 200, "correct": 160, "exact": 0.80}
    assert probe.branch(probe.gates(values_hold))["id"] == "B1-store-values-hold-the-roster"

    nonlinear = _report(probe, nonlinear_in=0.99, nonlinear_cap=0.30)
    nonlinear["arms"]["nonlinear_quad"]["heldout"] = {"n": 200, "correct": 150, "exact": 0.75}
    assert probe.branch(probe.gates(nonlinear))["id"] == "B2-nonlinear-readout-holds-the-roster"

    absent = _report(probe, separated=False)
    assert probe.branch(probe.gates(absent))["id"] == "B4-roster-absent-at-its-own-turn"


def test_check_accepts_a_consistent_verdict(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert probe.check(path) == []


def test_check_rejects_a_stale_gate(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    report["arms"]["linear_values"]["in_sample"]["exact"] = 0.99  # now readable
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("H2_store_values_are_readable.readable is stale" in item for item in problems)


def test_check_rejects_a_tampered_instrument(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    report["instrument"]["checkpoint_unchanged"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("checkpoint bytes changed" in item for item in problems)


def test_check_rejects_an_invented_auc(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    report["structure"]["heldout"]["auc"] = 0.99
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("does not follow from its own rank sum" in item for item in problems)


def test_check_requires_H1_when_a_reference_was_recorded(probe, tmp_path):
    """§70/§72 pass --reference, so there H1 is part of the instrument."""
    report = _report(probe)
    report["reproduction"]["equal"] = False
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert probe.h1_is_applicable(report) is True
    problems = probe.check(path)
    assert any("H1_linear_state_reproduces_§69 did not pass" in item for item in problems)


def test_check_does_not_require_H1_when_no_reference_was_recorded(probe, tmp_path):
    """§73: a newly trained carrier cannot reproduce §69, so H1 is not applicable.

    The stored ``instrument_ok`` flag keeps reading ``False`` (it folds H1 in
    unconditionally); §73 reads W0's components, which is what this checks.
    """
    report = _report(probe)
    report["reproduction"] = {"reference": None, "expected": None, "actual": None, "equal": False}
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert probe.h1_is_applicable(report) is False
    assert probe.instrument_problems(report) == []
    assert probe.check(path) == []


def test_check_still_fails_a_broken_H0_without_a_reference(probe, tmp_path):
    """Dropping H1 must not drop the rest of the instrument."""
    report = _report(probe)
    report["reproduction"] = {"reference": None, "expected": None, "actual": None, "equal": False}
    report["positive_controls"]["linear_values"]["in_sample"]["exact"] = 0.60
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("H0_instrument did not pass" in item for item in problems)


def test_a_report_without_a_reference_cannot_claim_a_reproduction(probe):
    report = _report(probe)
    report["reproduction"] = {"reference": None, "expected": None, "actual": None, "equal": False}
    report["gates"] = probe.gates(report)
    report["instrument_ok"] = True
    assert any("never recorded" in item for item in probe.instrument_problems(report))


# --------------------------------------------------------------------------- #
# the boundary extractor refuses a state without the store
# --------------------------------------------------------------------------- #
class _FakeCore:
    def __init__(self):
        self._torch = torch

    def read_vector(self, tensors):
        return torch.zeros(tensors["h"].shape[0], 4)

    def eval(self):
        return self


class _FakeTrainer:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def _chunks(self, sessions, batch):
        yield sessions

    def run_session(self, core, turns, gaps, boundaries=None):
        boundaries.append(self._snapshot)


class _FakeProbe:
    @staticmethod
    def turn_payload(trainer, session):
        return [[0]], [1.0]


class _FakeSelection:
    load_probe = staticmethod(lambda: _FakeProbe)


class _FakeContents:
    load_selection = staticmethod(lambda: _FakeSelection)


def test_boundary_features_refuses_the_no_store_ablation(probe):
    core = _FakeCore()
    trainer = _FakeTrainer({"h": torch.zeros(2, 8)})
    with pytest.raises(SystemExit):
        probe.boundary_features(trainer, _FakeContents, core, [{}, {}], 0)


def test_boundary_features_flattens_the_store(probe):
    core = _FakeCore()
    snapshot = {"h": torch.zeros(2, 8), "k": torch.zeros(2, 3, 4), "v": torch.zeros(2, 3, 4)}
    trainer = _FakeTrainer(snapshot)
    views = probe.boundary_features(trainer, _FakeContents, core, [{}, {}], 0)
    assert views["state"].shape == (2, 12)
    assert views["values"].shape == (2, 12)
    assert views["value_shape"] == [3, 4]
