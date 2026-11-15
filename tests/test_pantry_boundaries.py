# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§69 contracts: the three boundaries, the tuple readout and the mechanical fork.

No trained checkpoint is read here. The arithmetic runs on tensors and dicts the
test builds; the corpus is touched only to pin target extraction (roster order,
the roster turn's own assert, the shared boundary index). The model-derived
numbers are graded by the script, never here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_pantry_boundaries.py"


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("pantry_boundaries_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_boundaries_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def contents(stage):
    return stage.load_contents()


@pytest.fixture(scope="module")
def trainer(contents):
    return contents.load_selection().load_trainer()


@pytest.fixture(scope="module")
def ecosystem(trainer):
    return trainer._load_generator()


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
# the three boundaries
# --------------------------------------------------------------------------- #
def test_boundary_turns_are_roster_evidence_and_last(stage, small):
    turns = stage.boundary_turns(small["train"][0])
    assert turns == {"roster": 1, "evidence": 2, "answer": 3}
    assert turns["answer"] == len(small["train"][0]["turns"]) - 1


def test_shared_boundaries_accepts_identical_sessions(stage, small):
    assert stage.shared_boundaries(small["train"]) == {"roster": 1, "evidence": 2, "answer": 3}


def test_shared_boundaries_refuses_a_moved_boundary(stage, small):
    rows = [json.loads(json.dumps(row)) for row in small["train"][:2]]
    rows[1]["session_meta"]["evidence_turn"] = 1
    with pytest.raises(SystemExit):
        stage.shared_boundaries(rows)


def test_roster_names_keep_the_stated_order(stage, small):
    session = small["train"][0]
    assert stage.roster_names(session) == list(session["environment"]["actors"])


def test_pairing_reads_the_roster_turn_assert(stage, small):
    session = small["train"][0]
    turn = int(session["session_meta"]["roster_turn"])
    mapping = next(a["value"] for a in session["turns"][turn]["asserts"] if a["kind"] == "roster")
    expected = {name: colour for colour, name in mapping.items()}
    assert stage.pairing_of(session) == expected


def test_pairing_refuses_a_session_without_the_assert(stage, small):
    session = json.loads(json.dumps(small["train"][0]))
    turn = int(session["session_meta"]["roster_turn"])
    session["turns"][turn]["asserts"] = []
    with pytest.raises(SystemExit):
        stage.pairing_of(session)


# --------------------------------------------------------------------------- #
# targets
# --------------------------------------------------------------------------- #
def test_roster_target_is_a_multi_hot_over_every_name(stage, small, contents):
    got = stage.targets(small["train"], small["names"], small["colours"], contents)
    assert got["roster"][0].count(1) == 2
    assert len(got["roster"][0]) == len(small["names"])
    stated = set(stage.roster_names(small["train"][0]))
    assert {small["names"][i] for i, flag in enumerate(got["roster"][0]) if flag} == stated


def test_colour_target_is_the_live_value_index(stage, small, contents):
    got = stage.targets(small["train"], small["names"], small["colours"], contents)
    for row, session in enumerate(small["train"]):
        assert small["colours"][got["colour"][row]] == contents.live_value(session)


def test_pairing_target_is_in_roster_order(stage, small, contents):
    got = stage.targets(small["train"], small["names"], small["colours"], contents)
    for row, session in enumerate(small["train"]):
        mapping = stage.pairing_of(session)
        expected = [small["colours"].index(mapping[name]) for name in stage.roster_names(session)]
        assert got["pairing"][row] == expected
        assert len(got["pairing"][row]) == 2


def test_culprit_target_is_the_oracle_name(stage, small, contents):
    got = stage.targets(small["train"], small["names"], small["colours"], contents)
    for row, session in enumerate(small["train"]):
        assert small["names"][got["culprit"][row]] == session["ground_truth_oracle"]["culprit"]


def test_structure_key_is_shared_by_both_roster_orders(stage, small, contents):
    got = stage.targets(small["train"], small["names"], small["colours"], contents)
    groups = {}
    for row, key in enumerate(got["structure"]):
        groups.setdefault(key, []).append(row)
    assert len(groups) == len(small["train"]) // 2
    for rows in groups.values():
        assert len(rows) == 2
        first, second = (stage.pairing_of(small["train"][row]) for row in rows)
        # the twin reverses the order the roster is *stated* in, not the mapping
        assert list(first.items())[::-1] == list(second.items())
        assert got["pairing"][rows[0]] == got["pairing"][rows[1]]


# --------------------------------------------------------------------------- #
# chance levels and the majority baseline
# --------------------------------------------------------------------------- #
def test_chance_levels_are_the_uniform_picks(stage):
    levels = stage.chance_levels(8, 12, 2)
    assert levels["colour"] == pytest.approx(1 / 8)
    assert levels["roster"] == pytest.approx(1 / 66)
    assert levels["culprit"] == pytest.approx(1 / 12)
    assert levels["pairing"] == pytest.approx(1 / 64)
    assert levels["pairing_slot"] == pytest.approx(1 / 8)


def test_pairing_chance_is_one_over_eight_to_the_k(stage):
    for k, expected in ((2, 1 / 8**2), (3, 1 / 8**3), (5, 1 / 8**5)):
        assert stage.chance_levels(8, 12, k)["pairing"] == pytest.approx(expected)


def test_chance_levels_refuse_impossible_dimensions(stage):
    with pytest.raises(SystemExit):
        stage.chance_levels(8, 12, 0)
    with pytest.raises(SystemExit):
        stage.chance_levels(0, 12, 2)
    with pytest.raises(SystemExit):
        stage.chance_levels(8, 12, 13)


def test_majority_baseline_single_label(stage):
    got = stage.majority_baseline([1, 1, 2], [1, 2, 2, 2])
    assert got["prediction"] == 1
    assert got["correct"] == 1
    assert got["exact"] == pytest.approx(0.25)


def test_majority_baseline_tuple_reports_row_and_slot(stage):
    train = [(0, 1), (0, 1), (2, 2)]
    test = [(0, 1), (2, 2)]
    got = stage.majority_baseline(train, test)
    assert got["prediction"] == [0, 1]
    assert got["exact"] == pytest.approx(0.5)
    # flattened train is 0,1,0,1,2,2: 0 is the first of three tied answers
    assert got["slot_prediction"] == 0
    assert got["slot_n"] == 4
    assert got["slot_exact"] == pytest.approx(0.25)


def test_as_key_makes_sequences_hashable(stage):
    assert stage.as_key([1, 2]) == (1, 2)
    assert stage.as_key(3) == 3


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def test_single_label_scoring_counts_argmax_hits(stage):
    logits = torch.tensor([[3.0, 0.0], [0.0, 3.0], [2.0, 1.0]])
    targets = torch.tensor([0, 1, 1])
    got = stage.score_predictions(logits, targets, kind="single")
    assert got == {"n": 3, "correct": 2}


def test_set_scoring_requires_the_exact_top_k(stage):
    logits = torch.tensor([[3.0, 2.0, 0.0], [0.0, 2.0, 3.0]])
    targets = torch.tensor([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
    got = stage.score_predictions(logits, targets, kind="set", k=2)
    assert got["correct"] == 1


def test_tuple_scoring_reports_slot_and_strict_rates(stage):
    # two rows, two slots, three colours: one row perfect, one row half right
    logits = torch.tensor(
        [
            [9.0, 0.0, 0.0, 0.0, 9.0, 0.0],
            [0.0, 9.0, 0.0, 9.0, 0.0, 0.0],
        ]
    )
    targets = torch.tensor([[0, 1], [0, 0]])
    got = stage.score_predictions(logits, targets, kind="tuple")
    assert got["correct"] == 1
    assert got["slot_correct"] == 3
    assert got["slot_n"] == 4


def test_tuple_scoring_refuses_a_width_that_does_not_divide(stage):
    logits = torch.zeros(2, 7)
    targets = torch.zeros(2, 2, dtype=torch.long)
    with pytest.raises(SystemExit):
        stage.score_predictions(logits, targets, kind="tuple")


def test_scored_adds_the_per_slot_rate_only_when_present(stage):
    assert stage._scored({"n": 4, "correct": 1}) == {"n": 4, "correct": 1, "exact": 0.25}
    scored = stage._scored({"n": 2, "correct": 1, "slot_n": 4, "slot_correct": 3})
    assert scored["slot_exact"] == pytest.approx(0.75)


def test_wilson_brackets_the_estimate(stage):
    low, high = stage.wilson(50, 100)
    assert low < 0.5 < high
    assert stage.wilson(0, 0) == (0.0, 0.0)
    assert stage.wilson(0, 10)[0] == 0.0


# --------------------------------------------------------------------------- #
# one fact at one boundary
# --------------------------------------------------------------------------- #
def _cell(exact_in, exact_out, capacity, slot_in=0.0, slot_out=0.0, slot_capacity=0.0, n=200):
    return {
        "in_sample": {
            "n": n,
            "correct": int(round(exact_in * n)),
            "exact": exact_in,
            "slot_n": n * 2,
            "slot_correct": int(round(slot_in * n * 2)),
            "slot_exact": slot_in,
        },
        "heldout": {
            "n": n,
            "correct": int(round(exact_out * n)),
            "exact": exact_out,
            "slot_n": n * 2,
            "slot_correct": int(round(slot_out * n * 2)),
            "slot_exact": slot_out,
        },
        "capacity": {
            "n": n,
            "correct": int(round(capacity * n)),
            "exact": capacity,
            "slot_n": n * 2,
            "slot_correct": int(round(slot_capacity * n * 2)),
            "slot_exact": slot_capacity,
            "labels_changed": 1.0,
            "permutation_is_bijection": True,
        },
        "in_distribution": {"n": n, "correct": int(round(exact_out * n)), "exact": exact_out},
    }


def test_fact_gate_requires_the_effect_floor_and_the_interval(stage):
    baseline = {"exact": 0.10}
    passing = stage.fact_gate(_cell(0.99, 0.80, 0.10), baseline, 0.125)
    assert passing["transfers"] is True
    small = stage.fact_gate(_cell(0.99, 0.30, 0.10), baseline, 0.125)
    assert small["transfers"] is False


def test_fact_gate_uses_the_stricter_of_chance_and_baseline(stage):
    block = _cell(0.99, 0.30, 0.10)
    got = stage.fact_gate(block, {"exact": 0.40}, 0.125)
    assert got["floor"] == pytest.approx(0.40)
    assert got["transfers"] is False


def test_fact_gate_marks_a_capacity_limited_cell(stage):
    block = _cell(0.99, 0.90, 0.95)
    got = stage.fact_gate(block, {"exact": 0.0}, 0.125)
    assert got["capacity_limited"] is True


def test_slot_metric_reads_the_per_slot_fields(stage):
    block = _cell(0.99, 0.90, 0.10, slot_in=0.99, slot_out=0.55, slot_capacity=0.20)
    got = stage.fact_gate(block, {"slot_exact": 0.13}, 0.125, metric="slot")
    assert got["metric"] == "slot"
    assert got["heldout_exact"] == pytest.approx(0.55)
    assert got["chance"] == pytest.approx(0.125)
    assert got["transfers"] is True


# --------------------------------------------------------------------------- #
# the fork
# --------------------------------------------------------------------------- #
def _gate(**overrides):
    gate = {
        "G0_positive_control": {
            "pass": True,
            "in_sample": 1.0,
            "capacity": 0.1,
            "floor": 0.95,
            "capacity_max": 0.5,
        },
        "G1_colour_transfers_at_evidence": {"transfers": True, "heldout_exact": 0.8},
        "G2_colour_transfers_at_answer": {"transfers": False, "heldout_exact": 0.1},
        "G3_roster_transfers_at_its_turn": {"transfers": True, "heldout_exact": 0.6},
        "G4_roster_transfers_at_answer": {"transfers": False, "heldout_exact": 0.1},
        "G5_pairing_slot_transfers_at_its_turn": {"transfers": True, "heldout_exact": 0.6},
        "G6_pairing_slot_transfers_at_answer": {"transfers": False, "heldout_exact": 0.1},
        "G7_culprit_at_answer": {"transfers": False, "wilson_lower": 0.2, "roster_ceiling": 0.5},
    }
    for key, value in overrides.items():
        gate[key] = {**gate[key], **value}
    return gate


def test_branch_b0_when_the_positive_control_fails(stage):
    gate = _gate(G0_positive_control={"pass": False})
    assert stage.branch(gate)["id"] == "B0-instrument"


def test_branch_b0_outranks_every_other_condition(stage):
    gate = _gate(G0_positive_control={"pass": False}, G7_culprit_at_answer={"transfers": True})
    assert stage.branch(gate)["id"] == "B0-instrument"


def test_branch_b1_when_the_answer_beats_the_roster_ceiling(stage):
    gate = _gate(G7_culprit_at_answer={"transfers": True, "wilson_lower": 0.6})
    assert stage.branch(gate)["id"] == "B1-contradiction-with-§67"


def test_branch_b2_when_the_answer_boundary_contradicts_68(stage):
    gate = _gate(G2_colour_transfers_at_answer={"transfers": True})
    assert stage.branch(gate)["id"] == "B2-answer-boundary-contradicts-§68"


def test_branch_b3_when_facts_and_mapping_are_held_then_lost(stage):
    assert stage.branch(_gate())["id"] == "B3-held-at-their-turn-lost-by-the-answer"


def test_branch_b4_when_the_facts_transfer_but_the_mapping_does_not(stage):
    gate = _gate(G5_pairing_slot_transfers_at_its_turn={"transfers": False})
    assert stage.branch(gate)["id"] == "B4-facts-held-mapping-missing"


def test_branch_b5_when_only_one_fact_transfers(stage):
    gate = _gate(G3_roster_transfers_at_its_turn={"transfers": False})
    assert stage.branch(gate)["id"] == "B5-partial-facts-held"


def test_branch_b6_when_no_fact_transfers_anywhere(stage):
    gate = _gate(
        G1_colour_transfers_at_evidence={"transfers": False},
        G3_roster_transfers_at_its_turn={"transfers": False},
        G5_pairing_slot_transfers_at_its_turn={"transfers": False},
    )
    assert stage.branch(gate)["id"] == "B6-facts-not-transferable-anywhere"


def test_every_branch_has_a_next_step(stage):
    branches = [
        stage.branch(_gate(G0_positive_control={"pass": False})),
        stage.branch(_gate(G7_culprit_at_answer={"transfers": True})),
        stage.branch(_gate(G2_colour_transfers_at_answer={"transfers": True})),
        stage.branch(_gate()),
        stage.branch(_gate(G5_pairing_slot_transfers_at_its_turn={"transfers": False})),
        stage.branch(_gate(G3_roster_transfers_at_its_turn={"transfers": False})),
        stage.branch(
            _gate(
                G1_colour_transfers_at_evidence={"transfers": False},
                G3_roster_transfers_at_its_turn={"transfers": False},
                G5_pairing_slot_transfers_at_its_turn={"transfers": False},
            )
        ),
    ]
    assert len({item["id"] for item in branches}) == 7
    assert all(item["next"] for item in branches)


# --------------------------------------------------------------------------- #
# the report, its gates and its re-check
# --------------------------------------------------------------------------- #
def _report(stage, k=2):
    baselines = {
        "roster_boundary.roster": {"exact": 0.015},
        "roster_boundary.pairing": {"exact": 0.0, "slot_exact": 0.13},
        "evidence_boundary.colour": {"exact": 0.10},
        "evidence_boundary.roster": {"exact": 0.015},
        "evidence_boundary.pairing": {"exact": 0.0, "slot_exact": 0.13},
        "answer_boundary.colour": {"exact": 0.10},
        "answer_boundary.roster": {"exact": 0.015},
        "answer_boundary.pairing": {"exact": 0.0, "slot_exact": 0.13},
        "answer_boundary.culprit": {"exact": 0.08},
    }
    report = {
        "k": k,
        "dimensions": {"colours": 8, "names": 12},
        "turns": {"roster": 1, "evidence": 2, "answer": 3},
        "majority_baselines": baselines,
        "instrument": {"carrier_unchanged": True, "checkpoint_unchanged": True},
        "roster_boundary": {
            "roster": _cell(0.60, 0.22, 0.14),
            "pairing": _cell(0.25, 0.03, 0.19, slot_in=0.40, slot_out=0.20, slot_capacity=0.19),
        },
        "evidence_boundary": {
            "colour": _cell(0.91, 0.86, 0.21),
            "roster": _cell(0.30, 0.12, 0.05),
            "pairing": _cell(0.25, 0.18, 0.04, slot_in=0.40, slot_out=0.53, slot_capacity=0.04),
        },
        "answer_boundary": {
            "colour": _cell(0.29, 0.12, 0.20),
            "roster": _cell(0.28, 0.12, 0.03),
            "pairing": _cell(0.10, 0.02, 0.04, slot_in=0.20, slot_out=0.14, slot_capacity=0.04),
            "culprit": _cell(1.0, 0.29, 0.16),
        },
    }
    for boundary in ("roster_boundary", "evidence_boundary", "answer_boundary"):
        for name, block in report[boundary].items():
            block["read_only"] = _cell(0.2, 0.1, 0.1)
    report["gates"] = stage.gates(report)
    report["branch"] = stage.branch(report["gates"])
    return report


def test_gates_read_every_required_cell(stage):
    report = _report(stage)
    assert set(report["gates"]) == {
        "G0_positive_control",
        "G1_colour_transfers_at_evidence",
        "G2_colour_transfers_at_answer",
        "G3_roster_transfers_at_its_turn",
        "G4_roster_transfers_at_answer",
        "G5_pairing_slot_transfers_at_its_turn",
        "G6_pairing_slot_transfers_at_answer",
        "G7_culprit_at_answer",
    }


def test_gates_send_the_synthetic_report_to_b5(stage):
    report = _report(stage)
    assert report["gates"]["G0_positive_control"]["pass"] is True
    assert report["gates"]["G1_colour_transfers_at_evidence"]["transfers"] is True
    assert report["gates"]["G3_roster_transfers_at_its_turn"]["transfers"] is False
    assert report["branch"]["id"] == "B5-partial-facts-held"


def test_check_accepts_a_faithful_report(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    path = tmp_path / "ok.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert stage.check(path) == []


def test_check_rejects_a_stale_gate(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    report["gates"]["G1_colour_transfers_at_evidence"]["transfers"] = False
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert any("stale" in problem for problem in stage.check(path))


def test_check_rejects_a_stale_branch(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    report["branch"] = {"id": "B0-instrument", "reading": "", "next": ""}
    path = tmp_path / "branch.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert any("branch is stale" in problem for problem in stage.check(path))


def test_check_rejects_a_missing_read_only_column(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    del report["evidence_boundary"]["colour"]["read_only"]
    path = tmp_path / "no-read.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert any("read-only" in problem for problem in stage.check(path))


def test_check_rejects_a_capacity_control_that_is_not_a_permutation(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    report["answer_boundary"]["culprit"]["capacity"]["permutation_is_bijection"] = False
    path = tmp_path / "capacity.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert any("permutation" in problem for problem in stage.check(path))


def test_check_rejects_a_moved_carrier(stage, tmp_path):
    report = _report(stage)
    report["instrument_ok"] = True
    report["instrument"]["carrier_unchanged"] = False
    path = tmp_path / "carrier.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert any("carrier" in problem for problem in stage.check(path))


# --------------------------------------------------------------------------- #
# the registered design, pinned
# --------------------------------------------------------------------------- #
def test_registered_constants_are_pinned(stage):
    assert stage.PROBE_STEPS == 2000
    assert stage.PROBE_BATCH == 64
    assert stage.PROBE_LR == pytest.approx(1e-3)
    assert stage.PROBE_WEIGHT_DECAY == pytest.approx(1e-4)
    assert stage.PROBE_SEED == 20261121
    assert stage.CAPACITY_SEED == 20261121
    assert stage.FOLDS == 5
    assert stage.READABLE_FLOOR == pytest.approx(0.95)
    assert stage.TRANSFER_FLOOR == pytest.approx(0.50)
    assert stage.CAPACITY_MAX == pytest.approx(0.50)


def test_main_errors_without_a_mode(stage):
    with pytest.raises(SystemExit):
        stage.main([])


def test_main_check_reports_a_missing_file(stage, capsys):
    assert stage.main(["--check", "/definitely/not/here.json"]) == 1
    assert "FAILED" in capsys.readouterr().out
