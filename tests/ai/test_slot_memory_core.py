# ANGELA-MATRIX: L3 [βγδ] [A] [L3+]
"""Round-7 arm: the store is part of the one state, and nothing else changed.

Round 6's conclusion was a design requirement, not a score: addressability does
not emerge from overwriting one 128-d vector twice. This arm adds a key-addressed
store **inside the same state object** and keeps everything else - the
recurrence, the two step functions, the weights hash, the checkpoint format.

These pin the contract properties before the scored run:

* one substrate (R1): ``ai_step`` and ``al_step`` share one weights set and one
  state object; the store is written only by ``ai_step``;
* explicit reset (R5): the store is created by ``init_state`` and round-trips
  through ``CoreState``/checkpointing with identical logits;
* the ablation (R4) removes the store and keeps every parameter;
* the geometry (slots/dims) is part of the weights identity, so a checkpoint
  cannot be loaded into a differently shaped store and silently answer;
* zero time is the identity for the controller and leaves the store alone.

No training happens here.
"""

from __future__ import annotations

import copy

import pytest
from ai.core.core_state import CoreState, CoreStateInvalid
from ai.core.stateful_decoder import SlotMemoryCore

torch = pytest.importorskip("torch")


def _model(**kwargs) -> SlotMemoryCore:
    options = {"hidden": 16, "emb": 8, "seed": 0, "slots": 4, "slot_dim": 8, "value_dim": 8}
    options.update(kwargs)
    return SlotMemoryCore(26, **options).eval()


def _tokens(batch: int, length: int) -> "torch.Tensor":
    generator = torch.Generator().manual_seed(7)
    return torch.randint(0, 26, (batch, length), generator=generator)


def test_one_state_object_holds_the_controller_and_the_store():
    core = _model()
    state = core.init_state(3)
    assert set(state.tensors) == {"h", "slot_k", "slot_v"}
    assert state.tensors["slot_k"].shape == (3, 4, 8)
    assert state.tensors["slot_v"].shape == (3, 4, 8)
    assert state.model_kind == "slots"


def test_both_step_functions_mutate_the_same_object():
    core = _model()
    state = core.init_state(2)
    version = state.state_version
    core.ai_step(_tokens(2, 3), state)
    after_ai = state.state_version
    core.al_step(120.0, state)
    assert version < after_ai < state.state_version
    assert state.ticks >= 1


def test_zero_time_is_the_identity_and_does_not_touch_the_store():
    core = _model()
    state = core.init_state(2)
    core.ai_step(_tokens(2, 2), state)
    before = {name: value.clone() for name, value in state.tensors.items()}
    ticks = state.ticks
    returned = core.al_step(0.0, state)
    assert returned is state
    assert state.ticks == ticks
    for name, value in before.items():
        assert torch.equal(state.tensors[name], value), name


def test_per_sample_dt_only_advances_the_samples_with_time_left():
    core = _model()
    state = core.init_state(2)
    core.ai_step(_tokens(2, 2), state)
    hidden = state.tensors["h"].clone()
    core.al_step(torch.tensor([0.0, 60.0]), state)
    assert torch.equal(state.tensors["h"][0], hidden[0])
    assert not torch.allclose(state.tensors["h"][1], hidden[1])


def test_the_store_is_written_only_by_ai_step():
    core = _model()
    state = core.init_state(2)
    keys, values = state.tensors["slot_k"].clone(), state.tensors["slot_v"].clone()
    assert float(keys.abs().sum()) == 0.0 and float(values.abs().sum()) == 0.0
    core.ai_step(_tokens(2, 4), state)
    assert float(state.tensors["slot_k"].abs().sum()) > 0.0
    assert float(state.tensors["slot_v"].abs().sum()) > 0.0


def test_the_ablation_keeps_every_parameter_and_writes_nothing():
    full = _model()
    ablated = _model(memory=False)
    assert full.parameter_count() == ablated.parameter_count()
    state = ablated.init_state(2)
    ablated.ai_step(_tokens(2, 4), state)
    assert float(state.tensors["slot_v"].abs().sum()) == 0.0
    assert float(ablated.read_vector(state).abs().sum()) == 0.0


def test_the_store_geometry_is_part_of_the_weights_identity(tmp_path):
    core = _model()
    path = tmp_path / "slots.pt"
    core.save_weights(str(path))
    other = _model(slots=8)
    with pytest.raises(RuntimeError):
        other.load_weights(str(path))


def test_state_round_trips_through_core_state_with_identical_logits():
    core = _model()
    with torch.no_grad():
        state = core.init_state(2)
        logits, state = core.ai_step(_tokens(2, 5), state)
        exported = core.export_state(state)
        assert isinstance(exported, CoreState)
        assert set(exported.tensors) == {"h", "slot_k", "slot_v"}
        attached = core.attach_state(exported)
        again, _ = core.ai_step(_tokens(2, 1), copy.deepcopy(attached))
        once, _ = core.ai_step(_tokens(2, 1), copy.deepcopy(state))
    assert torch.allclose(again, once, atol=1e-6)


def test_a_state_from_another_arm_is_refused():
    core = _model()
    foreign = core.init_state(1)
    object.__setattr__(foreign, "model_kind", "gru")
    with pytest.raises(CoreStateInvalid):
        core.attach_state(foreign)


def test_the_weights_hash_covers_the_store_parameters():
    core = _model()
    before = core.weights_hash()
    with torch.no_grad():
        core.value_proj.weight[0, 0] += 1.0
    core.invalidate_hash()
    assert core.weights_hash() != before
