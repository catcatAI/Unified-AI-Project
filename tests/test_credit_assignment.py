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
