# ANGELA-MATRIX: L2 [βγδ] [A] [L3+]
"""P0 contract tests for the core state schema (``ai/core/core_state.py``).

These cover §3 of ``AI_AL_SINGLE_CORE_CONTRACT.md`` only -- the shape of a state
object and the refusal rules.  ``ai_step``/``al_step`` behaviour (T1-T6) is P1
and must not be implied by a green run here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from ai.core.core_state import (
    META_FILENAME,
    SCHEMA_VERSION,
    TENSORS_FILENAME,
    CoreState,
    CoreStateCorrupt,
    CoreStateInvalid,
    CoreStateTooLarge,
    CoreStateVersionMismatch,
    hash_weights_bytes,
)

WEIGHTS = hash_weights_bytes(b"weights-v1")


def _new_state(**overrides) -> CoreState:
    params = dict(
        model_kind="gru",
        weights_hash=WEIGHTS,
        user_id="user-1",
        session_id="session-1",
        tensors={"h": np.arange(8, dtype=np.float32)},
        now="2026-11-12T00:00:00Z",
    )
    params.update(overrides)
    return CoreState.create(**params)


def test_roundtrip_preserves_state_and_tensors(tmp_path: Path) -> None:
    state = _new_state()
    state.ticks = 7
    state.last_dt_s = 12.5
    state.bump(now="2026-11-12T00:00:12Z")
    state.save(tmp_path)

    loaded = CoreState.load(tmp_path)

    assert loaded.schema_version == SCHEMA_VERSION
    assert loaded.model_kind == state.model_kind
    assert loaded.weights_hash == state.weights_hash
    assert loaded.user_id == state.user_id
    assert loaded.session_id == state.session_id
    assert loaded.born_at == state.born_at
    assert loaded.last_update == "2026-11-12T00:00:12Z"
    assert loaded.ticks == 7
    assert loaded.last_dt_s == pytest.approx(12.5)
    assert loaded.state_version == state.state_version == 1
    np.testing.assert_array_equal(loaded.tensors["h"], state.tensors["h"])


def test_save_writes_exactly_two_files_and_no_temp_leftovers(tmp_path: Path) -> None:
    _new_state().save(tmp_path)

    names = sorted(path.name for path in tmp_path.iterdir())
    assert names == sorted([META_FILENAME, TENSORS_FILENAME])


def test_meta_persists_no_derived_fields(tmp_path: Path) -> None:
    """Derived read-outs (emotion/intensity/drift) must not become state."""
    _new_state().save(tmp_path)
    meta = json.loads((tmp_path / META_FILENAME).read_text(encoding="utf-8"))

    assert set(meta) == {
        "schema_version",
        "model_kind",
        "weights_hash",
        "user_id",
        "session_id",
        "born_at",
        "last_update",
        "ticks",
        "last_dt_s",
        "state_version",
        "tensors",
        "checksum",
    }


def test_missing_meta_refuses_instead_of_resetting(tmp_path: Path) -> None:
    with pytest.raises(CoreStateCorrupt):
        CoreState.load(tmp_path)

    assert not (tmp_path / META_FILENAME).exists()


def test_missing_tensors_refuses(tmp_path: Path) -> None:
    _new_state().save(tmp_path)
    (tmp_path / TENSORS_FILENAME).unlink()

    with pytest.raises(CoreStateCorrupt):
        CoreState.load(tmp_path)


def test_tensor_tampering_is_rejected_by_checksum(tmp_path: Path) -> None:
    _new_state().save(tmp_path)
    path = tmp_path / TENSORS_FILENAME
    payload = bytearray(path.read_bytes())
    payload[-16] ^= 0xFF
    path.write_bytes(bytes(payload))

    with pytest.raises(CoreStateCorrupt):
        CoreState.load(tmp_path)


def test_meta_tampering_is_rejected_by_checksum(tmp_path: Path) -> None:
    _new_state().save(tmp_path)
    path = tmp_path / META_FILENAME
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["ticks"] = 999
    path.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(CoreStateCorrupt):
        CoreState.load(tmp_path)


def test_schema_version_mismatch_refuses(tmp_path: Path) -> None:
    _new_state().save(tmp_path)

    with pytest.raises(CoreStateVersionMismatch):
        CoreState.load(tmp_path, expected_schema_version=SCHEMA_VERSION + 1)


def test_weights_hash_mismatch_refuses(tmp_path: Path) -> None:
    _new_state().save(tmp_path)

    with pytest.raises(CoreStateVersionMismatch):
        CoreState.load(tmp_path, expected_weights_hash=hash_weights_bytes(b"other"))


def test_state_version_is_monotonic_across_save_load(tmp_path: Path) -> None:
    state = _new_state()
    for _ in range(3):
        state.bump()
    state.save(tmp_path)
    loaded = CoreState.load(tmp_path)
    loaded.bump()
    loaded.save(tmp_path)

    assert CoreState.load(tmp_path).state_version == 4


def test_save_refuses_non_numpy_tensors(tmp_path: Path) -> None:
    """A torch tensor with an autograd graph must be exported, not silently saved."""
    state = _new_state()
    state.tensors["h"] = [1.0, 2.0, 3.0]

    with pytest.raises(CoreStateInvalid):
        state.save(tmp_path)

    assert not (tmp_path / META_FILENAME).exists()


def test_oversized_state_is_refused_not_truncated(tmp_path: Path) -> None:
    big = np.random.default_rng(0).standard_normal(3_000_000).astype(np.float32)
    state = _new_state(tensors={"h": big})

    with pytest.raises(CoreStateTooLarge):
        state.save(tmp_path)

    assert not (tmp_path / META_FILENAME).exists()
    assert not (tmp_path / TENSORS_FILENAME).exists()


def test_create_rejects_unknown_model_kind() -> None:
    with pytest.raises(CoreStateInvalid):
        _new_state(model_kind="transformer")


def test_create_rejects_placeholder_weights_hash() -> None:
    with pytest.raises(CoreStateInvalid):
        _new_state(weights_hash="todo")


def test_malformed_weights_hash_in_meta_is_corruption(tmp_path: Path) -> None:
    _new_state().save(tmp_path)
    path = tmp_path / META_FILENAME
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["weights_hash"] = "todo"
    path.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(CoreStateCorrupt):
        CoreState.load(tmp_path)
