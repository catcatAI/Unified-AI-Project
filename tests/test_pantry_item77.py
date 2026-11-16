# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§77 contract tests: the item-addressed write and the A/B verdict arithmetic.

Two things are tested and neither needs a fitted carrier:

* the split rule (``item_end_positions``) and the core's ``address="item"``
  switch - the rejected combinations, the plan's per-row slots, the padding
  mask, fresh-slot content equal to ``sigmoid(write_gate(h)) * value_proj(h)``,
  parameter parity with ``address="turn"``, and the turn-level slot count;
* the probe's registered arithmetic - ``M_slots`` (2 vs 3 active slots, 99%
  coverage of exactly 3), ``M_landed`` (99% of writes land), the contrast margin
  and fit comparability, the branch's fixed precedence, and ``check()``'s
  refusal of a tampered report.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
STATEFUL = REPO_ROOT / "apps" / "backend" / "src" / "ai" / "core" / "stateful_decoder.py"
ITEM77 = REPO_ROOT / "scripts" / "probe_pantry_item77.py"
TRAINER = REPO_ROOT / "scripts" / "train_pantry_deduction.py"

torch = pytest.importorskip("torch")

BYTE_OFFSET = 3


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def stateful():
    return _load_module("stateful_decoder_item77_under_test", STATEFUL)


@pytest.fixture(scope="module")
def trainer():
    return _load_module("pantry_item77_trainer_under_test", TRAINER)


@pytest.fixture(scope="module")
def probe77():
    return _load_module("pantry_item77_under_test", ITEM77)


def turn_tokens(text: str):
    """One turn's token ids exactly as ``turn_tokens`` in the trainer builds them."""
    return [BYTE_OFFSET + byte for byte in (text + "\n").encode("utf-8")]


def build(stateful, **overrides):
    kwargs = dict(
        token_count=259,
        hidden=16,
        emb=8,
        slots=16,
        slot_dim=16,
        value_dim=16,
        chunk_seconds=1.0,
        device="cpu",
        address="item",
        write_strength="learned",
        write_slots=1,
    )
    kwargs.update(overrides)
    return stateful.TurnStoreCore(**kwargs)


def active_slots(values) -> list:
    norms = values.norm(dim=-1)
    return [index for index in range(values.shape[0]) if float(norms[index].item()) > 0.0]


# --------------------------------------------------------------------------- #
# the split rule
# --------------------------------------------------------------------------- #
def test_item_end_positions_without_a_separator(trainer):
    assert trainer.item_end_positions(turn_tokens("abc")) == [2]


def test_item_end_positions_one_separator(trainer):
    tokens = turn_tokens("a、b")
    positions = trainer.item_end_positions(tokens)
    assert positions == [3, 4]
    # the separator stays at the end of the item it terminates
    assert tokens[positions[0]] - BYTE_OFFSET == "、".encode("utf-8")[-1]
    assert tokens[positions[1]] - BYTE_OFFSET == ord("b")


def test_item_end_positions_two_separators(trainer):
    assert trainer.item_end_positions(turn_tokens("a、b、c")) == [3, 7, 8]


def test_item_end_positions_empty_turn(trainer):
    assert trainer.item_end_positions(turn_tokens("")) == []


def test_item_end_positions_trailing_separator(trainer):
    assert trainer.item_end_positions(turn_tokens("a、")) == [3]


def test_item_end_positions_ends_before_the_newline(trainer):
    tokens = turn_tokens("a")
    assert tokens[-1] == BYTE_OFFSET + 10
    assert trainer.item_end_positions(tokens)[-1] == len(tokens) - 2


# --------------------------------------------------------------------------- #
# the core's item address
# --------------------------------------------------------------------------- #
def test_item_needs_one_write_slot(stateful):
    with pytest.raises(ValueError, match="write_slots"):
        build(stateful, write_slots=2)


def test_item_rejects_a_forced_write(stateful):
    with pytest.raises(ValueError, match="force"):
        build(stateful, write_strength="force")


def test_item_end_turn_needs_a_plan(stateful):
    core = build(stateful)
    state = core.init_state(2)
    with pytest.raises(ValueError, match="items"):
        core.end_turn(state.tensors)


def test_item_write_weights_is_not_one_distribution(stateful):
    core = build(stateful)
    with pytest.raises(ValueError, match="write_weights"):
        core.write_weights(torch.zeros(2, core.hidden), 0)


def test_item_write_lands_at_the_learned_strength(stateful):
    core = build(stateful)
    core.eval()
    states = torch.randn(1, 5, core.hidden)
    state = core.init_state(1)
    with torch.no_grad():
        written = core.end_turn(state.tensors, items=[[(3, 7)]], states=states)
        expected = torch.sigmoid(core.write_gate(states[:, 3])) * core.value_proj(states[:, 3])
    assert torch.allclose(written["v"][:, 7], expected, atol=1e-6)
    assert float(written["v"][:, :7].abs().sum()) == 0.0


def test_item_slots_are_per_row(stateful):
    core = build(stateful)
    states = torch.randn(2, 4, core.hidden)
    written = core.end_turn(
        core.init_state(2).tensors,
        items=[[(1, 0)], [(2, 5)]],
        states=states,
    )
    assert active_slots(written["v"][0]) == [0]
    assert active_slots(written["v"][1]) == [5]


def test_item_write_is_masked_by_the_padding_mask(stateful):
    core = build(stateful)
    states = torch.randn(2, 4, core.hidden)
    valid = torch.tensor([[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 0.0, 0.0]])
    written = core.end_turn(
        core.init_state(2).tensors,
        items=[[(2, 0)], [(2, 1)]],
        states=states,
        valid=valid,
    )
    assert active_slots(written["v"][0]) == [0]
    assert active_slots(written["v"][1]) == []


def test_item_keeps_the_parameter_count(stateful):
    turn = build(stateful, address="turn")
    item = build(stateful, address="item")
    assert turn.parameter_count() == item.parameter_count()
    left, right = turn.state_dict(), item.state_dict()
    assert set(left) == set(right)
    for name in left:
        assert set(left[name]) == set(right[name])
        for key, value in left[name].items():
            assert tuple(value.shape) == tuple(right[name][key].shape)


def test_item_config_records_the_address(stateful):
    assert build(stateful, address="item").config()["address"] == "item"
    assert build(stateful, address="item").config()["write_slots"] == 1


# --------------------------------------------------------------------------- #
# the turn-level slot count (through the trainer's run_session)
# --------------------------------------------------------------------------- #
def test_run_session_writes_three_slots_at_the_roster_boundary(stateful, trainer):
    turns = [[turn_tokens("a"), turn_tokens("x、y")]]
    gaps = [[0.0, 0.0]]

    item = build(stateful, address="item")
    item_snapshots = []
    trainer.run_session(item, turns, gaps, boundaries=item_snapshots)
    assert [len(active_slots(snapshot["v"][0])) for snapshot in item_snapshots] == [1, 3]
    assert active_slots(item_snapshots[-1]["v"][0]) == [0, 1, 2]

    turn = build(stateful, address="turn")
    turn_snapshots = []
    trainer.run_session(turn, turns, gaps, boundaries=turn_snapshots)
    assert [len(active_slots(snapshot["v"][0])) for snapshot in turn_snapshots] == [1, 2]


def test_run_session_keeps_a_counter_per_sample(stateful, trainer):
    core = build(stateful, address="item")
    turns = [
        [turn_tokens("a、b"), turn_tokens("c")],
        [turn_tokens("a"), turn_tokens("c")],
    ]
    gaps = [[0.0, 0.0], [0.0, 0.0]]
    snapshots = []
    trainer.run_session(core, turns, gaps, boundaries=snapshots)
    assert active_slots(snapshots[-1]["v"][0]) == [0, 1, 2]
    assert active_slots(snapshots[-1]["v"][1]) == [0, 1]


# --------------------------------------------------------------------------- #
# the registered arithmetic
# --------------------------------------------------------------------------- #
def reading(exact, null_p=0.002494, chance=0.0005, n=400, overlap=1.0, draws=400):
    """A stored cell; ``ge`` and ``p_value`` are normalised the way ``null_block`` writes them."""
    correct = int(round(exact * n))
    normalised = round(correct / n, 4) if n else 0.0
    ge = max(0, int(round(null_p * (draws + 1))) - 1)
    p_value = round((1 + ge) / (draws + 1), 6)
    return {
        "observed": {
            "n": n,
            "correct": correct,
            "exact": normalised,
            "overlap": overlap,
            "overlap_sum": round(overlap * n, 4),
            "wilson": {"low": 0.0, "high": 1.0},
        },
        "null": {
            "draws": draws,
            "seed": 20261125,
            "exact": {
                "mean": 0.1,
                "sd": 0.02,
                "min": 0.02,
                "max": 0.2,
                "p95": 0.15,
                "p99": 0.18,
            },
            "overlap": {"mean": 0.35, "sd": 0.05, "min": 0.1, "max": 0.6, "p95": 0.45, "p99": 0.5},
            "p_value": p_value,
            "ge": ge,
        },
        "chance": {"exact": chance, "overlap": 0.5},
    }


def arm(
    exact_lro,
    *,
    exact_in=0.9,
    exact_held=0.5,
    unseen=0.2,
    unseen_p=0.002494,
    active_slots=3,
    heldout_p=0.002494,
    overlap=1.0,
    in_sample_p=0.002494,
    landed=200,
    role="treatment",
    address=None,
):
    address = address or ("turn" if role == "control" else "item")
    return {
        "arm": role,
        "k": 2,
        "corpus_seed": 20261127,
        "corpus": {
            "train_digest": "a" * 16,
            "heldout_digest": "b" * 16,
            "digests_match": True,
            "items_per_session": 5,
        },
        "store": {
            "active_slots": {"counts": {str(active_slots): 200}},
            "rank1_residual": {"mean": 0.4},
        },
        "landing": {
            "arm": role,
            "sessions": 200,
            "landed": landed,
            "coverage": round(landed / 200, 6),
            "required_coverage": 0.99,
            "required_cosine": 0.999,
            "min_cosine": 0.9999,
            "failures": [],
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "mode_matches": True,
            "write_mode": {"address": address, "write_strength": "learned", "write_slots": 1},
        },
        "reproduction": {"applicable": False, "equal": False},
        "probe": {"chance": {"exact": 0.0005, "overlap": 0.5}},
        "dimensions": {"names": 12, "colours": 3},
        "split": {"seen": 176, "unseen": 24, "rows": 200},
        "readings": {
            "linear_state": {
                "in_sample": reading(exact_in, in_sample_p),
                "heldout": reading(exact_held, heldout_p),
                "leave_roster_out": reading(exact_lro, 0.002494, overlap=overlap),
                "seen": reading(0.5),
                "unseen": reading(unseen, unseen_p, n=24),
            },
            "linear_values": {
                "in_sample": reading(0.6, in_sample_p),
                "heldout": reading(0.2, heldout_p),
                "leave_roster_out": reading(0.05, 0.002494),
                "seen": reading(0.3),
                "unseen": reading(0.0833, 0.027431, n=24),
            },
            "nonlinear_quad": {
                "in_sample": reading(0.8, in_sample_p),
                "heldout": reading(0.3, heldout_p),
                "leave_roster_out": reading(0.02, 0.002494),
                "seen": reading(0.2),
                "unseen": reading(0.0416, 0.5, n=24),
            },
        },
    }


def graded(probe77, block):
    """Attach the gates, as ``run_arm`` does before anything reads them."""
    block["gates"] = probe77.arm_gates(probe77.load_composition(), block, k=2)
    block["instrument_ok"] = bool(
        block["gates"]["N0_instrument"]["pass"]
        and block["gates"]["M_slots"]["pass"]
        and block["gates"]["M_landed"]["pass"]
    )
    return block


def pair(probe77, control, treatment):
    control["arm"] = "control"
    control["store"]["active_slots"]["counts"] = {"2": 200}
    control["landing"]["arm"] = "control"
    treatment["arm"] = "treatment"
    treatment["store"]["active_slots"]["counts"] = {"3": 200}
    treatment["landing"]["arm"] = "treatment"
    return graded(probe77, control), graded(probe77, treatment)


def test_registered_constants(probe77):
    assert probe77.NULL_DRAWS == 400
    assert probe77.ALPHA == 0.005
    assert probe77.CONTRAST_MARGIN == 0.05
    assert probe77.FIT_COMPARABILITY == 0.15
    assert probe77.UNSEEN_FLOOR == 0.125
    assert probe77.ITEM_SEPARATOR == "、"
    assert probe77.EXPECTED_ITEMS_PER_SESSION == 5
    assert probe77.MECHANISM_MAX == {"control": 3, "treatment": 3}
    assert probe77.MECHANISM_COVERAGE == 0.99
    assert probe77.MECHANISM_COSINE == 0.999
    assert probe77.REGISTERED["control"]["address"] == "turn"
    assert probe77.REGISTERED["treatment"]["address"] == "item"


def test_arm_gates_uses_74s_arithmetic(probe77):
    composition = probe77.load_composition()
    gate = probe77.arm_gates(composition, arm(0.20), k=2)
    assert gate["Q1_relative_fit"]["any"] is True
    assert gate["Q2_transfer"]["any"] is True
    # 0.20 with overlap 1.0 is below the 1.5 floor, so Q3 does not pass
    assert gate["Q3_composed_from_names"]["any"] is False
    assert gate["U_unseen_floor"]["any"] is True
    assert gate["N0_instrument"]["pass"] is True
    assert gate["M_slots"]["pass"] is True
    assert gate["M_landed"]["pass"] is True
    assert gate["N0_instrument"]["corpus_digests_match"] is True


def test_control_mechanism_needs_at_most_three_slots(probe77):
    composition = probe77.load_composition()
    block = arm(0.2, active_slots=2, role="control", address="turn")
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"3": 200}
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"4": 200}
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is False


def test_treatment_mechanism_needs_exactly_three_slots_nearly_always(probe77):
    composition = probe77.load_composition()
    block = arm(0.2, active_slots=3)
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"2": 200}
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is False
    # 197/200 = 0.985 is below the registered 0.99 coverage
    block["store"]["active_slots"]["counts"] = {"3": 197, "2": 3}
    assert probe77.arm_gates(composition, block, k=2)["M_slots"]["pass"] is False


def test_landed_gate_needs_the_registered_coverage(probe77):
    composition = probe77.load_composition()
    block = arm(0.2, landed=200)
    assert probe77.arm_gates(composition, block, k=2)["M_landed"]["pass"] is True
    block["landing"]["landed"] = 197
    block["landing"]["coverage"] = round(197 / 200, 6)
    assert probe77.arm_gates(composition, block, k=2)["M_landed"]["pass"] is False


def test_n0_needs_the_corpus_the_carrier_was_trained_on(probe77):
    composition = probe77.load_composition()
    block = arm(0.2)
    block["corpus"]["digests_match"] = False
    assert probe77.arm_gates(composition, block, k=2)["N0_instrument"]["pass"] is False


def test_n0_needs_the_registered_write_mode(probe77):
    composition = probe77.load_composition()
    block = arm(0.2)
    block["instrument"]["mode_matches"] = False
    assert probe77.arm_gates(composition, block, k=2)["N0_instrument"]["pass"] is False


def test_contrast_needs_the_registered_margin(probe77):
    block = probe77.contrast(arm(0.15, role="control"), arm(0.20))
    assert block["readable"] is True
    assert block["rows"]["linear_state"]["delta"] == pytest.approx(0.05)
    assert block["gain_arms"] == ["linear_state"]


def test_contrast_below_the_margin_is_not_a_gain(probe77):
    block = probe77.contrast(arm(0.15, role="control"), arm(0.19))
    assert block["gain_arms"] == []
    assert block["loss_arms"] == []


def test_contrast_is_unreadable_when_fit_differs(probe77):
    block = probe77.contrast(arm(0.15, exact_in=0.20, role="control"), arm(0.40, exact_in=0.90))
    assert block["readable"] is False
    assert block["rows"]["linear_state"]["fit_comparable"] is False


def test_contrast_loss_arm(probe77):
    block = probe77.contrast(arm(0.40, role="control"), arm(0.10))
    assert block["loss_arms"] == ["linear_state"]
    assert block["gain_arms"] == []


def test_descriptors_record_every_cell(probe77):
    block = probe77.contrast(arm(0.15, role="control"), arm(0.20))
    keys = set(block["descriptors"])
    assert keys == {
        f"{name}.{which}"
        for name in probe77.FAMILIES
        for which in ("in_sample", "heldout", "leave_roster_out")
    }
    assert block["descriptors"]["linear_state.leave_roster_out"] == pytest.approx(0.05)


def test_branch_instrument_first(probe77):
    control, treatment = pair(probe77, arm(0.2), arm(0.2))
    treatment["instrument"]["carrier_unchanged"] = False
    treatment = graded(probe77, treatment)
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "N0-instrument"


def test_branch_landing_failure_is_instrument(probe77):
    control, treatment = pair(probe77, arm(0.2), arm(0.2, landed=190))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "N0-instrument"
    assert treatment["gates"]["M_landed"]["pass"] is False


def test_branch_treatment_without_fit(probe77):
    control, treatment = pair(probe77, arm(0.2), arm(0.2, in_sample_p=0.5))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P3-treatment-no-fit"
    assert "more epochs" in fork["next"]


def test_branch_gain_without_the_floor(probe77):
    control, treatment = pair(
        probe77,
        arm(0.10, role="control"),
        arm(0.20, unseen=0.0416, unseen_p=0.5),
    )
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P4-partial-gain-from-item-content"


def test_branch_gain_with_floor_and_unseen_is_the_item_limit(probe77):
    control, treatment = pair(probe77, arm(0.10, role="control"), arm(0.20, overlap=1.6))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P1-item-content-was-the-limit"


def test_branch_loss(probe77):
    control, treatment = pair(probe77, arm(0.30, role="control"), arm(0.10))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P5-item-content-hurt"


def test_branch_flat(probe77):
    control, treatment = pair(probe77, arm(0.10, role="control"), arm(0.11))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P2-both-width-and-content-were-not-the-limit"


def test_branch_no_transfer(probe77):
    control, treatment = pair(probe77, arm(0.10, role="control"), arm(0.10, heldout_p=0.5))
    fork = probe77.branch(control, treatment, probe77.contrast(control, treatment))
    assert fork["id"] == "P6-treatment-no-transfer"


# --------------------------------------------------------------------------- #
# check()
# --------------------------------------------------------------------------- #
def report(probe77, control, treatment):
    block = probe77.contrast(control, treatment)
    return {
        "stage": probe77.STAGE,
        "probe": {
            "null_draws": probe77.NULL_DRAWS,
            "null_seed": probe77.NULL_SEED,
            "alpha": probe77.ALPHA,
            "contrast_margin": probe77.CONTRAST_MARGIN,
            "item_separator": probe77.ITEM_SEPARATOR,
            "expected_items_per_session": probe77.EXPECTED_ITEMS_PER_SESSION,
            "mechanism_coverage": probe77.MECHANISM_COVERAGE,
            "mechanism_cosine": probe77.MECHANISM_COSINE,
            "composition_floor": {
                "overlap_fraction": probe77.COMPOSED_OVERLAP_FRACTION,
                "overlap": round(probe77.COMPOSED_OVERLAP_FRACTION * 2, 4),
            },
        },
        "arms": {"control": control, "treatment": treatment},
        "contrast": block,
        "branch": probe77.branch(control, treatment, block),
    }


def consistent(probe77):
    return pair(
        probe77,
        arm(0.10, role="control"),
        arm(0.20, unseen=0.0416, unseen_p=0.5),
    )


def test_check_accepts_a_consistent_report(probe77, tmp_path):
    control, treatment = consistent(probe77)
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(report(probe77, control, treatment)), encoding="utf-8")
    assert probe77.check(path) == []


def test_check_rejects_a_stale_branch(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["branch"] = {"id": "P1-item-content-was-the-limit", "reading": "", "next": ""}
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("branch is stale" in problem for problem in problems)


def test_check_rejects_a_broken_p_value(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["arms"]["control"]["readings"]["linear_state"]["heldout"]["null"]["p_value"] = 0.9
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("p_value does not follow" in problem for problem in problems)


def test_check_rejects_a_tampered_mechanism(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["arms"]["treatment"]["gates"]["M_slots"]["pass"] = False
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("does not re-derive" in problem for problem in problems)


def test_check_rejects_a_different_stage(probe77, tmp_path):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps({"stage": "§76"}), encoding="utf-8")
    assert probe77.check(path) == ["this is not a §77 report"]


def test_check_rejects_a_short_null(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["probe"]["null_draws"] = 200
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("null_draws" in problem for problem in problems)


def test_check_rejects_an_address_mismatch(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["arms"]["treatment"]["instrument"]["write_mode"]["address"] = "turn"
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("address is" in problem for problem in problems)


def test_check_rejects_a_different_item_separator(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["probe"]["item_separator"] = ","
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("item separator" in problem for problem in problems)


def test_check_rejects_a_different_corpus_digest(probe77, tmp_path):
    control, treatment = consistent(probe77)
    data = report(probe77, control, treatment)
    data["arms"]["treatment"]["corpus"]["digests_match"] = False
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe77.check(path)
    assert any("different corpus" in problem for problem in problems)


def test_slot_median_is_the_median_active_slot_count(probe77):
    assert probe77.slot_median({"active_slots": {"counts": {"3": 200}}}) == 3.0
    assert probe77.slot_median({"active_slots": {"counts": {"2": 100, "4": 100}}}) == 3.0
    assert probe77.slot_median({"active_slots": {"counts": {}}}) == 0.0


def test_exact_fraction_counts_the_registered_value(probe77):
    store = {"active_slots": {"counts": {"3": 197, "2": 3}}}
    assert probe77.exact_fraction(store, 3) == pytest.approx(0.985)
