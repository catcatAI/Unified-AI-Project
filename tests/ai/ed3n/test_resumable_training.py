"""
Regression tests for resumable / staged training in scripts/train_pipeline.py.

These tests guard the contract that a training run killed mid-sub-stage can be
re-invoked and will CONTINUE from the last finished sub-stage (per-epoch ED3N
checkpoints, reflex/sequence/joint guards, per-batch GARDEN checkpoints) rather
than restarting from scratch, and that a step is only marked "completed" once
ALL of its sub-stages finish.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [A] [L0]
# =============================================================================

import os
import sys
import json
import shutil

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import scripts.train_pipeline as tp
from unittest.mock import patch
from ai.core.training_coordinator import TrainingCoordinator


def _ckpt_dir():
    return tp.CKPT_DIR


def _make_tiny_batches():
    s = []
    for a, b in [("Alice", "Bob"), ("Bob", "Carol")]:
        s.append({
            "input": f"{a} is taller than {b}.",
            "output": f"{b} is shorter than {a}.",
            "domain": "association",
        })
    for i in range(20):
        s.append({"input": f"{i}+1", "output": str(i + 1), "domain": "math"})
    return {"ed3n": s, "garden": []}


def _state_file():
    return os.path.join(_ckpt_dir(), "training_state.json")


@pytest.fixture(autouse=True)
def _clean_ckpt():
    d = _ckpt_dir()
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)
    yield
    if os.path.isdir(d):
        shutil.rmtree(d)


def _save_state_factory(state):
    def save_state(step, data=None):
        if "completed_steps" not in state:
            state["completed_steps"] = []
        if step not in state["completed_steps"]:
            state["completed_steps"].append(step)
        if data:
            state.update(data)
        with open(_state_file(), "w", encoding="utf-8") as f:
            json.dump(state, f)
    return save_state


def test_ed3n_epoch_resume_continues_from_checkpoint():
    """A run allowed only 1 epoch, then a 2-epoch run must resume at epoch 2."""
    state = {}
    save = _save_state_factory(state)
    batches = _make_tiny_batches()

    with patch.object(tp, "limit_value", side_effect=lambda k, d=2: 1 if k == "train.ed3n.epochs" else d):
        tp._step4_train_ed3n(TrainingCoordinator(), batches, state, save)

    assert state.get("ed3n_epochs_done") == 1
    assert os.path.exists(os.path.join(_ckpt_dir(), "ed3n_epoch1.json"))
    assert not os.path.exists(os.path.join(_ckpt_dir(), "ed3n_epoch2.json"))

    with patch.object(tp, "limit_value", side_effect=lambda k, d=2: 2 if k == "train.ed3n.epochs" else d):
        tp._step4_train_ed3n(TrainingCoordinator(), batches, state, save)

    assert state.get("ed3n_epochs_done") == 2
    assert os.path.exists(os.path.join(_ckpt_dir(), "ed3n_epoch2.json"))
    # reflex/seq/joint must be skipped on resume (already done in run 1)
    assert state.get("ed3n_reflex_done") is True
    assert state.get("ed3n_seq_done") is True
    assert state.get("ed3n_joint_done") is True


def test_step4_not_completed_mid_epoch_kill():
    """A kill after epoch 1 must NOT mark step 4 complete (else resume skips it)."""
    state = {}
    save = _save_state_factory(state)
    batches = _make_tiny_batches()

    orig_train = tp.ED3NTrainer.train_step
    calls = {"n": 0}

    def _boom(self, batch):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise KeyboardInterrupt("simulated kill after epoch 1")
        return orig_train(self, batch)

    with patch.object(tp, "limit_value", side_effect=lambda k, d=2: 2 if k == "train.ed3n.epochs" else d):
        with patch.object(tp.ED3NTrainer, "train_step", _boom):
            try:
                tp._step4_train_ed3n(TrainingCoordinator(), batches, state, save)
            except KeyboardInterrupt:
                pass

    persisted = json.load(open(_state_file(), encoding="utf-8"))
    assert 4 not in persisted.get("completed_steps", [])
    assert persisted.get("ed3n_epochs_done") == 1
    assert os.path.exists(os.path.join(_ckpt_dir(), "ed3n_epoch1.json"))


def test_garden_batch_resume_continues_from_index():
    """A re-invoked GARDEN step must resume from garden_batch_done, not redo all."""
    state = {"garden_batch_done": 0}
    save = _save_state_factory(state)
    batches = {"ed3n": [], "garden": [{"input": f"fact {i}", "output": str(i)} for i in range(1500)]}

    orig_learn = tp.GARDENEngine.learn_batch
    seen = {"n": 0}

    def _partial(self, samples, confidence=0.7, train_associations=True):
        seen["n"] += len(samples)
        if seen["n"] >= 1000:
            raise KeyboardInterrupt("simulated kill after batch 1")
        return orig_learn(self, samples, confidence=confidence, train_associations=train_associations)

    with patch.object(tp.GARDENEngine, "learn_batch", _partial):
        try:
            tp._step5_train_garden(TrainingCoordinator(), batches, state, save)
        except KeyboardInterrupt:
            pass

    persisted = json.load(open(_state_file(), encoding="utf-8"))
    assert persisted.get("garden_batch_done", 0) >= 500
    assert 5 not in persisted.get("completed_steps", [])

    # Second invocation: should continue from garden_batch_done.
    tp._step5_train_garden(TrainingCoordinator(), batches, state, save)
    persisted = json.load(open(_state_file(), encoding="utf-8"))
    assert persisted.get("garden_batch_done") == 1500
    assert 5 in persisted.get("completed_steps", [])
