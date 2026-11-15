# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§67 contracts: the selection head's arithmetic, its arms and its mechanical fork.

No trained checkpoint is read here: the integration cases rebuild a small
untrained ``TurnStoreCore`` and read a handful of corpus sessions, which is
enough to pin the feature shapes, the masking, the rotation and the gates. The
model-derived numbers are graded by the script itself, never here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "train_pantry_selection.py"


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("pantry_selection_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_selection_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def trainer(stage):
    return stage.load_trainer()


@pytest.fixture(scope="module")
def ecosystem(trainer):
    return trainer._load_generator()


@pytest.fixture(scope="module")
def small(trainer, ecosystem):
    """Eight train sessions and eight held-out sessions from the k=2 corpus."""
    corpus = trainer.load_corpus(minimal_binding=True, order_augmented=True, roster_size=2)
    return {
        "train": list(corpus["train"])[:16],
        "heldout": list(corpus["heldout"])[:8],
        "names": sorted(ecosystem.ACTORS),
        "meta": corpus["meta"],
    }


@pytest.fixture(scope="module")
def probe(stage):
    return stage.load_probe()


@pytest.fixture(scope="module")
def features(stage, trainer, probe, small):
    core = trainer.build_core(hidden=32, emb=16, device="cpu", kind="turnstore", memory=True)
    return {
        "core": core,
        "train": stage.session_features(trainer, probe, core, small["train"], small["names"]),
        "heldout": stage.session_features(trainer, probe, core, small["heldout"], small["names"]),
        "names_vec": stage.name_vectors(core, small["names"], trainer),
    }


# --------------------------------------------------------------------------- #
# the arithmetic
# --------------------------------------------------------------------------- #
def test_wilson_matches_the_textbook_interval(stage):
    low, high = stage.wilson(100, 200)
    assert low == pytest.approx(0.4314, abs=5e-4)
    assert high == pytest.approx(0.5686, abs=5e-4)
    low, high = stage.wilson(0, 200)
    assert low == 0.0
    assert 0.0 < high < 0.03
    assert stage.wilson(0, 0) == (0.0, 0.0)


def test_wilson_interval_narrows_with_more_trials(stage):
    small = stage.wilson(5, 10)
    large = stage.wilson(500, 1000)
    assert (large[1] - large[0]) < (small[1] - small[0])


def test_summarise_counts_the_agreement_it_names(stage):
    picks = ["Alex", "Alex", "Betty"]
    block = stage.summarise(picks, ["Alex", "Betty", "Betty"])
    assert block["n"] == 3
    assert block["correct"] == 2
    assert block["exact"] == pytest.approx(0.6667)
    assert block["distinct_predictions"] == 2
    assert block["top_prediction"] == "Alex"
    assert block["top_share"] == pytest.approx(0.6667)
    assert block["wilson_lower"] < block["exact"] < block["wilson_upper"]


def test_summarise_is_zero_safe(stage):
    block = stage.summarise([], [])
    assert block["n"] == 0 and block["exact"] == 0.0


# --------------------------------------------------------------------------- #
# the intervention
# --------------------------------------------------------------------------- #
def test_rotation_moves_every_row_to_its_neighbour(stage):
    torch = pytest.importorskip("torch")
    tensor = torch.arange(8, dtype=torch.float32).reshape(4, 2)
    rotated = stage.rotate_rows(torch, tensor)
    assert torch.equal(rotated[0], tensor[1])
    assert torch.equal(rotated[-1], tensor[0])
    assert stage.mutation_share(tensor) == 1.0


def test_rotation_is_not_identity_when_every_row_is_equal(stage):
    torch = pytest.importorskip("torch")
    tensor = torch.ones(4, 3)
    assert stage.mutation_share(tensor) == 0.0
    assert stage.mutation_share(torch.ones(1, 3)) == 0.0


# --------------------------------------------------------------------------- #
# the head
# --------------------------------------------------------------------------- #
def test_head_scores_one_value_per_candidate(stage):
    torch = pytest.importorskip("torch")
    head = stage.build_head(torch, 8, 4, 6, 5, seed=7)
    scores = head(torch.randn(3, 8), torch.randn(3, 4), torch.randn(3, 5, 6))
    assert tuple(scores.shape) == (3, 5)
    assert stage.parameter_count(head) > 0


def test_head_initialisation_is_identical_across_arms(stage):
    torch = pytest.importorskip("torch")
    first = stage.build_head(torch, 8, 4, 6, 5, seed=11)
    second = stage.build_head(torch, 8, 4, 6, 5, seed=11)
    for left, right in zip(first.state_dict().values(), second.state_dict().values()):
        assert torch.equal(left, right)


def test_masking_removes_the_input_from_the_computation(stage):
    torch = pytest.importorskip("torch")
    data = {
        "h": torch.randn(4, 8),
        "read": torch.randn(4, 4),
        "roster": torch.tensor([[0, 2], [1, 3], [2, 0], [3, 1]]),
    }
    names_vec = torch.randn(6, 5)
    state, read, candidates = stage._prepare(torch, data, names_vec, slice(None), True, True)
    assert torch.equal(state, data["h"]) and torch.equal(read, data["read"])
    masked_state, masked_read, _ = stage._prepare(torch, data, names_vec, slice(None), False, False)
    assert torch.count_nonzero(masked_state) == 0
    assert torch.count_nonzero(masked_read) == 0
    assert tuple(candidates.shape) == (4, 2, 5)
    assert torch.equal(candidates[0, 1], names_vec[2])


def test_a_separable_head_fits_and_predicts_its_candidates(stage):
    torch = pytest.importorskip("torch")
    torch.manual_seed(3)
    count, candidates, dim = 24, 3, 5
    roster = torch.as_tensor([[0, 1], [1, 2], [0, 2]] * 8, dtype=torch.long)
    target = torch.as_tensor([0, 1, 1] * 8, dtype=torch.long)
    names_vec = torch.randn(4, dim)
    read = torch.zeros(count, dim)
    for row in range(count):
        read[row] = names_vec[roster[row, target[row]]] * 3.0
    data = {
        "h": torch.zeros(count, dim),
        "read": read,
        "roster": roster,
        "target": target,
        "culprit": [""] * count,
    }
    head = stage.build_head(torch, dim, dim, dim, 8, seed=5)
    curve = stage.fit_head(
        torch,
        head,
        data,
        names_vec,
        steps=300,
        batch=8,
        lr=1e-2,
        weight_decay=0.0,
        seed=5,
        use_h=False,
        use_read=True,
        observer=lambda step: {"step": step},
        every=100,
    )
    assert [point["step"] for point in curve] == [100, 200, 300]
    names = ["a", "b", "c", "d"]
    picks = stage.predict(torch, head, data, names_vec, names, use_h=False, use_read=True)
    assert len(picks) == count
    expected = [names[int(roster[row, target[row]])] for row in range(count)]
    assert sum(1 for left, right in zip(picks, expected) if left == right) >= count - 1


# --------------------------------------------------------------------------- #
# features
# --------------------------------------------------------------------------- #
def test_features_carry_both_levels_and_a_roster_target(features, small):
    train = features["train"]
    assert train["h"].shape[0] == len(small["train"])
    assert train["read"].shape[0] == len(small["train"])
    assert train["read"].shape[1] > 0
    assert train["roster"].shape[1] == 2
    assert int(train["target"].max()) < 2
    for row, session in enumerate(small["train"]):
        roster = session["environment"]["actors"]
        assert session["ground_truth_oracle"]["culprit"] == roster[int(train["target"][row])]


def test_name_vectors_are_the_mean_byte_embedding(stage, features, small, trainer):
    torch = pytest.importorskip("torch")
    core = features["core"]
    table = core.embedding.weight.detach()
    name = small["names"][0]
    ids = [trainer.BYTE_OFFSET + byte for byte in name.encode("utf-8")]
    expected = table[torch.as_tensor(ids, dtype=torch.long)].mean(dim=0)
    assert torch.allclose(features["names_vec"][0], expected)


# --------------------------------------------------------------------------- #
# the gates and the fork
# --------------------------------------------------------------------------- #
def _block(low, high):
    return {"exact": (low + high) / 2, "wilson_lower": low, "wilson_upper": high}


def _arms(*, fit=0.99, held=0.70, upper=0.78, order=0.90, h_upper=0.56, cand_upper=0.56):
    block = _block
    return {
        "read": {
            "fit": {"exact": fit},
            "heldout": block(held - 0.06, upper),
            "order_same_person": order,
        },
        "h": {"fit": {"exact": fit}, "heldout": block(0.44, h_upper)},
        "cand": {"fit": {"exact": fit}, "heldout": block(0.44, cand_upper)},
    }


def _gates(stage, arms, *, k=2, permuted_upper=0.56, outside=0):
    permuted = {"exact": 0.5, "wilson_lower": 0.44, "wilson_upper": permuted_upper}
    return stage.gates(arms, k=k, permuted=permuted, outside={arm: outside for arm in stage.ARMS})


def test_gates_pass_together_when_the_head_beats_every_baseline(stage):
    gate = _gates(stage, _arms())
    assert all(block["pass"] for block in gate.values())
    assert stage.branch(gate)["id"] == "R4e-readout-was-missing"


def test_gate_fit_failure_selects_the_cannot_fit_branch(stage):
    gate = _gates(stage, _arms(fit=0.50))
    assert gate["S1_fit"]["pass"] is False
    assert stage.branch(gate)["id"] == "R4a-head-cannot-fit"


def test_gate_transfer_failure_selects_fits_not_transfers(stage):
    gate = _gates(stage, _arms(held=0.50, upper=0.57))
    assert gate["S2_transfer"]["pass"] is False
    assert stage.branch(gate)["id"] == "R4b-fits-not-transfers"


def test_gate_attribution_failure_selects_uses_a_prior(stage):
    gate = _gates(stage, _arms(held=0.60, upper=0.68), permuted_upper=0.70)
    assert gate["S2_transfer"]["pass"] is True
    assert gate["S4_attribution"]["pass"] is False
    assert stage.branch(gate)["id"] == "R4c-uses-a-prior"


def test_gate_order_failure_selects_unstable_under_order(stage):
    gate = _gates(stage, _arms(order=0.55))
    assert gate["S3_order"]["pass"] is False
    assert stage.branch(gate)["id"] == "R4d-unstable-under-order"


def test_an_out_of_roster_pick_fails_the_construction_gate(stage):
    gate = _gates(stage, _arms(), outside=1)
    assert gate["R3_in_roster"]["pass"] is False


def test_branch_is_a_pure_function_of_the_gates(stage):
    gate = _gates(stage, _arms())
    assert stage.branch(gate) == stage.branch(json.loads(json.dumps(gate)))


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _report(stage, **overrides):
    arms = _arms(**overrides)
    gate = _gates(stage, arms)
    return {
        "k": 2,
        "arms": {
            arm: {**arms[arm], "curve": [{"step": 500}, {"step": 1000}], "parameters": 16641}
            for arm in stage.ARMS
        },
        "permuted_read": {"exact": 0.5, "wilson_lower": 0.44, "wilson_upper": 0.56},
        "gates": gate,
        "branch": stage.branch(gate),
        "r4_cost": {
            "weights_hash_before": "abc",
            "weights_hash_after": "abc",
            "carrier_unchanged": True,
            "checkpoint_sha256_before": "def",
            "checkpoint_sha256_after": "def",
            "checkpoint_unchanged": True,
            "read_permutation_share": 1.0,
        },
        "instrument_ok": True,
    }


def test_check_accepts_a_well_formed_report(stage, tmp_path):
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(_report(stage)), encoding="utf-8")
    assert stage.check(path) == []


def test_check_rejects_a_stale_branch(stage, tmp_path):
    data = _report(stage)
    assert data["branch"]["id"] == "R4e-readout-was-missing"
    data["branch"]["id"] = "R4a-head-cannot-fit"
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert any("stale" in problem for problem in stage.check(path))


def test_check_rejects_a_changed_carrier(stage, tmp_path):
    data = _report(stage)
    data["r4_cost"]["weights_hash_after"] = "changed"
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = stage.check(path)
    assert any("carrier weights changed" in problem for problem in problems)


def test_check_rejects_a_missing_arm(stage, tmp_path):
    data = _report(stage)
    data["arms"].pop("cand")
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert any("arm cand is missing" in problem for problem in stage.check(path))


def test_check_rejects_a_short_curve(stage, tmp_path):
    data = _report(stage)
    data["arms"]["read"]["curve"] = [{"step": 500}]
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert any("fewer than two curve points" in problem for problem in stage.check(path))


def test_check_rejects_a_permutation_that_did_nothing(stage, tmp_path):
    data = _report(stage)
    data["r4_cost"]["read_permutation_share"] = 0.0
    path = tmp_path / "sel67.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert any("not a real rotation" in problem for problem in stage.check(path))


def test_cli_requires_a_report_or_a_check(stage):
    with pytest.raises(SystemExit):
        stage.main([])
