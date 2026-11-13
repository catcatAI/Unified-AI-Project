# ANGELA-MATRIX: L4 [βγδ] [B] [L3]
"""The credit-assignment probe's contract (§49.16).

These tests do not measure a model. They pin the apparatus that decides the next
variable:

* the probe's forward pass is ``run_session``'s (same ``ai_step``/``al_step``
  order, same tokenisation helpers) - if it drifted, the gradient profile would
  describe a different computation than the one the trainer runs;
* ``grad_profile`` reports the earliest turn above the floor, how many turns are
  reached, and a backwards shrink factor, and it does not invent a reach when
  every gradient is below the floor;
* the mechanism it claims is real even in a toy model: the answer's gradient
  reaches the last turns and dies before the evidence turns;
* a floor of zero would make "no gradient" look like "reach", so the floor is
  positive by construction.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "probe_credit_assignment.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("credit_assignment_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["credit_assignment_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def driver(probe):
    return probe.load_driver()


class _FakeGrad:
    def __init__(self, norm: float) -> None:
        self._norm = norm

    def norm(self) -> float:
        return self._norm


class _FakeTensor:
    def __init__(self, norm: float) -> None:
        self.grad = _FakeGrad(norm)


def test_reach_is_the_earliest_turn_above_the_floor(probe):
    profile = probe.grad_profile(
        core=None,
        boundary=[_FakeTensor(0.0), _FakeTensor(1e-12), _FakeTensor(1e-3), _FakeTensor(1.0)],
        floor=1e-6,
    )
    assert profile["turns"] == 4
    assert profile["earliest_turn_above_floor"] == 2
    assert profile["turns_reached"] == 2
    assert profile["norms"][0] == 0.0


def test_no_reach_is_reported_as_none_not_zero(probe):
    profile = probe.grad_profile(
        core=None,
        boundary=[_FakeTensor(1e-12), _FakeTensor(1e-9)],
        floor=1e-6,
    )
    assert profile["earliest_turn_above_floor"] is None
    assert profile["turns_reached"] is None
    # the decay is still measurable when nothing clears the floor
    assert profile["shrink_per_turn"] is not None and profile["shrink_per_turn"] < 1.0


def test_shrink_is_measured_backwards(probe):
    # 1.0 -> 1e-3 -> 1e-6 going forwards = 1e3 shrink per turn going backwards
    profile = probe.grad_profile(
        core=None,
        boundary=[_FakeTensor(1.0), _FakeTensor(1e-3), _FakeTensor(1e-6)],
        floor=1e-12,
    )
    assert profile["shrink_per_turn"] == pytest.approx(1e3, rel=1e-6)


def test_the_floor_is_positive(probe):
    assert probe.GRAD_FLOOR > 0.0


def test_forward_pass_is_run_sessions_sequence(probe, driver):
    torch = pytest.importorskip("torch")
    core = driver.build_core(hidden=8, emb=4, device="cpu", seed=23)
    session = driver.load_corpus()["heldout"][0]

    with torch.enable_grad():
        loss, hidden, boundary = probe.turnwise_forward(driver, core, [session])
    with torch.no_grad():
        _, expected = driver.run_session(
            core, [driver.turn_tokens(session)], [driver.turn_gaps(session)]
        )
    assert len(boundary) == len(session["turns"])
    assert torch.allclose(hidden, expected, atol=1e-6)
    assert torch.isfinite(loss)
    assert loss.ndim == 0


def test_gradient_reaches_only_the_end_of_a_long_session(probe, driver):
    """The claim the probe exists for: the evidence turns get no gradient.

    A toy width is enough - this is the recurrence's contract, not a property of
    the trained checkpoint.
    """
    torch = pytest.importorskip("torch")
    core = driver.build_core(hidden=8, emb=4, device="cpu", seed=29)
    session = driver.load_corpus()["heldout"][1]

    with torch.enable_grad():
        loss, _, boundary = probe.turnwise_forward(driver, core, [session])
        loss.backward()
    profile = probe.grad_profile(core, boundary)

    assert profile["turns"] == 11
    assert profile["turns_reached"] is not None and profile["turns_reached"] <= 2
    # the earliest turn is not merely below the floor: it is numerically absent
    assert profile["norms"][0] < 1e-12
    assert profile["shrink_per_turn"] < 1.0


# --------------------------------------------------------------------------- #
# the state probe (§50.13): is the conclusion in the state at all?
# --------------------------------------------------------------------------- #
def _planted(probe, torch, *, separability=6.0, seed=7):
    generator = torch.Generator().manual_seed(seed)
    centres = torch.eye(3) * separability
    train_x, train_y, test_x, test_y = [], [], [], []
    for label in range(3):
        train_x.append(centres[label] + 0.1 * torch.randn(40, 3, generator=generator))
        test_x.append(centres[label] + 0.1 * torch.randn(20, 3, generator=generator))
        train_y += [label] * 40
        test_y += [label] * 20
    return (
        torch.cat(train_x),
        probe._one_hot(train_y, 3),
        torch.cat(test_x),
        test_y,
    )


def test_ridge_readout_recovers_a_planted_signal(probe):
    torch = pytest.importorskip("torch")
    train_x, train_y, test_x, test_y = _planted(probe, torch)
    logits = probe.ridge_readout(train_x, train_y, test_x, ridge=1.0)
    predicted = [int(value) for value in logits.argmax(dim=1)]
    assert predicted == test_y  # a real signal is not allowed to read as chance


def test_ridge_readout_is_at_chance_on_random_labels(probe):
    """Without a signal the readout must not find one: this is the null."""
    torch = pytest.importorskip("torch")
    generator = torch.Generator().manual_seed(11)
    train_x = torch.randn(300, 8, generator=generator)
    test_x = torch.randn(200, 8, generator=generator)
    train_y = probe._one_hot([int(v) for v in torch.randint(0, 4, (300,), generator=generator)], 4)
    accuracy = (probe.ridge_readout(train_x, train_y, test_x).argmax(dim=1) == 0).float().mean()
    assert float(accuracy) < 0.45  # chance is 0.25; allow the small-sample wobble


def test_state_spread_reports_collinearity(probe):
    torch = pytest.importorskip("torch")
    generator = torch.Generator().manual_seed(13)
    # sessions differ only by how far they slide along one shared direction
    direction = torch.randn(16, generator=generator)
    scales = torch.randn(50, 1, generator=generator)
    collinear = 30.0 + scales * direction + 1e-3 * torch.randn(50, 16, generator=generator)
    spread = probe.state_spread(collinear)
    assert spread["mean_pairwise_cosine"] > 0.99  # all sessions point the same way
    assert spread["participation_ratio"] < 2.0  # and vary along ~one direction

    isotropic = torch.randn(400, 16, generator=generator)
    wide = probe.state_spread(isotropic)
    assert abs(wide["mean_pairwise_cosine"]) < 0.2
    assert wide["participation_ratio"] > 8.0


def test_probe_labels_are_the_culprit_or_the_chain(probe, driver):
    sessions = driver.load_corpus()["heldout"][:3]
    assert probe._labels(sessions, "culprit") == [
        session["ground_truth_oracle"]["culprit"] for session in sessions
    ]
    assert probe._labels(sessions, "chain") == [
        session["session_meta"]["chain"] for session in sessions
    ]
    with pytest.raises(SystemExit):
        probe._labels(sessions, "width")


def test_probe_skips_overfit_smoke_and_control_reports(probe, tmp_path, monkeypatch):
    """A calibration arm or a format control must never stand in for the model."""
    monkeypatch.setattr(probe, "REPORTS", tmp_path)
    (tmp_path / "pantry_deduction_0001.json").write_text(
        json.dumps({"control_arm": "rand", "checkpoint": "control.pt"}), encoding="utf-8"
    )
    (tmp_path / "pantry_deduction_0002.json").write_text(
        json.dumps({"control_arm": "answer", "smoke": True, "checkpoint": "smoke.pt"}),
        encoding="utf-8",
    )
    (tmp_path / "pantry_deduction_0003.json").write_text(
        json.dumps({"control_arm": "answer", "overfit": True, "checkpoint": "cal.pt"}),
        encoding="utf-8",
    )
    assert probe._newest_scored_report() is None
    (tmp_path / "pantry_deduction_0004.json").write_text(
        json.dumps({"control_arm": "answer", "checkpoint": "scored.pt"}), encoding="utf-8"
    )
    assert probe._newest_scored_report().name.endswith("0004.json")


def test_state_probe_scores_only_held_out_sessions(probe, driver):
    pytest.importorskip("torch")
    corpus = driver.load_corpus()
    core = driver.build_core(hidden=8, emb=4, device="cpu", seed=61)
    block = probe.state_probe(
        driver,
        core,
        corpus["train"][:8],
        corpus["heldout"][:4],
        boundaries=[6, 10],
        batch=4,
    )
    assert block["target"] == "culprit"
    assert block["train_n"] == 8 and block["heldout_n"] == 4
    assert [row["boundary"] for row in block["boundaries"]] == [6, 10]
    assert block["classes"] >= 2
    assert all(
        row["chance"] == pytest.approx(1 / block["classes"], abs=1e-4)
        for row in block["boundaries"]
    )
    # a toy width on unseen sessions is not allowed to look like a solution
    assert all(row["accuracy"] <= 0.75 for row in block["boundaries"])
    assert "diagnostic" in block["note"]
