# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for §72's write-side probe.

These pin the parts that must not drift silently: the recomputed write gate is
the exact one ``end_turn`` uses, a one-slot store reads as rank 1, the address
row is the softmax weights and not something else, the four arms are the
registered four, the gates use the registered floors, the branch precedence is
fixed, and a stored verdict re-derives from its own numbers. No carrier, corpus
or checkpoint is loaded, and nothing is trained: every tensor here is synthetic.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "probe_pantry_slots.py"


def _load():
    spec = importlib.util.spec_from_file_location("probe_pantry_slots", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_slots"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


class FakeCore(torch.nn.Module):
    """Only the attributes ``slot_block`` and ``write_weights`` touch."""

    def __init__(self, hidden: int = 6, slots: int = 4, slot_dim: int = 5) -> None:
        super().__init__()
        self.hidden = hidden
        self.slots = slots
        self.slot_dim = slot_dim
        self.value_dim = slot_dim
        self.log_write_scale = torch.nn.Parameter(torch.zeros(1))
        self.slot_gate = torch.nn.Linear(hidden, slots)


def _views(
    core: FakeCore,
    hidden: torch.Tensor,
    weights: torch.Tensor,
    read: torch.Tensor,
    *,
    values_from: torch.Tensor = None,
) -> dict:
    """``values`` built the way ``end_turn`` builds them: one share per slot."""
    rows = read if values_from is None else values_from
    values = weights.unsqueeze(-1) * rows.unsqueeze(1)
    state = torch.cat([hidden, read], dim=1)
    return {"values": values.reshape(len(hidden), -1), "state": state, "read": read}


def _one_hot_setup(core: FakeCore, count: int = 4, *, index: int = 0) -> dict:
    """Every row writes slot ``index`` with a different 1-D value direction."""
    with torch.no_grad():
        core.slot_gate.weight.zero_()
        core.slot_gate.bias.zero_()
        core.slot_gate.bias[index] = 40.0
        core.log_write_scale.fill_(0.0)
    hidden = torch.randn(count, core.hidden)
    weights = probe_weights(core, hidden)
    read = torch.randn(count, core.slot_dim)
    return {"hidden": hidden, "weights": weights, "read": read}


def probe_weights(core: FakeCore, hidden: torch.Tensor) -> torch.Tensor:
    with torch.no_grad():
        return torch.softmax(torch.exp(core.log_write_scale) * core.slot_gate(hidden), dim=-1)


# --------------------------------------------------------------------------- #
# the write
# --------------------------------------------------------------------------- #
def test_write_weights_are_a_distribution(probe):
    core = FakeCore()
    hidden = torch.randn(5, core.hidden)
    weights = probe.write_weights(torch, core, hidden)
    assert weights.shape == (5, core.slots)
    assert torch.all(weights > 0)
    assert torch.allclose(weights.sum(dim=1), torch.ones(5), atol=1e-6)


def test_write_weights_are_the_end_turn_gate(probe):
    # end_turn: softmax(exp(log_write_scale) * slot_gate(h)). The probe must
    # recompute exactly that, not an approximation of it.
    core = FakeCore()
    with torch.no_grad():
        core.log_write_scale.fill_(0.7)
    hidden = torch.randn(3, core.hidden)
    expected = torch.softmax(torch.exp(core.log_write_scale) * core.slot_gate(hidden), dim=-1)
    assert torch.allclose(probe.write_weights(torch, core, hidden), expected, atol=0.0)


def test_a_concentrated_gate_reads_as_one_address(probe):
    core = FakeCore()
    setup = _one_hot_setup(core)
    block = probe.slot_block(
        torch, core, _views(core, setup["hidden"], setup["weights"], setup["read"])
    )
    assert float(block["max_share"].min()) > 0.999
    assert float((block["effective_slots"] - 1.0).abs().max()) < 1e-3


def test_a_flat_gate_does_not_read_as_one_address(probe):
    core = FakeCore()
    with torch.no_grad():
        core.slot_gate.weight.zero_()
        core.slot_gate.bias.zero_()
    hidden = torch.randn(4, core.hidden)
    weights = probe.write_weights(torch, core, hidden)
    block = probe.slot_block(
        torch, core, _views(core, hidden, weights, torch.randn(4, core.slot_dim))
    )
    assert float(block["max_share"].max()) < 0.5
    assert float(block["effective_slots"].min()) > 3.5


# --------------------------------------------------------------------------- #
# the store
# --------------------------------------------------------------------------- #
def test_a_one_slot_store_is_exactly_rank_one(probe):
    core = FakeCore()
    setup = _one_hot_setup(core)
    block = probe.slot_block(
        torch, core, _views(core, setup["hidden"], setup["weights"], setup["read"])
    )
    assert float(block["rank1_residual"].max()) < 1e-6
    assert [int(value) for value in block["active_slots"].tolist()] == [1] * 4


def test_active_slots_respect_the_share_floor(probe):
    core = FakeCore(hidden=4, slots=4, slot_dim=2)
    hidden = torch.zeros(2, 4)
    weights = torch.full((2, 4), 0.25)
    read = torch.zeros(2, 2)
    views = _views(core, hidden, weights, read)
    values = views["values"].reshape(2, 4, 2).clone()
    values[:, 0] = torch.tensor([1.0, 0.0])
    values[:, 1] = torch.tensor([0.5, 0.0])
    values[:, 2] = torch.tensor([1e-9, 0.0])
    views["values"] = values.reshape(2, -1)
    block = probe.slot_block(torch, core, views)
    # floor is ACTIVE_SLOT_SHARE * the strongest norm = 1e-3, so 0.5 counts and
    # 1e-9 does not.
    assert [int(value) for value in block["active_slots"].tolist()] == [2, 2]

    values[:, 1] = torch.tensor([1e-9, 0.0])
    views["values"] = values.reshape(2, -1)
    block = probe.slot_block(torch, core, views)
    assert [int(value) for value in block["active_slots"].tolist()] == [1, 1]


def test_read_alignment_is_one_when_read_is_the_written_value(probe):
    core = FakeCore()
    setup = _one_hot_setup(core)
    block = probe.slot_block(
        torch, core, _views(core, setup["hidden"], setup["weights"], setup["read"])
    )
    assert float(block["read_cos"].min()) > 0.99999

    # Same store, different pooled read: the read no longer *is* the write.
    other = setup["read"] + torch.randn_like(setup["read"])
    block = probe.slot_block(
        torch,
        core,
        _views(core, setup["hidden"], setup["weights"], other, values_from=setup["read"]),
    )
    assert float(block["read_cos"].min()) < 0.999


def test_the_address_row_is_the_softmax_weights(probe):
    core = FakeCore()
    setup = _one_hot_setup(core)
    block = probe.slot_block(
        torch, core, _views(core, setup["hidden"], setup["weights"], setup["read"])
    )
    weights = block["weights"]
    # unit address rows reproduce the weights exactly; the stored row carries the
    # amplitude of the strongest singular value of the value matrix.
    unit = torch.nn.functional.normalize(block["address"], dim=1).double()
    assert torch.allclose(unit, weights.double(), atol=1e-8)


def test_a_constant_address_is_rank_one_across_sessions(probe):
    core = FakeCore(hidden=4, slots=4, slot_dim=2)
    hidden = torch.zeros(6, 4)  # identical hidden => identical gate => identical address
    weights = probe_weights(core, hidden)
    read = torch.randn(6, 2)
    block = probe.slot_block(torch, core, _views(core, hidden, weights, read))
    assert float(block["address_rank1_residual"]) < 1e-9


def test_summarise_reports_fractions_between_zero_and_one(probe):
    core = FakeCore()
    setup = _one_hot_setup(core)
    block = probe.slot_block(
        torch, core, _views(core, setup["hidden"], setup["weights"], setup["read"])
    )
    summary = probe.summarise(torch, block)
    assert summary["sessions"] == 4
    for key in (
        "one_address_fraction",
        "single_slot_fraction",
        "rank1_fraction",
        "read_is_write_fraction",
    ):
        assert 0.0 <= summary[key] <= 1.0
    assert summary["one_address_fraction"] == 1.0
    assert summary["single_slot_fraction"] == 1.0
    assert summary["rank1_fraction"] == 1.0
    assert summary["read_is_write_fraction"] == 1.0
    assert summary["active_slots"]["counts"] == {"1": 4}


# --------------------------------------------------------------------------- #
# the arms
# --------------------------------------------------------------------------- #
def test_the_arms_are_the_registered_four(probe):
    assert probe.ARMS == ("values", "read", "state", "address")


def test_feature_matrix_names_each_registered_view(probe):
    views = {
        "values": torch.zeros(2, 8),
        "state": torch.zeros(2, 6),
        "read": torch.zeros(2, 3),
    }
    block = {"address": torch.zeros(2, 4)}
    assert probe.feature_matrix(views, "values", block) is views["values"]
    assert probe.feature_matrix(views, "state", block) is views["state"]
    assert probe.feature_matrix(views, "read", block) is views["read"]
    assert probe.feature_matrix(views, "address", block) is block["address"]
    with pytest.raises(SystemExit):
        probe.feature_matrix(views, "quad", block)


def test_arm_hands_the_fold_structures_to_cross_validate(probe):
    # cross_validate's fourth positional argument is the fold key list; passing
    # None there fails at run time, so the call is pinned rather than assumed.
    seen = {}

    class FakeBoundaries:
        PROBE_SEED = 11
        FOLDS = 3

        def run_probe(self, *args, **kwargs):
            seen["run_probe"] = (args, kwargs)
            return {"in_sample": {"exact": 0.4}, "heldout": {"exact": 0.1}}

        def capacity_ceiling(self, *args, **kwargs):
            seen["capacity_ceiling"] = (args, kwargs)
            return {"exact": 0.2}

        def cross_validate(self, *args, **kwargs):
            seen["cross_validate"] = (args, kwargs)
            return {"exact": 0.3}

    structure = ["s0", "s0", "s1"]
    result = probe.arm(
        FakeBoundaries(),
        torch,
        torch.zeros(3, 4),
        torch.zeros(3, 4),
        torch.zeros(3, 6),
        torch.zeros(3, 6),
        structure,
        names=6,
        slots=2,
    )
    assert seen["cross_validate"][0][3] is structure
    assert seen["cross_validate"][1]["folds"] == 3
    assert seen["run_probe"][1]["slots"] == 2
    assert seen["capacity_ceiling"][1]["out"] == 6
    assert result == {
        "in_sample": {"exact": 0.4},
        "heldout": {"exact": 0.1},
        "capacity": {"exact": 0.2},
        "in_distribution": {"exact": 0.3},
    }


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def _arm(exact: float, *, capacity: float = 0.2, in_sample: float = 0.4) -> dict:
    return {
        "in_sample": {"exact": in_sample, "correct": int(in_sample * 200), "n": 200},
        "heldout": {"exact": exact, "correct": int(exact * 200), "n": 200},
        "capacity": {"exact": capacity, "correct": int(capacity * 200), "n": 200},
        "in_distribution": {"exact": 0.5},
    }


def _report(probe, **overrides) -> dict:
    ok = 1.0
    mechanism = {
        "sessions": 200,
        "max_share": {"mean": 1.0, "min": 1.0, "max": 1.0},
        "effective_slots": {"mean": 1.0, "min": 1.0, "max": 1.0},
        "active_slots": {"mean": 1.0, "min": 1.0, "max": 1.0, "counts": {"1": 200}},
        "rank1_residual": {"mean": 1e-7, "min": 0.0, "max": 1e-6},
        "read_cos": {"mean": ok, "min": ok, "max": ok},
        "one_address_fraction": ok,
        "single_slot_fraction": ok,
        "rank1_fraction": ok,
        "read_is_write_fraction": ok,
        "address_rank1_residual": 0.0,
    }
    report = {
        "k": 2,
        "mechanism": {"train": dict(mechanism), "heldout": dict(mechanism)},
        "arms": {
            "values": _arm(0.14),
            "read": _arm(0.13),
            "state": _arm(0.12),
            "address": _arm(0.02),
        },
        "instrument": {
            "carrier_unchanged": True,
            "checkpoint_unchanged": True,
            "determinism_ok": True,
            "determinism_min_cosine": 1.0,
            "features_finite": True,
            "seconds": 1.0,
        },
    }
    report.update(overrides)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = bool(report["gates"]["S0_instrument"]["pass"])
    return report


def test_the_registered_report_passes_every_gate(probe):
    report = _report(probe)
    assert all(block["pass"] for block in report["gates"].values())
    assert report["branch"]["id"] == "S1-single-address-temporal-superposition"


def test_gates_use_the_registered_floors(probe):
    assert probe.READABLE_FLOOR == 0.95
    assert probe.TRANSFER_FLOOR == 0.50
    assert probe.CAPACITY_MAX == 0.50
    assert probe.ADDRESS_TRANSFER_MAX == 0.10
    assert probe.ONE_ADDRESS_FLOOR == 0.95
    assert probe.RANK1_EPS == 1e-3
    assert probe.FRACTION_FLOOR == 0.95
    assert probe.READ_COS_FLOOR == 0.999
    assert probe.ACTIVE_SLOT_SHARE == 1e-3


def test_a_distributed_address_breaks_the_one_address_gate(probe):
    report = _report(probe)
    report["mechanism"]["heldout"]["one_address_fraction"] = 0.50
    gate = probe.gates(report)
    assert gate["S1_one_address"]["pass"] is False
    assert probe.branch(gate)["id"] == "S4-slots-are-distributed"


def test_a_multi_slot_store_breaks_the_rank_one_gate(probe):
    report = _report(probe)
    report["mechanism"]["heldout"]["single_slot_fraction"] = 0.80
    gate = probe.gates(report)
    assert gate["S2_single_slot_store"]["pass"] is False
    assert probe.branch(gate)["id"] == "S4-two-addresses"


def test_a_read_that_is_not_the_write_takes_its_own_branch(probe):
    report = _report(probe)
    report["mechanism"]["heldout"]["read_is_write_fraction"] = 0.60
    gate = probe.gates(report)
    assert gate["S3_read_is_the_write"]["pass"] is False
    assert probe.branch(gate)["id"] == "S2-read-is-not-the-write"


def test_an_address_that_names_the_roster_takes_its_own_branch(probe):
    report = _report(probe)
    report["arms"]["address"] = _arm(0.35)
    gate = probe.gates(report)
    assert gate["S4_address_carries_no_roster"]["pass"] is False
    assert probe.branch(gate)["id"] == "S3-address-codes-the-roster"


def test_a_readable_store_fails_the_store_gate(probe):
    report = _report(probe)
    report["arms"]["values"] = _arm(0.60)
    gate = probe.gates(report)
    assert gate["S5_store_is_not_readable"]["pass"] is False


def test_capacity_above_the_ceiling_blocks_the_transfer(probe):
    # A held-out number means nothing when permuted labels score as high.
    report = _report(probe)
    report["arms"]["values"] = _arm(0.60, capacity=0.55)
    gate = probe.gates(report)
    assert gate["S5_store_is_not_readable"]["pass"] is True


def test_a_moved_carrier_fails_the_instrument(probe):
    report = _report(probe)
    report["instrument"]["carrier_unchanged"] = False
    gate = probe.gates(report)
    assert gate["S0_instrument"]["pass"] is False
    assert probe.branch(gate)["id"] == "S0-instrument"


def test_branch_takes_the_first_matching_reading(probe):
    # precedence: S0 > S1 > S2 > S3 > S4 > S1-pass
    report = _report(probe)
    report["instrument"]["determinism_ok"] = False
    gate = probe.gates(report)
    assert probe.branch(gate)["id"] == "S0-instrument"


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def test_check_accepts_a_well_formed_verdict(probe, tmp_path):
    report = _report(probe)
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert probe.check(path) == []


def test_check_rejects_a_stale_gate(probe, tmp_path):
    report = _report(probe)
    report["gates"]["S1_one_address"]["pass"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("S1_one_address.pass is stale" in item for item in problems)


def test_check_rejects_a_stale_branch(probe, tmp_path):
    report = _report(probe)
    report["branch"]["id"] = "S3-address-codes-the-roster"
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("the branch is stale" in item for item in problems)


def test_check_rejects_a_non_fraction(probe, tmp_path):
    report = _report(probe)
    report["mechanism"]["heldout"]["one_address_fraction"] = 1.4
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("one_address_fraction is not a fraction" in item for item in problems)


def test_check_rejects_a_changed_carrier(probe, tmp_path):
    report = _report(probe)
    report["instrument"]["checkpoint_unchanged"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("checkpoint bytes changed" in item for item in problems)
