# ANGELA-MATRIX: L2 [βγδ] [A] [L3+]
"""SSM arm tests: exact semigroup, shared state, and a learnable time constant.

These pin the properties §40 relies on **before** the scored run:

* ``al_step`` is a product of exponentials, so the semigroup holds exactly
  (the probe's 1e-2 gate must be trivially met — that is the architectural
  claim, not a capability claim);
* zero time is the identity, and a skipped ``al_step`` leaves the state alone;
* per-sample ``dt`` only touches the samples that have time left;
* the state round-trips through ``CoreState`` / checkpointing with identical
  logits, and ``tau`` is part of the weights hash and the checkpoint.

No training happens here.
"""

from __future__ import annotations

import numpy as np
import pytest
from ai.core.core_state import CoreState
from ai.core.stateful_decoder import SSMCore

torch = pytest.importorskip("torch")


def _model(**kwargs) -> SSMCore:
    options = {"hidden": 16, "emb": 8, "seed": 0}
    options.update(kwargs)
    return SSMCore(26, **options).eval()


def _hidden(state: CoreState) -> torch.Tensor:
    return state.tensors["h"]


def test_semigroup_is_exact_for_uneven_pairs() -> None:
    model = _model()
    state = model.init_state(5, session_id="semigroup")
    state.tensors["h"] = torch.randn(5, model.hidden)

    for dt1, dt2 in ((30.0, 30.0), (20.0, 40.0), (50.0, 50.0), (7.0, 53.0)):
        with torch.no_grad():
            sequential = model.init_state(5)
            sequential.tensors["h"] = _hidden(state).clone()
            model.al_step(dt1, sequential)
            model.al_step(dt2, sequential)

            joined = model.init_state(5)
            joined.tensors["h"] = _hidden(state).clone()
            model.al_step(dt1 + dt2, joined)

            delta = float((_hidden(sequential) - _hidden(joined)).abs().max())

        # The registered gate is 1e-2; exactness should be far below it.
        assert delta <= 1e-5, f"{dt1}+{dt2}: max|dh|={delta:.3e}"


def test_zero_time_is_the_identity() -> None:
    model = _model()
    state = model.init_state(3, session_id="zero")
    state.tensors["h"] = torch.randn(3, model.hidden)
    before = _hidden(state).clone()
    ticks = state.ticks

    returned = model.al_step(0.0, state)

    assert returned is state
    assert torch.equal(_hidden(state), before)
    assert state.ticks == ticks


def test_per_sample_dt_only_moves_samples_with_time() -> None:
    model = _model()
    state = model.init_state(3, session_id="batch")
    state.tensors["h"] = torch.randn(3, model.hidden)
    before = _hidden(state).clone()

    model.al_step([0.0, 30.0, 90.0], state)

    assert torch.equal(_hidden(state)[0], before[0])
    assert not torch.equal(_hidden(state)[1], before[1])
    assert state.ticks == 2  # 30 s -> 1 chunk, 90 s -> 2 chunks


def test_decay_is_monotonic_in_elapsed_time() -> None:
    model = _model()
    norms = []
    for dt in (0.0, 10.0, 60.0, 120.0, 400.0):
        state = model.init_state(2, session_id="monotonic")
        state.tensors["h"] = torch.ones(2, model.hidden)
        with torch.no_grad():
            model.al_step(dt, state)
        norms.append(float(_hidden(state).norm(dim=-1).mean()))

    assert norms == sorted(norms, reverse=True)
    assert norms[0] > norms[-1]


def test_state_round_trip_keeps_the_logits() -> None:
    model = _model()
    state = model.init_state(2, session_id="roundtrip")
    tokens = torch.tensor([[1, 2, 3], [4, 5, 6]])

    with torch.no_grad():
        snapshot = model.export_state(state)
        logits_a, _ = model.ai_step(tokens, state)

        assert isinstance(snapshot.tensors["h"], np.ndarray)

        restored = model.attach_state(snapshot)
        logits_b, _ = model.ai_step(tokens, restored)

    assert torch.equal(logits_a, logits_b)


def test_time_enters_only_through_al_step() -> None:
    model = _model()
    tokens = torch.tensor([[1, 2], [3, 4]])
    query = torch.tensor([[5], [6]])

    with torch.no_grad():
        first = model.init_state(2, session_id="skip")
        _, first = model.ai_step(tokens, first)

        second = model.init_state(2, session_id="skip")
        _, second = model.ai_step(tokens, second)

        model.al_step(60.0, first)
        with_time, _ = model.ai_step(query, first)
        without_time, _ = model.ai_step(query, second)

    # The elapsed time exists for the model only because al_step ran on `first`.
    assert not torch.equal(with_time, without_time)


def test_tau_is_log_spaced_positive_and_learnable() -> None:
    model = _model(tau_min=20.0, tau_max=2000.0).train()
    tau = model.tau().detach()

    assert bool((tau > 0).all())
    assert float(tau.min()) >= 20.0 - 1e-3
    assert float(tau.max()) <= 2000.0 + 1e-3
    assert float(tau.max()) > 10.0 * float(tau.min())

    state = model.init_state(2, session_id="grad")
    state.tensors["h"] = torch.randn(2, model.hidden)
    model.al_step(30.0, state)
    loss = _hidden(state).pow(2).mean()
    loss.backward()

    assert model.tau_log.grad is not None
    assert float(model.tau_log.grad.abs().sum()) > 0.0


def test_tau_is_hashed_and_checkpointed(tmp_path) -> None:
    model = _model()
    before = model.weights_hash()

    with torch.no_grad():
        model.tau_log[0] += 0.5
    model.invalidate_hash()
    assert model.weights_hash() != before

    path = tmp_path / "ssm.pt"
    model.save_weights(str(path))
    restored = _model()
    restored.load_weights(str(path))

    assert torch.equal(restored.tau(), model.tau().detach())
    assert restored.weights_hash() == model.weights_hash()
    assert restored.config()["model_kind"] == "ssm"


def test_model_kind_and_parameter_count_are_reported() -> None:
    model = _model(hidden=12, emb=5)
    state = model.init_state(1)

    assert state.model_kind == "ssm"
    expected = 26 * 5 + 5 * 12 + (12 * 26 + 26) + 12
    assert model.parameter_count() == expected
