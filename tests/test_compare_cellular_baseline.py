# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Contract tests for the bounded-cellular-machine baseline (CORE_GAP §二十二).

The design note this baseline implements claims three things that are easy to
state and easy to get wrong. They are pinned here, because the first two runs of
this machine failed them:

1. **No global reset.** A saturated region must be pushed back by its own
   fatigue, not cleared on a timer. The test runs a constant input for 300 steps
   and asserts the container never jumps back to a fresh state.
2. **Not a uniform field.** An all-excitatory lattice synchronises: every cell
   converges to the same value, so the "container" holds one number (measured
   activation std 0.012 over 384 cells). The shipped coupling is mixed-sign and
   the test asserts real contrast survives a long idle run.
3. **The input actually reaches the container.** At ``1/sqrt(cells)`` scaling a
   token moved the activation by ~0.01 against a recurrent drive of ~0.18, and
   different inputs produced indistinguishable states (across-row std 0.004).
   The test asserts that two tokens lead to distinguishable containers.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "compare_cellular_baseline.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("compare_cellular_baseline_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ca():
    return _load(SCRIPT)


def _machine(ca, cells=64, vocab=32, **kwargs):
    return ca.BoundedCellMachine(cells, vocab, seed=0, **kwargs)


def test_constant_input_is_not_a_global_reset(ca):
    """300 steps of one token must not clear the container back to init."""
    machine = _machine(ca)
    initial = machine.features().copy()
    machine.step(5)
    machine.step(5)
    shaped = machine.features().copy()
    for _ in range(300):
        machine.step(5)
    after = machine.features().copy()
    # a timer-based wipe would land exactly on the initial vector
    assert not np.allclose(after, initial, atol=1e-6)
    # and the state must keep evolving rather than freeze on an absorbing point
    assert not np.allclose(after, shaped, atol=1e-6)
    assert np.isfinite(after).all()


def test_lattice_keeps_contrast_instead_of_synchronising(ca):
    """Mixed-sign coupling: cells must not converge to one shared value."""
    machine = _machine(ca, cells=64)
    for _ in range(200):
        machine.step(7)
    spread = float(machine.x.std())
    assert spread > 0.02, f"lattice collapsed to a uniform field (std={spread:.4f})"
    # heterogeneous, not saturated: some cells on, some off
    assert 0.0 < float(machine.x.min()) and float(machine.x.max()) < 1.0


def test_tokens_reach_the_container(ca):
    """Two different tokens must leave different containers."""
    a = _machine(ca, cells=64)
    b = _machine(ca, cells=64)
    a.step(3)
    b.step(11)
    assert not np.allclose(a.features(), b.features(), atol=1e-6)
    # and the difference must survive the recurrent wash-out for a few steps
    a.step(0)
    b.step(0)
    assert not np.allclose(a.features(), b.features(), atol=1e-6)


def test_container_size_and_readout_shape(ca):
    """The container is finite and every state variable is read out."""
    machine = _machine(ca, cells=36, latch=16)
    assert machine.cells == 36
    assert machine.rows * machine.cols >= machine.cells
    assert machine.features().shape == (36 * 4,)  # x, fatigue, threshold, latch
    plain = _machine(ca, cells=36)
    assert plain.features().shape == (36 * 3,)
    # the latch is a slow integrator: it must move slower than the activation
    machine.reset()
    machine.step(1)
    before = machine.m.copy()
    for _ in range(4):
        machine.step(1)
    assert float(np.abs(machine.m - before).mean()) < float(machine.x.std())


def test_scores_use_the_probe_unit(ca):
    """±0.005 on all six fields is the grader's unit, and 0.01 is a miss."""
    fields = ca._FIELDS
    gold = np.array([[0.10, 0.20, 0.30, 0.40, 0.50, 0.60]], dtype=np.float32)
    hit = ca._score(gold.copy(), gold)
    assert hit["row_exact"] == 1.0 and hit["row_hits"] == 1
    miss = gold.copy()
    miss[0, 0] += 0.01  # one step of the print grid is already out of tolerance
    out = ca._score(np.round(miss, 2), gold)
    assert out["row_exact"] == 0.0
    assert out["field_top1"][fields[0]] == 0.0
    assert out["field_top1"][fields[1]] == 1.0
