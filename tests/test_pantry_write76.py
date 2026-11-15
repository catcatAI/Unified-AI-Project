# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§76 contract tests: the per-turn write width and the A/B verdict arithmetic.

Two things are tested here and neither needs a fitted carrier:

* the core's ``write_slots`` switch - parameter parity, strict checkpoint
  loading, the chunk partition (``n`` sub-writes per turn, zeros outside each
  chunk's block, chunks summing to the one-slot value), the rejected
  combinations, and the one-slot contract still being bit-identical to §73;
* the probe's registered arithmetic - the mechanism gate (2 vs 8 active slots),
  the contrast margin and fit comparability, the branch's fixed precedence, and
  ``check()``'s refusal of a tampered report.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WRITE76 = REPO_ROOT / "scripts" / "probe_pantry_write76.py"
STATEFUL = REPO_ROOT / "apps" / "backend" / "src" / "ai" / "core" / "stateful_decoder.py"

torch = pytest.importorskip("torch")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe76():
    return _load_module("pantry_write76_under_test", WRITE76)


@pytest.fixture(scope="module")
def stateful():
    return _load_module("stateful_decoder_under_test", STATEFUL)


# --------------------------------------------------------------------------- #
# the write width
# --------------------------------------------------------------------------- #
def build(stateful, *, write_slots=1, address="turn", write_strength="learned", **overrides):
    kwargs = dict(
        token_count=64,
        hidden=32,
        emb=16,
        slots=16,
        slot_dim=32,
        value_dim=64,
        chunk_seconds=1.0,
        device="cpu",
        address=address,
        write_strength=write_strength,
        write_slots=write_slots,
    )
    kwargs.update(overrides)
    return stateful.TurnStoreCore(**kwargs)


def store_of(core, batch=2, seed=3):
    generator = torch.Generator().manual_seed(seed)
    hidden = torch.randn(batch, core.hidden, generator=generator)
    state = core.init_state(batch)
    state.tensors["h"] = hidden.clone()
    return hidden, state.tensors


def test_write_slots_keeps_the_parameter_count(stateful):
    one = build(stateful, write_slots=1)
    four = build(stateful, write_slots=4)
    assert one.parameter_count() == four.parameter_count()
    assert set(one.state_dict()) == set(four.state_dict())


def test_config_records_the_width(stateful):
    assert build(stateful, write_slots=1).config()["write_slots"] == 1
    assert build(stateful, write_slots=4).config()["write_slots"] == 4


def test_multi_slot_needs_the_turn_address(stateful):
    with pytest.raises(ValueError, match="write_slots"):
        build(stateful, write_slots=4, address="gate")


def test_slots_must_divide_the_store(stateful):
    with pytest.raises(ValueError, match="slots"):
        build(stateful, write_slots=3)
    with pytest.raises(ValueError, match="slot_dim"):
        build(stateful, write_slots=8, slot_dim=12)
    with pytest.raises(ValueError, match="value_dim"):
        build(stateful, write_slots=8, value_dim=12)


def test_zero_width_is_rejected(stateful):
    with pytest.raises(ValueError, match="write_slots"):
        build(stateful, write_slots=0)


def test_strict_load_rejects_a_width_mismatch(stateful, tmp_path):
    four = build(stateful, write_slots=4)
    path = tmp_path / "four.pt"
    four.save_weights(str(path))
    one = build(stateful, write_slots=1)
    with pytest.raises(Exception, match="write_slots"):
        one.load_weights(str(path), strict_config=True)
    four.load_weights(str(path), strict_config=True)


def test_turn_index_picks_the_block(stateful):
    core = build(stateful, write_slots=4)
    for turn in range(4):
        _, tensors = store_of(core, seed=5 + turn)
        written = core.end_turn(tensors, address=turn)
        norms = written["v"][0].norm(dim=-1)
        active = [i for i in range(core.slots) if float(norms[i]) > 0.0]
        assert active == [turn * 4 + j for j in range(4)]


def test_chunk_blocks_are_disjoint(stateful):
    one = build(stateful, write_slots=1)
    four = build(stateful, write_slots=4)
    four.load_state_dict(one.state_dict())
    _, tensors = store_of(four)
    written = four.end_turn(tensors, address=1)
    width_v = four.value_dim // 4
    for slot in range(4, 8):
        block = slot - 4
        for chunk in range(4):
            part = written["v"][0, slot, chunk * width_v : (chunk + 1) * width_v]
            if chunk == block:
                assert float(part.abs().sum()) >= 0.0
            else:
                assert float(part.abs().sum()) == 0.0


def test_chunks_sum_to_the_one_slot_value(stateful):
    """The content invariant: the treatment writes the same numbers, split up."""
    one = build(stateful, write_slots=1)
    four = build(stateful, write_slots=4)
    four.load_state_dict(one.state_dict())
    hidden, tensors = store_of(one, seed=11)
    control = one.end_turn(tensors, address=2)
    _, tensors = store_of(four, seed=11)
    treatment = four.end_turn(tensors, address=2)
    assert torch.allclose(treatment["v"][0].sum(dim=0), control["v"][0, 2], atol=1e-6)
    assert torch.allclose(treatment["k"][0].sum(dim=0), control["k"][0, 2], atol=1e-6)


def test_one_slot_is_bit_identical(stateful):
    """§73's arm must not move: the same write, the same numbers."""
    core = build(stateful, write_slots=1)
    hidden, tensors = store_of(core, seed=13)
    written = core.end_turn(tensors, address=3)
    expected = core.value_proj(hidden) * torch.sigmoid(core.write_gate(hidden))
    assert torch.allclose(written["v"][:, 3], expected, atol=1e-6)
    assert torch.equal(written["v"][:, 3], expected)


def test_write_weights_is_the_one_slot_contract(stateful):
    one = build(stateful, write_slots=1)
    hidden, _ = store_of(one)
    weights = one.write_weights(hidden, 0)
    assert tuple(weights.shape) == (2, one.slots)
    assert weights.sum(dim=1).tolist() == pytest.approx([1.0, 1.0])
    four = build(stateful, write_slots=4)
    with pytest.raises(ValueError, match="write_weights"):
        four.write_weights(hidden, 0)


def test_force_is_still_a_documented_dead_end(stateful):
    """The dropped §76 candidate: kept in the core, not an arm."""
    core = build(stateful, write_slots=1, write_strength="force")
    hidden, tensors = store_of(core)
    written = core.end_turn(tensors, address=0)
    assert torch.allclose(written["v"][:, 0], core.value_proj(hidden), atol=1e-6)


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
    active_slots=8,
    heldout_p=0.002494,
    overlap=1.0,
    in_sample_p=0.002494,
    role="treatment",
):
    return {
        "arm": role,
        "k": 2,
        "corpus_seed": 20261127,
        "corpus": {"train_digest": "a" * 16, "heldout_digest": "b" * 16},
        "store": {
            "active_slots": {"counts": {str(active_slots): 200}},
            "rank1_residual": {"mean": 0.4},
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "write_mode": {"address": "turn", "write_strength": "learned", "write_slots": 4},
        },
        "probe": {"chance": {"exact": 0.0005, "overlap": 0.5}},
        "reproduction": {"applicable": False, "equal": False},
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


def graded(probe76, block):
    """Attach the gates, as ``run_arm`` does before anything reads them."""
    block["gates"] = probe76.arm_gates(probe76.load_composition(), block, k=2)
    block["instrument_ok"] = bool(
        block["gates"]["N0_instrument"]["pass"] and block["gates"]["W_mechanism"]["pass"]
    )
    return block


def pair(probe76, control, treatment):
    control["arm"] = "control"
    control["instrument"]["write_mode"]["write_slots"] = 1
    control["store"]["active_slots"]["counts"] = {"2": 200}
    treatment["arm"] = "treatment"
    treatment["instrument"]["write_mode"]["write_slots"] = 4
    return graded(probe76, control), graded(probe76, treatment)


def test_registered_constants(probe76):
    assert probe76.NULL_DRAWS == 400
    assert probe76.ALPHA == 0.005
    assert probe76.CONTRAST_MARGIN == 0.05
    assert probe76.FIT_COMPARABILITY == 0.15
    assert probe76.UNSEEN_FLOOR == 0.125
    assert probe76.SLOTS_PER_TURN == {"control": 1, "treatment": 4}
    assert probe76.MECHANISM_MAX == {"control": 3, "treatment": 8}


def test_arm_gates_uses_74s_arithmetic(probe76):
    composition = probe76.load_composition()
    gate = probe76.arm_gates(composition, arm(0.20), k=2)
    assert gate["Q1_relative_fit"]["any"] is True
    assert gate["Q2_transfer"]["any"] is True
    # 0.20 with overlap 1.0 is below the 1.5 floor, so Q3 does not pass
    assert gate["Q3_composed_from_names"]["any"] is False
    assert gate["S1_seen"]["any"] is True
    assert gate["S2_unseen"]["any"] is True
    assert gate["U_unseen_floor"]["any"] is True
    assert gate["W_mechanism"]["pass"] is True
    assert gate["N0_instrument"]["pass"] is True
    assert gate["N0_instrument"]["reproduction_applicable"] is False


def test_control_mechanism_needs_at_most_three_slots(probe76):
    composition = probe76.load_composition()
    block = arm(0.2, active_slots=2, role="control")
    assert probe76.arm_gates(composition, block, k=2)["W_mechanism"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"3": 200}
    assert probe76.arm_gates(composition, block, k=2)["W_mechanism"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"6": 200}
    assert probe76.arm_gates(composition, block, k=2)["W_mechanism"]["pass"] is False


def test_treatment_mechanism_needs_eight_slots(probe76):
    composition = probe76.load_composition()
    block = arm(0.2, active_slots=8)
    assert probe76.arm_gates(composition, block, k=2)["W_mechanism"]["pass"] is True
    block["store"]["active_slots"]["counts"] = {"7": 200}
    assert probe76.arm_gates(composition, block, k=2)["W_mechanism"]["pass"] is False


def test_contrast_needs_the_registered_margin(probe76):
    block = probe76.contrast(arm(0.15, exact_in=0.90), arm(0.20, exact_in=0.90))
    assert block["readable"] is True
    assert block["rows"]["linear_state"]["delta"] == pytest.approx(0.05)
    assert block["gain_arms"] == ["linear_state"]


def test_contrast_below_the_margin_is_not_a_gain(probe76):
    block = probe76.contrast(arm(0.15, exact_in=0.90), arm(0.19, exact_in=0.90))
    assert block["gain_arms"] == []
    assert block["loss_arms"] == []


def test_contrast_is_unreadable_when_fit_differs(probe76):
    block = probe76.contrast(arm(0.15, exact_in=0.20), arm(0.40, exact_in=0.90))
    assert block["readable"] is False
    assert block["rows"]["linear_state"]["fit_comparable"] is False


def test_contrast_loss_arm(probe76):
    block = probe76.contrast(arm(0.40, exact_in=0.90), arm(0.10, exact_in=0.90))
    assert block["loss_arms"] == ["linear_state"]
    assert block["gain_arms"] == []


def test_descriptors_record_every_cell(probe76):
    block = probe76.contrast(arm(0.15, exact_in=0.90), arm(0.20, exact_in=0.90))
    keys = set(block["descriptors"])
    assert keys == {
        f"{name}.{which}"
        for name in probe76.FAMILIES
        for which in ("in_sample", "heldout", "leave_roster_out")
    }
    assert block["descriptors"]["linear_state.leave_roster_out"] == pytest.approx(0.05)


def test_branch_instrument_first(probe76):
    control, treatment = pair(probe76, arm(0.2), arm(0.2))
    treatment["instrument"]["carrier_unchanged"] = False
    treatment = graded(probe76, treatment)
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "N0-instrument"


def test_branch_mechanism_failure_is_instrument(probe76):
    control, treatment = pair(probe76, arm(0.2, active_slots=2), arm(0.2, active_slots=2))
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "N0-instrument"
    assert treatment["gates"]["W_mechanism"]["pass"] is False


def test_branch_treatment_without_fit(probe76):
    control, treatment = pair(probe76, arm(0.2), arm(0.2, in_sample_p=0.5))
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W3-treatment-no-fit"
    assert "more epochs" in fork["next"]


def test_branch_gain_without_the_floor(probe76):
    control, treatment = pair(
        probe76, arm(0.10, exact_in=0.90), arm(0.20, exact_in=0.90, unseen=0.0416, unseen_p=0.5)
    )
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W4-partial-gain-from-resolution"


def test_branch_gain_with_floor_and_unseen_is_the_write_limit(probe76):
    control, treatment = pair(
        probe76, arm(0.10, exact_in=0.90), arm(0.20, exact_in=0.90, overlap=1.6)
    )
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W1-the-write-resolution-was-the-limit"


def test_branch_loss(probe76):
    control, treatment = pair(probe76, arm(0.30, exact_in=0.90), arm(0.10, exact_in=0.90))
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W5-resolution-hurt"


def test_branch_flat(probe76):
    control, treatment = pair(probe76, arm(0.10, exact_in=0.90), arm(0.11, exact_in=0.90))
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W2-the-write-was-not-the-limit"


def test_branch_no_transfer(probe76):
    control, treatment = pair(
        probe76, arm(0.10, exact_in=0.90), arm(0.10, exact_in=0.90, heldout_p=0.5)
    )
    fork = probe76.branch(control, treatment, probe76.contrast(control, treatment))
    assert fork["id"] == "W6-treatment-no-transfer"


# --------------------------------------------------------------------------- #
# check()
# --------------------------------------------------------------------------- #
def report(probe76, control, treatment):
    block = probe76.contrast(control, treatment)
    return {
        "stage": probe76.STAGE,
        "probe": {
            "null_draws": probe76.NULL_DRAWS,
            "null_seed": probe76.NULL_SEED,
            "alpha": probe76.ALPHA,
            "contrast_margin": probe76.CONTRAST_MARGIN,
            "composition_floor": {
                "overlap_fraction": probe76.COMPOSED_OVERLAP_FRACTION,
                "overlap": round(probe76.COMPOSED_OVERLAP_FRACTION * 2, 4),
            },
        },
        "arms": {"control": control, "treatment": treatment},
        "contrast": block,
        "branch": probe76.branch(control, treatment, block),
    }


def consistent(probe76):
    control, treatment = pair(
        probe76, arm(0.10, exact_in=0.90), arm(0.20, exact_in=0.90, unseen=0.0416, unseen_p=0.5)
    )
    return control, treatment


def test_check_accepts_a_consistent_report(probe76, tmp_path):
    control, treatment = consistent(probe76)
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(report(probe76, control, treatment)), encoding="utf-8")
    assert probe76.check(path) == []


def test_check_rejects_a_stale_branch(probe76, tmp_path):
    control, treatment = consistent(probe76)
    data = report(probe76, control, treatment)
    data["branch"] = {"id": "W1-the-write-resolution-was-the-limit", "reading": "", "next": ""}
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe76.check(path)
    assert any("branch is stale" in problem for problem in problems)


def test_check_rejects_a_broken_p_value(probe76, tmp_path):
    control, treatment = consistent(probe76)
    data = report(probe76, control, treatment)
    data["arms"]["control"]["readings"]["linear_state"]["heldout"]["null"]["p_value"] = 0.9
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe76.check(path)
    assert any("p_value does not follow" in problem for problem in problems)


def test_check_rejects_a_tampered_mechanism(probe76, tmp_path):
    control, treatment = consistent(probe76)
    data = report(probe76, control, treatment)
    data["arms"]["treatment"]["gates"]["W_mechanism"]["pass"] = False
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe76.check(path)
    assert any("does not re-derive" in problem for problem in problems)


def test_check_rejects_a_different_stage(probe76, tmp_path):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps({"stage": "§75"}), encoding="utf-8")
    assert probe76.check(path) == ["this is not a §76 report"]


def test_check_rejects_a_short_null(probe76, tmp_path):
    control, treatment = consistent(probe76)
    data = report(probe76, control, treatment)
    data["probe"]["null_draws"] = 200
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe76.check(path)
    assert any("null_draws" in problem for problem in problems)


def test_check_rejects_a_write_slots_mismatch(probe76, tmp_path):
    control, treatment = consistent(probe76)
    data = report(probe76, control, treatment)
    data["arms"]["treatment"]["instrument"]["write_mode"]["write_slots"] = 1
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe76.check(path)
    assert any("write_slots" in problem for problem in problems)


def test_slot_median_is_the_median_active_slot_count(probe76):
    assert probe76.slot_median({"active_slots": {"counts": {"2": 200}}}) == 2.0
    assert probe76.slot_median({"active_slots": {"counts": {"2": 100, "8": 100}}}) == 5.0
    assert probe76.slot_median({"active_slots": {"counts": {}}}) == 0.0
