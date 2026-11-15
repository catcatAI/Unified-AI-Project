# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§68 contracts: the readouts, their controls and the mechanical fork.

No trained checkpoint is read here. The arithmetic is exercised on tensors the
test builds, and the two integration cases read a handful of corpus sessions to
pin the target extraction and the roster-preserving shift. The model-derived
numbers are graded by the script itself, never here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_pantry_contents.py"


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("pantry_contents_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_contents_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def trainer(stage):
    return stage.load_selection().load_trainer()


@pytest.fixture(scope="module")
def ecosystem(trainer):
    return trainer._load_generator()


@pytest.fixture(scope="module")
def probe(stage):
    return stage.load_selection().load_probe()


@pytest.fixture(scope="module")
def small(trainer, ecosystem):
    """Sixteen order-augmented train sessions (eight structures) and eight held out."""
    corpus = trainer.load_corpus(minimal_binding=True, order_augmented=True, roster_size=2)
    return {
        "train": list(corpus["train"])[:16],
        "heldout": list(corpus["heldout"])[:8],
        "names": sorted(ecosystem.ACTORS),
        "colours": sorted(ecosystem.COLOURS),
    }


# --------------------------------------------------------------------------- #
# targets
# --------------------------------------------------------------------------- #
def test_live_value_reads_the_evidence_turn(stage, small):
    session = small["train"][0]
    turn = int(session["session_meta"]["evidence_turn"])
    expected = [a["value"] for a in session["turns"][turn]["asserts"] if a["kind"] == "seen"]
    assert stage.live_value(session) == expected[0]


def test_live_value_refuses_a_session_without_the_assert(stage, small):
    session = json.loads(json.dumps(small["train"][0]))
    turn = int(session["session_meta"]["evidence_turn"])
    session["turns"][turn]["asserts"] = []
    with pytest.raises(SystemExit):
        stage.live_value(session)


def test_structure_of_groups_both_roster_orders(stage, small):
    structures = [stage.structure_of(session) for session in small["train"]]
    counts = {}
    for key in structures:
        counts[key] = counts.get(key, 0) + 1
    assert sorted(counts.values()) == [2] * (len(structures) // 2)
    assert small["train"][0]["session_id"] in structures[0]


def test_targets_carry_the_three_answers(stage, small):
    block = stage.targets(small["train"], small["names"], small["colours"])
    assert len(block["colour"]) == len(block["roster"]) == len(block["culprit"]) == 16
    for row, session in enumerate(small["train"]):
        assert sum(block["roster"][row]) == 2
        assert block["colour"][row] == small["colours"].index(stage.live_value(session))
        assert block["culprit"][row] == small["names"].index(
            session["ground_truth_oracle"]["culprit"]
        )
        assert block["structure"][row] == stage.structure_of(session)


# --------------------------------------------------------------------------- #
# chance levels and baselines
# --------------------------------------------------------------------------- #
def test_chance_levels_are_the_uniform_pick(stage):
    levels = stage.chance_levels(8, 12, 2)
    assert levels["colour"] == pytest.approx(1 / 8)
    assert levels["culprit"] == pytest.approx(1 / 12)
    assert levels["roster"] == pytest.approx(1 / 66)
    assert stage.chance_levels(8, 12, 5)["roster"] == pytest.approx(1 / 792)


@pytest.mark.parametrize(
    "colours,names,k",
    [(0, 12, 2), (8, 0, 2), (8, 12, 0), (8, 12, 13)],
)
def test_chance_levels_reject_impossible_dimensions(stage, colours, names, k):
    with pytest.raises(SystemExit):
        stage.chance_levels(colours, names, k)


def test_majority_baselines_take_the_train_mode(stage):
    names = ["A", "B", "C"]
    colours = ["red", "blue"]
    train = {
        "colour": [0, 0, 1],
        "roster": [[1, 1, 0], [1, 0, 1]],
        "culprit": [0, 1],
    }
    test = {"colour": [0, 1], "roster": [[1, 0, 1]], "culprit": [1]}
    block = stage.majority_baselines(train, test, names, colours)
    assert block["colour"]["prediction"] == "red"
    assert block["colour"]["correct"] == 1 and block["colour"]["exact"] == 0.5
    assert block["roster"]["prediction"] == ["A", "B"]
    assert block["roster"]["correct"] == 0
    assert block["culprit"]["prediction"] == "A"
    assert block["culprit"]["correct"] == 0


# --------------------------------------------------------------------------- #
# the probe's arithmetic
# --------------------------------------------------------------------------- #
def test_standardise_centres_on_the_train_split(stage):
    torch = pytest.importorskip("torch")
    train = torch.tensor([[0.0, 10.0], [2.0, 14.0]])
    held = torch.tensor([[100.0, -3.0]])
    scaled, scaled_held = stage.standardise(train, held)
    assert torch.allclose(scaled.mean(dim=0), torch.zeros(2), atol=1e-6)
    assert torch.allclose(scaled.std(dim=0, unbiased=False), torch.ones(2), atol=1e-6)
    # the held-out row keeps the train scale: it is not re-centred on itself
    assert scaled_held[0, 0] > 50.0


def test_fold_of_keeps_both_orders_together(stage):
    keys = ["a", "b", "c", "d"]
    assert stage.fold_of("b", keys, 2) == stage.fold_of("b", keys, 2)
    assert stage.fold_of("a", keys, 4) == 0 and stage.fold_of("d", keys, 4) == 3
    assert stage.fold_of("d", keys, 4) == stage.fold_of("d", keys, 4)


def test_score_predictions_grades_a_set_as_exact(stage):
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[3.0, 2.0, 0.0, -1.0], [0.0, 5.0, 4.0, -2.0]])
    targets = torch.tensor([[1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 1.0, 0.0]])
    block = stage.score_predictions(torch, logits, targets, kind="set", k=2)
    assert block == {"n": 2, "correct": 2}
    shifted = stage.score_predictions(torch, logits, targets[[1, 0]], kind="set", k=2)
    assert shifted["correct"] == 0


def test_argmax_readout_counts_only_the_top_label(stage):
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[2.0, 0.0], [0.0, 3.0]])
    targets = torch.tensor([0, 0])
    block = stage.score_predictions(torch, logits, targets, kind="single")
    assert block == {"n": 2, "correct": 1}


def test_a_separable_probe_fits_and_generalises(stage):
    torch = pytest.importorskip("torch")
    generator = torch.Generator().manual_seed(5)
    centres = torch.tensor([[8.0, 0.0], [0.0, 8.0], [-8.0, -8.0]])
    labels = torch.arange(60) % 3
    train_x = centres[labels] + torch.randn(60, 2, generator=generator) * 0.2
    held_x = centres[labels] + torch.randn(60, 2, generator=generator) * 0.2
    block = stage.run_probe(
        torch,
        train_x,
        labels,
        held_x,
        labels,
        kind="single",
        out=3,
        seed=11,
        steps=2000,
    )
    assert block["in_sample"]["exact"] >= 0.95
    assert block["heldout"]["exact"] >= 0.95


def test_cross_validate_holds_whole_structures_out(stage):
    torch = pytest.importorskip("torch")
    generator = torch.Generator().manual_seed(9)
    labels = torch.arange(40) % 2
    features = torch.zeros(40, 4)
    features[:, 0] = labels * 6.0
    features += torch.randn(40, 4, generator=generator) * 0.1
    structures = [f"structure_{index // 2}" for index in range(40)]
    block = stage.cross_validate(
        torch, features, labels, structures, kind="single", out=2, seed=3, steps=2000
    )
    assert block["exact"] >= 0.9
    assert len(block["folds"]) == stage.FOLDS


# --------------------------------------------------------------------------- #
# the shift control
# --------------------------------------------------------------------------- #
def test_shift_labels_moves_every_label(stage):
    torch = pytest.importorskip("torch")
    for width in (2, 3, 5):
        target = torch.arange(60) % width
        shifted = stage.shift_labels(target, width)
        assert torch.all(shifted != target)
        assert int(shifted.max()) < width and int(shifted.min()) >= 0
        assert sorted(shifted.tolist()) == sorted(target.tolist())


def test_shift_labels_needs_two_positions(stage):
    torch = pytest.importorskip("torch")
    with pytest.raises(SystemExit):
        stage.shift_labels(torch.zeros(4, dtype=torch.long), 1)


def test_shifted_culprits_stay_in_their_row_roster(stage, trainer, probe, small):
    torch = pytest.importorskip("torch")
    core = trainer.build_core(hidden=32, emb=16, device="cpu", kind="turnstore", memory=True)
    session = stage.load_selection()
    features = session.session_features(trainer, probe, core, small["train"], small["names"])
    shifted = stage.shift_labels(features["target"], 2)
    picks, in_roster = stage.shifted_culprits(features, shifted, small["names"], 2)
    assert in_roster == 1.0
    assert len(picks) == len(small["train"])
    for row, pick in enumerate(picks):
        roster = [small["names"][index] for index in features["roster"][row].tolist()]
        assert pick in roster


def test_capacity_control_permutes_the_labels(stage):
    torch = pytest.importorskip("torch")
    features = torch.randn(40, 3)
    labels = torch.arange(40) % 8
    block = stage.capacity_ceiling(torch, features, labels, kind="single", out=8, steps=5)
    assert block["permutation_is_bijection"] is True
    assert block["labels_changed"] >= 0.5
    assert block["n"] == 40
    assert 0.0 <= block["exact"] <= 1.0


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def _block(in_sample: float, capacity: float, correct: int, n: int = 200) -> dict:
    return {
        "in_sample": {"exact": in_sample, "correct": int(in_sample * n), "n": n},
        "heldout": {"exact": round(correct / n, 4), "correct": correct, "n": n},
        "capacity": {
            "exact": capacity,
            "labels_changed": 0.9,
            "permutation_is_bijection": True,
            "seed": 1,
        },
        "in_distribution": {"exact": 0.0, "correct": 0, "n": 0, "folds": []},
    }


def make_report(**overrides) -> dict:
    """A report whose numbers are chosen so each gate can be steered by hand."""
    report = {
        "k": 2,
        "dimensions": {"colours": 8, "names": 12},
        "majority_baselines": {
            "colour": {"exact": 0.1},
            "roster": {"exact": 0.015},
            "culprit": {"exact": 0.09},
        },
        "colour": _block(1.0, 0.22, 160),
        "roster": _block(1.0, 0.05, 150),
        "culprit": _block(1.0, 0.16, 100),
        "shift": {
            "fit": {"exact": 1.0},
            "same_rows_true_labels": {"exact": 0.0},
            "labels_changed": 1.0,
            "labels_in_row_roster": 1.0,
        },
        "instrument": {"carrier_unchanged": True, "checkpoint_unchanged": True},
        "instrument_ok": True,
    }
    report.update(overrides)
    return report


def test_gates_pass_when_both_facts_transfer(stage):
    gate = stage.gates(make_report())
    assert gate["G1_readout_can_fit"]["pass"] is True
    assert gate["G2_shift_fits"]["pass"] is True
    assert gate["G3_colour"]["transfers"] is True
    assert gate["G4_roster"]["transfers"] is True
    assert gate["G5_culprit_control"]["transfers"] is False


def test_transfer_needs_the_effect_floor_not_just_the_baseline(stage):
    # 90/200 = 0.45: its Wilson lower bound (0.38) is far above the 0.125 chance level, so a
    # baseline-relative rule would call this a transfer. The registered effect floor refuses it.
    weak = stage.gates(make_report(colour=_block(1.0, 0.22, 90)))["G3_colour"]
    assert weak["heldout_exact"] == 0.45
    assert weak["wilson_lower"] > weak["floor"]
    assert weak["transfers"] is False
    # 110/200 = 0.55 clears the floor; the interval leg then confirms it clears the baseline too
    strong = stage.gates(make_report(colour=_block(1.0, 0.22, 110)))["G3_colour"]
    assert strong["heldout_exact"] == 0.55
    assert strong["wilson_lower"] > strong["floor"]
    assert strong["transfers"] is True


def test_the_culprit_control_uses_the_roster_ceiling(stage):
    # 100/200 = 0.50 is exactly the k=2 roster ceiling, so it is not a contradiction
    assert stage.gates(make_report())["G5_culprit_control"]["transfers"] is False
    strong = stage.gates(make_report(culprit=_block(1.0, 0.16, 160)))
    assert strong["G5_culprit_control"]["transfers"] is True


def test_gates_flag_an_in_sample_fit_at_its_own_capacity(stage):
    gate = stage.gates(make_report(colour=_block(0.30, 0.28, 120)))
    assert gate["G3_colour"]["readable"] is False
    assert gate["G3_colour"]["in_sample_above_capacity"] is True


def _gate(**flags) -> dict:
    base = {
        "G1_readout_can_fit": {"pass": True, "in_sample": 1.0},
        "G2_shift_fits": {"pass": True, "value": 1.0},
        "G5_culprit_control": {
            "transfers": False,
            "wilson_lower": 0.1,
            "roster_ceiling": 0.5,
        },
        "G3_colour": {
            "readable": True,
            "transfers": False,
            "heldout_exact": 0.1,
            "in_sample": 1.0,
            "capacity": 0.2,
        },
        "G4_roster": {
            "readable": True,
            "transfers": False,
            "heldout_exact": 0.1,
            "in_sample": 1.0,
            "capacity": 0.05,
        },
    }
    for key, value in flags.items():
        base[key] = {**base[key], **value}
    return base


@pytest.mark.parametrize(
    "flags,expected",
    [
        ({"G1_readout_can_fit": {"pass": False}}, "N0-instrument"),
        ({"G5_culprit_control": {"transfers": True}}, "N5-contradiction"),
        ({"G2_shift_fits": {"pass": False}}, "N4-fit-needs-true-labels"),
        (
            {"G3_colour": {"transfers": True}, "G4_roster": {"transfers": True}},
            "N1-facts-without-pairing",
        ),
        ({"G3_colour": {"transfers": True}}, "N2-partial-facts"),
        ({"G3_colour": {"readable": False}}, "N3-facts-not-linearly-readable"),
        ({}, "N6-session-key-only"),
    ],
)
def test_every_branch_is_reachable(stage, flags, expected):
    fork = stage.branch(_gate(**flags))
    assert fork["id"] == expected
    assert fork["reading"] and fork["next"]


def test_the_branch_order_puts_the_instrument_first(stage):
    # a broken readout outranks every substantive reading, including a contradiction
    fork = stage.branch(
        _gate(
            G1_readout_can_fit={"pass": False},
            G5_culprit_control={"transfers": True},
            G3_colour={"transfers": True},
        )
    )
    assert fork["id"] == "N0-instrument"


def test_branch_is_a_pure_function_of_the_gates(stage):
    once = stage.branch(_gate(G3_colour={"transfers": True}))
    twice = stage.branch(_gate(G3_colour={"transfers": True}))
    assert once == twice


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _write(tmp_path: Path, report: dict, compute: bool = True) -> Path:
    if compute:
        report["gates"] = stage_gates(report)
        report["branch"] = stage_branch(report["gates"])
    else:
        report.setdefault("gates", {})
        report.setdefault("branch", {})
    path = tmp_path / "contents68.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def stage_gates(report: dict) -> dict:
    module = sys.modules["pantry_contents_under_test"]
    return module.gates(report)


def stage_branch(gate: dict) -> dict:
    module = sys.modules["pantry_contents_under_test"]
    return module.branch(gate)


def test_check_accepts_a_well_formed_report(stage, tmp_path):
    path = _write(tmp_path, make_report())
    assert stage.check(path) == []


def test_check_rejects_a_stale_gate(stage, tmp_path):
    report = make_report()
    path = _write(tmp_path, report)
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["colour"]["heldout"]["exact"] = 0.1
    stored["colour"]["heldout"]["correct"] = 20
    path.write_text(json.dumps(stored), encoding="utf-8")
    assert any("stale" in problem for problem in stage.check(path))


def test_check_rejects_a_changed_carrier(stage, tmp_path):
    report = make_report()
    report["instrument"]["carrier_unchanged"] = False
    path = _write(tmp_path, report)
    assert any("carrier" in problem for problem in stage.check(path))


def test_check_rejects_a_shift_that_left_the_roster(stage, tmp_path):
    report = make_report()
    report["shift"]["labels_in_row_roster"] = 0.5
    path = _write(tmp_path, report)
    problems = stage.check(path)
    assert any("roster" in problem or "stale" in problem for problem in problems)


def test_check_rejects_a_capacity_control_that_did_nothing(stage, tmp_path):
    report = make_report()
    report["roster"]["capacity"]["labels_changed"] = 0.0
    path = _write(tmp_path, report)
    assert any("capacity" in problem for problem in stage.check(path))


def test_check_rejects_a_missing_baseline(stage, tmp_path):
    report = make_report()
    report["majority_baselines"] = {}
    path = _write(tmp_path, report, compute=False)
    assert any("baseline" in problem for problem in stage.check(path))


def test_cli_requires_a_report_or_a_check(stage):
    with pytest.raises(SystemExit):
        stage.main([])
