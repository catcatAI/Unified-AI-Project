# ANGELA-MATRIX: L2 [βγδ] [A] [L3+]
"""Contract tests for the two-cycle step interface (``ai_step`` / ``al_step``).

These pin the mechanics, not the score:

* ``chunk_dt`` splits gaps into equal chunks of ≤ 60 s and treats zero/negative
  time as **identity**;
* ``al_step`` updates only the samples whose gap is non-zero (no zero-input
  padding that would move a finished sample's ``h``);
* ``ai_step`` and ``al_step`` share one set of weights and one state object;
* exporting a state (numpy) and attaching it back is exact, and the same holds
  through ``CoreState.save`` / ``CoreState.load`` — the unit-level half of T4.

No training happens here; a run that changes the design must fail a test
before it can move a number in ``CORE_GAP_ANALYSIS.md`` §37.
"""

from __future__ import annotations

import numpy as np
import pytest
from ai.core.core_state import CoreState
from ai.core.core_step import chunk_dt

torch = pytest.importorskip("torch")

from ai.core.stateful_decoder import GRUCore  # noqa: E402


def _model(**kwargs) -> GRUCore:
    defaults = dict(token_count=8, hidden=4, emb=3, seed=0)
    defaults.update(kwargs)
    return GRUCore(**defaults).eval()


def _state_with_h(model: GRUCore, hidden) -> CoreState:
    state = model.init_state(int(hidden.shape[0]), session_id="unit")
    state.tensors["h"] = hidden.clone()
    return state


@pytest.mark.parametrize(
    "dt,expected",
    [
        (0.0, ()),
        (-5.0, ()),
        (30.0, (30.0,)),
        (60.0, (60.0,)),
        (90.0, (45.0, 45.0)),
    ],
)
def test_chunk_dt_splits_equally_within_the_limit(dt, expected) -> None:
    assert chunk_dt(dt) == expected


def test_chunk_dt_conserves_time_and_respects_the_limit() -> None:
    for dt in (1.0, 59.9, 61.0, 240.0, 400.0):
        chunks = chunk_dt(dt)
        assert sum(chunks) == pytest.approx(dt)
        assert max(chunks) <= 60.0
        assert len(chunks) == len(set(chunks)) or len(chunks) > 1


@pytest.mark.parametrize("dt", [float("nan"), float("inf")])
def test_chunk_dt_refuses_non_finite_time(dt) -> None:
    with pytest.raises(ValueError):
        chunk_dt(dt)


def test_zero_time_is_bitwise_identity() -> None:
    model = _model()
    state = model.init_state(2, session_id="zero")
    state.tensors["h"] = torch.randn(2, 4)
    before = state.tensors["h"].clone()
    ticks, version = state.ticks, state.state_version

    with torch.no_grad():
        returned = model.al_step(0.0, state)

    assert returned is state
    assert torch.equal(state.tensors["h"], before)
    assert (state.ticks, state.state_version) == (ticks, version)


def test_al_step_updates_only_samples_with_time() -> None:
    model = _model()
    hidden = torch.tensor([[0.1] * 4, [0.2] * 4])
    batch = _state_with_h(model, hidden)

    with torch.no_grad():
        model.al_step(torch.tensor([0.0, 90.0]), batch)
        zero_only = _state_with_h(model, hidden[0:1])
        model.al_step(0.0, zero_only)
        with_time = _state_with_h(model, hidden[1:2])
        model.al_step(90.0, with_time)

    assert torch.equal(batch.tensors["h"][0], hidden[0])
    assert torch.equal(batch.tensors["h"][0], zero_only.tensors["h"][0])
    assert torch.allclose(batch.tensors["h"][1], with_time.tensors["h"][0], atol=1e-6)


def test_al_step_ticks_count_chunks_not_calls() -> None:
    model = _model()
    state = model.init_state(1, session_id="ticks")

    with torch.no_grad():
        model.al_step(90.0, state)

    assert state.ticks == 2


def test_ai_step_returns_logits_and_mutates_the_same_state() -> None:
    model = _model()
    state = model.init_state(2, session_id="ai")
    before = state.tensors["h"].clone()
    tokens = torch.tensor([[1, 2, 3], [4, 5, 6]])

    with torch.no_grad():
        logits, returned = model.ai_step(tokens, state)

    assert returned is state
    assert logits.shape == (2, 3, 8)
    assert not torch.equal(state.tensors["h"], before)
    assert state.state_version == 1


def test_ai_step_rejects_a_batch_that_disagrees_with_the_state() -> None:
    model = _model()
    state = model.init_state(2, session_id="mismatch")

    with pytest.raises(ValueError):
        model.ai_step(torch.tensor([[1, 2, 3]]), state)


def test_export_attach_roundtrip_is_exact() -> None:
    model = _model()
    state = model.init_state(2, session_id="roundtrip")
    state.tensors["h"] = torch.randn(2, 4)
    state.ticks = 7

    exported = model.export_state(state)
    assert isinstance(exported.tensors["h"], np.ndarray)
    restored = model.attach_state(exported)

    assert torch.equal(restored.tensors["h"], state.tensors["h"])
    assert restored.ticks == state.ticks


def test_state_survives_save_and_load_with_identical_logits(tmp_path) -> None:
    model = _model()
    state = model.init_state(2, session_id="save")
    state.tensors["h"] = torch.randn(2, 4)
    tokens = torch.tensor([[1, 2], [3, 4]])

    # Save the pre-step state first: ai_step() mutates the state it is given.
    model.export_state(state).save(tmp_path)

    with torch.no_grad():
        expected, _ = model.ai_step(tokens, state)
        loaded = CoreState.load(tmp_path, expected_weights_hash=model.weights_hash())
        restored = model.attach_state(loaded)
        actual, _ = model.ai_step(tokens, restored)

    assert torch.equal(actual, expected)


def test_weights_hash_is_stable_and_changes_with_weights() -> None:
    model = _model()
    first = model.weights_hash()
    assert first.startswith("sha256:")
    assert model.weights_hash() == first

    with torch.no_grad():
        next(model.parameters()).add_(1.0)
    model.invalidate_hash()

    assert model.weights_hash() != first


def test_semigroup_is_reported_not_claimed() -> None:
    """30+30 vs 60 seconds is *close*, not identical — and that is documented."""
    model = _model()
    hidden = torch.zeros(2, 4)

    with torch.no_grad():
        left = _state_with_h(model, hidden)
        model.al_step(30.0, left)
        model.al_step(30.0, left)
        right = _state_with_h(model, hidden)
        model.al_step(60.0, right)

    difference = float((left.tensors["h"] - right.tensors["h"]).abs().max())
    assert 0.0 < difference < 1.0


# -- round 2: the chunk count must stop being a time signal ------------------
#
# §37's gaps were unequal, so a 180 s gap became three al_step chunks and a 20 s
# gap one; "how many steps elapsed" could stand in for "how much time elapsed".
# Round 2 fixes 8 equal gaps, so every session takes exactly 8 chunks and only
# the dt magnitude carries the gap.  These tests pin that property *before* the
# scored run, so a generator change cannot quietly restore the shortcut.


def _load_probe():
    import importlib.util
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    scripts = repo_root / "scripts"
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "probe_state_cycles_under_test", scripts / "probe_state_cycles.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves ``cls.__module__`` through sys.modules; an exec'd
    # module that was never registered fails at the first @dataclass.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load_probe()


def _chunk_totals(sessions, probe_module) -> set:
    from ai.core.core_step import chunk_dt

    return {sum(len(chunk_dt(gap, 60.0)) for gap in session.gaps) for session in sessions}


def test_round2_generator_equalises_step_counts(probe) -> None:
    sessions = probe.generate_sessions(200, seed=2000, gap_count=8, gap_mode="equal")

    assert {len(session.gaps) for session in sessions} == {8}
    assert max(max(session.gaps) for session in sessions) <= 50.0
    assert _chunk_totals(sessions, probe) == {8}


def test_round2_generator_preserves_the_registered_bands(probe) -> None:
    sessions = probe.generate_sessions(400, seed=7, gap_count=8, gap_mode="equal")
    totals = [sum(session.gaps) for session in sessions]

    valid = [total for total, session in zip(totals, sessions) if not session.expired]
    expired = [total for total, session in zip(totals, sessions) if session.expired]

    assert valid and expired
    assert all(total <= 200.0 for total in valid)
    assert all(280.0 <= total <= 400.0 for total in expired)
    assert all(total > probe.EXPIRY_S for total in expired)
    assert all(total <= probe.EXPIRY_S for total in valid)


def test_round1_generator_still_has_varying_step_counts(probe) -> None:
    """Round 1 is kept reproducible *and* known to leak the chunk count."""
    sessions = probe.generate_sessions(400, seed=11, gap_count=4, gap_mode="random")

    assert len(_chunk_totals(sessions, probe)) > 1


def test_round2_fake_clock_keeps_the_same_step_count(probe) -> None:
    sessions = probe.generate_sessions(64, seed=5, gap_count=8, gap_mode="equal")
    fake = [(120.0 / 8,) * 8 for _ in sessions]

    assert _chunk_totals(sessions, probe) == {8}
    assert {sum(len(chunk_dt(gap, 60.0)) for gap in gaps) for gaps in fake} == {8}
