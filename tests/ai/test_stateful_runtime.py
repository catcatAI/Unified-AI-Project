# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
"""P4: the stateful core is advanced by the turn loop, opt-in and default off.

The point of these tests is the plumbing, not the score: one state object, one
writer, advanced once per turn and saved, with continuity *not* carried through
the prompt. Every refusal path has to leave the saved state untouched, because
a silent reset looks exactly like a successful resume to the next reader.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("torch")

from ai.core.core_state import CoreState  # noqa: E402
from ai.core.stateful_decoder import SSMCore  # noqa: E402
from ai.core.stateful_runtime import (  # noqa: E402
    BACKEND_NAME,
    TOKENIZER_NAME,
    ChatCoreRuntime,
    _parse_stamp,
    enabled,
    get_runtime,
    hash_token_ids,
    reset_runtime_for_tests,
)

TOKEN_COUNT = 26
SMALL = {"hidden": 8, "emb": 4, "chunk_seconds": 60.0}


@pytest.fixture(autouse=True)
def _clean_runtime(monkeypatch):
    """No cached runtime and no inherited flag between tests."""
    monkeypatch.delenv("ANGELA_STATEFUL_CORE", raising=False)
    monkeypatch.delenv("ANGELA_STATEFUL_CORE_DIR", raising=False)
    reset_runtime_for_tests()
    yield
    reset_runtime_for_tests()


def _checkpoint(directory: Path, *, seed: int = 0) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    SSMCore(TOKEN_COUNT, seed=seed, **SMALL).eval().save_weights(str(directory / "weights.pt"))
    return directory


def _runtime(directory: Path) -> ChatCoreRuntime:
    return ChatCoreRuntime(directory=directory, arch="ssm")


# -- the flag and the tokenizer ----------------------------------------------


def test_disabled_by_default_and_creates_nothing(tmp_path) -> None:
    directory = _checkpoint(tmp_path / "core")

    assert enabled() is False
    runtime = _runtime(directory)
    report = runtime.availability()

    assert report["enabled"] is False
    assert report["available"] is False
    assert "opt-in" in report["reason"]
    assert runtime.carries_continuity() is False
    assert runtime.advance("hello", session_id="s1") is None
    # A disabled core must not leave a directory behind: "off" means off.
    assert runtime.state_root.exists() is False


def test_tokenizer_is_deterministic_across_processes() -> None:
    first = hash_token_ids("hello", TOKEN_COUNT)
    second = hash_token_ids("hello", TOKEN_COUNT)

    # crc32, not the built-in hash(): the built-in is salted per process, so a
    # restart would change the buckets and "the state survived" would be
    # measuring the salt.
    assert first == second
    assert all(1 <= token < TOKEN_COUNT for token in first)
    assert hash_token_ids("", TOKEN_COUNT) == [1]
    assert hash_token_ids("hello", TOKEN_COUNT) != hash_token_ids("world", TOKEN_COUNT)
    with pytest.raises(ValueError):
        hash_token_ids("hello", 1)


def test_stamp_is_read_as_utc_not_local_time() -> None:
    # mktime() would read this struct as local time and silently add the host's
    # UTC offset to every gap.
    assert _parse_stamp("1970-01-01T00:00:00Z") == 0.0
    assert _parse_stamp("2026-11-12T00:00:00Z") == 1794441600.0
    assert _parse_stamp("not a stamp") is None


# -- the turn loop -----------------------------------------------------------


def test_missing_checkpoint_refuses_without_creating_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(tmp_path / "empty")

    report = runtime.availability()

    assert report["enabled"] is True
    assert report["available"] is False
    assert "no checkpoint" in report["reason"]
    assert runtime.advance("hello", session_id="s1") is None
    assert runtime.state_root.exists() is False


def test_two_turns_advance_the_same_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))

    first = runtime.advance("hello there", session_id="s1")
    assert first is not None
    assert first["created"] is True
    assert first["backend"] == BACKEND_NAME
    assert first["tokenizer"] == TOKENIZER_NAME
    assert first["arch"] == "ssm"
    assert first["dt_s"] == 0.0  # a new session has no elapsed time to apply
    assert first["state_version"] == 1

    saved = CoreState.load(runtime.state_path_for("s1"))
    second = runtime.advance(
        "a second turn", session_id="s1", now=_parse_stamp(saved.last_update) + 120.0
    )

    assert second is not None
    assert second["created"] is False
    # A turn with a gap is two mutations (al_step then ai_step), so the counter
    # grows by two: it counts writes, not turns.
    assert second["state_version"] == first["state_version"] + 2
    assert second["dt_s"] == 120.0
    assert second["ticks"] == 2  # one 60 s chunk per chunk_seconds
    assert second["weights_hash"] == first["weights_hash"]
    assert Path(second["state_path"]).is_dir()


def test_continuity_requires_a_live_core_not_just_a_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    directory = _checkpoint(tmp_path / "core")
    runtime = _runtime(directory)

    # A checkpoint on disk is not continuity by itself: if the load fails (no
    # torch, wrong file), suppressing the prompt carrier would remove the only
    # one there is and put nothing in its place.
    assert runtime.availability()["available"] is True
    assert runtime.carries_continuity() is False

    assert runtime.advance("hello", session_id="s1") is not None
    assert runtime.carries_continuity() is True


def test_a_broken_checkpoint_never_carries_continuity(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    directory = tmp_path / "broken"
    directory.mkdir()
    (directory / "weights.pt").write_bytes(b"not a checkpoint")

    runtime = _runtime(directory)

    assert runtime.advance("hello", session_id="s1") is None
    assert runtime.carries_continuity() is False
    assert "cannot load" in runtime.availability()["reason"]


def test_sessions_do_not_share_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))

    runtime.advance("session a, turn 1", session_id="a")
    path_a = runtime.state_path_for("a")
    before_a = (path_a / "meta.json").read_bytes()

    other = runtime.advance("session b, turn 1", session_id="b")

    assert other is not None and other["created"] is True
    assert runtime.state_path_for("b") != path_a
    # One user's turn must not advance another user's state.
    assert (path_a / "meta.json").read_bytes() == before_a


def test_a_second_runtime_resumes_the_saved_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    directory = _checkpoint(tmp_path / "core")

    first = _runtime(directory).advance("before restart", session_id="s1")
    assert first is not None

    resumed = _runtime(directory).advance("after restart", session_id="s1")

    assert resumed is not None
    assert resumed["created"] is False
    assert resumed["state_version"] >= first["state_version"] + 1
    assert resumed["weights_hash"] == first["weights_hash"]


# -- refusals (R5: an explicit reset, never a silent one) --------------------


def test_tampered_state_is_refused_and_left_untouched(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    runtime.advance("hello", session_id="s1")
    state_path = runtime.state_path_for("s1")

    tensors = state_path / "tensors.npz"
    payload = bytearray(tensors.read_bytes())
    payload[len(payload) // 2] ^= 0xFF
    tensors.write_bytes(bytes(payload))
    before_meta = (state_path / "meta.json").read_bytes()

    assert runtime.advance("after the damage", session_id="s1") is None
    assert (state_path / "meta.json").read_bytes() == before_meta


def test_state_from_other_weights_is_refused_and_not_overwritten(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    directory = _checkpoint(tmp_path / "core", seed=0)
    assert _runtime(directory).advance("hello", session_id="s1") is not None

    state_path = _runtime(directory).state_path_for("s1")
    before = (state_path / "meta.json").read_bytes()

    # Different weights, same shape: the state belongs to the old ones.
    _checkpoint(directory, seed=7)

    assert _runtime(directory).advance("still here?", session_id="s1") is None
    assert (state_path / "meta.json").read_bytes() == before


# -- the production wiring ---------------------------------------------------


def _chat_routes():
    pytest.importorskip("fastapi")
    from api.routes import chat_routes

    return chat_routes


def test_prompt_state_is_suppressed_when_the_core_carries_it(monkeypatch) -> None:
    chat_routes = _chat_routes()
    monkeypatch.setattr(chat_routes, "_stateful_core_carries_continuity", lambda: True)

    def _must_not_run():  # pragma: no cover - the assertion is that it is not called
        raise AssertionError("the prompt state must not be published")

    monkeypatch.setattr(chat_routes, "_get_state_matrix", _must_not_run)
    context = {}

    chat_routes._ctx_state_matrix(context)

    assert context == {"state_source": "core"}


def test_default_off_leaves_the_response_shape_alone(monkeypatch, tmp_path) -> None:
    chat_routes = _chat_routes()
    result = {"response_text": "hi"}

    chat_routes._attach_core_provenance(result, None)

    assert result == {"response_text": "hi"}


def test_provenance_records_core_or_none(monkeypatch) -> None:
    chat_routes = _chat_routes()
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    core = {"backend": BACKEND_NAME, "ticks": 3}

    advanced = {"response_text": "hi"}
    chat_routes._attach_core_provenance(advanced, core)
    assert advanced["state_source"] == "core"
    assert advanced["core_state"] == core

    refused = {"response_text": "hi"}
    chat_routes._attach_core_provenance(refused, None)
    # Enabled but refused: claiming "prompt" would assert a carrier this turn
    # never had.
    assert refused["state_source"] == "none"


@pytest.mark.asyncio
async def test_the_turn_loop_advances_the_core_once(monkeypatch, tmp_path) -> None:
    chat_routes = _chat_routes()
    directory = _checkpoint(tmp_path / "core")
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    monkeypatch.setenv("ANGELA_STATEFUL_CORE_DIR", str(directory))
    assert get_runtime().directory == directory

    calls = []

    async def _pipeline(user_message, user_name, history, session_id, *args, **kwargs):
        calls.append((user_message, session_id))
        return {"response_text": "a reply"}

    monkeypatch.setattr(chat_routes, "_run_chat_pipeline", _pipeline)

    result = await chat_routes._handle_chat_request("hello", "tester", [], "session-wired")

    assert calls == [("hello", "session-wired")]
    assert result["state_source"] == "core"
    assert result["core_state"]["backend"] == BACKEND_NAME
    assert result["core_state"]["ticks"] >= 0
    assert (_runtime(directory).state_path_for("session-wired") / "meta.json").is_file()
    # The reply itself is still the pipeline's: the core does not write text.
    assert result["response_text"] == "a reply"


@pytest.mark.asyncio
async def test_the_turn_loop_does_nothing_when_off(monkeypatch, tmp_path) -> None:
    chat_routes = _chat_routes()
    directory = _checkpoint(tmp_path / "core")
    monkeypatch.setenv("ANGELA_STATEFUL_CORE_DIR", str(directory))
    assert os.environ.get("ANGELA_STATEFUL_CORE") is None

    async def _pipeline(user_message, user_name, history, session_id, *args, **kwargs):
        return {"response_text": "a reply"}

    monkeypatch.setattr(chat_routes, "_run_chat_pipeline", _pipeline)

    result = await chat_routes._handle_chat_request("hello", "tester", [], "s-off")

    assert "state_source" not in result
    assert "core_state" not in result
    assert _runtime(directory).state_root.exists() is False
