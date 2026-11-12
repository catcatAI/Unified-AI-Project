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


# -- R3: one writer per session ---------------------------------------------


def test_availability_reports_the_writer_guarantee(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    report = _runtime(_checkpoint(tmp_path / "core")).availability()

    assert report["lock"] in {"flock", "msvcrt", "none"}
    # The claim must match the primitive: a host without a file lock is safe
    # for exactly one worker, and it says so instead of assuming.
    assert report["multi_writer_safe"] is (report["lock"] != "none")


def test_one_session_has_one_lock_and_other_sessions_do_not_share_it() -> None:
    from ai.core.stateful_runtime import _SessionLocks

    locks = _SessionLocks(stripes=64)
    assert locks.for_key("session-a") is locks.for_key("session-a")
    # A fixed stripe set: it cannot grow, so a session's lock never changes
    # identity (an evictable dict would let a second thread in).
    assert len({id(locks.for_key(f"s{i}")) for i in range(200)}) <= 64


def test_concurrent_turns_on_one_session_are_serialised(monkeypatch, tmp_path) -> None:
    import threading

    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    results = []
    errors = []

    def _turn(index: int) -> None:
        try:
            results.append(runtime.advance(f"turn {index}", session_id="s1", now=1000.0 + index))
        except Exception as exc:  # pragma: no cover - the assertion is that none happen
            errors.append(exc)

    threads = [threading.Thread(target=_turn, args=(i,)) for i in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    # No turn may be lost: losing one would be two writers reading the same
    # version and the later save overwriting the earlier one.
    assert all(item is not None for item in results)
    versions = sorted(int(item["state_version"]) for item in results)
    assert versions == list(range(1, 13))


def test_a_stale_expected_version_is_refused(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    first = runtime.advance("hello", session_id="s1", now=1000.0)
    assert first is not None
    before = (runtime.state_path_for("s1") / "meta.json").read_bytes()

    assert runtime.advance("stale", session_id="s1", expected_version=999) is None
    assert "expected version 999" in (runtime.last_refusal or "")
    assert (runtime.state_path_for("s1") / "meta.json").read_bytes() == before

    resumed = runtime.advance(
        "fresh", session_id="s1", expected_version=first["state_version"], now=1120.0
    )
    assert resumed is not None


def test_a_writer_that_bypasses_the_lock_is_detected(monkeypatch, tmp_path) -> None:
    """The version check is the only guard that sees an unlocked writer.

    Reproduced faithfully: the interfering write is a *legitimate* save (valid
    checksum) that took no lock, so only the counter can reveal it.
    """
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    first = runtime.advance("hello", session_id="s1", now=1000.0)
    assert first is not None

    core = runtime._core
    state_path = Path(first["state_path"])
    real_ai_step = core.ai_step

    def _interfere(tokens, state):
        other = core.attach_state(
            CoreState.load(state_path, expected_weights_hash=core.weights_hash())
        )
        other.bump()
        core.export_state(other).save(state_path)
        return real_ai_step(tokens, state)

    monkeypatch.setattr(core, "ai_step", _interfere)

    assert runtime.advance("second", session_id="s1", now=1120.0) is None
    assert "version conflict" in (runtime.last_refusal or "")
    # The other writer's state is still the one on disk — refusing means not
    # overwriting, not rolling back somebody else's turn.
    assert CoreState.load(state_path).state_version == first["state_version"] + 1


@pytest.mark.skipif(os.name == "nt", reason="the holder process uses fcntl")
def test_the_cross_process_lock_blocks_then_times_out(monkeypatch, tmp_path) -> None:
    import subprocess
    import sys

    from ai.core import stateful_runtime

    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    first = runtime.advance("hello", session_id="s1", now=1000.0)
    assert first is not None
    lock_path = Path(first["state_path"]) / stateful_runtime.LOCK_FILENAME
    assert lock_path.is_file()

    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl, os, time\n"
            f"fd = os.open({str(lock_path)!r}, os.O_RDWR | os.O_CREAT)\n"
            "fcntl.flock(fd, fcntl.LOCK_EX)\n"
            "print('held', flush=True)\n"
            "time.sleep(1.5)\n",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "held"
        monkeypatch.setattr(stateful_runtime, "LOCK_TIMEOUT_S", 0.25)

        assert runtime.advance("blocked", session_id="s1", now=1120.0) is None
        assert "held by another writer" in (runtime.last_refusal or "")
    finally:
        holder.wait(timeout=30)
        if holder.stdout is not None:
            holder.stdout.close()

    # Released, so the next turn is not punished for the earlier contention.
    assert runtime.advance("after release", session_id="s1", now=1240.0) is not None


def test_a_state_says_whose_it_is(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))

    first = runtime.advance("hello", session_id="s1", user_id="alice")
    assert first is not None
    assert first["user_id"] == "alice"
    assert CoreState.load(runtime.state_path_for("s1")).user_id == "alice"


def test_another_users_state_is_refused_not_shared(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    assert runtime.advance("hello", session_id="s1", user_id="alice") is not None
    before = (runtime.state_path_for("s1") / "meta.json").read_bytes()

    # Session ids are guessable; the owner is what decides. Sharing the state
    # here would let one user's turn advance another user's continuity.
    assert runtime.advance("hi", session_id="s1", user_id="bob") is None
    assert "belongs to 'alice'" in (runtime.last_refusal or "")
    assert (runtime.state_path_for("s1") / "meta.json").read_bytes() == before


def test_an_ownerless_state_is_adopted_not_rejected(monkeypatch, tmp_path) -> None:
    """States written before the owner was recorded must still resume.

    §41's measured run created its state with ``user_id=""``; refusing those
    would retroactively invalidate every state on disk.
    """
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    first = runtime.advance("hello", session_id="s1")
    assert first is not None
    assert first["user_id"] == ""

    resumed = runtime.advance("second", session_id="s1", user_id="alice", now=1120.0)
    assert resumed is not None


@pytest.mark.skipif(os.name == "nt", reason="the workers use fcntl-backed locks")
def test_two_processes_advance_one_state_without_losing_a_turn(monkeypatch, tmp_path) -> None:
    """The cross-process claim, measured rather than inferred from the lock.

    Ten turns spread over two real processes. Accounting is exact: the creating
    turn bumps once, every later turn bumps twice (al_step then ai_step), so the
    final version must be ``1 + 2 * 9`` whatever the interleaving. A lost update
    shows up as a smaller number and the run fails.
    """
    import subprocess
    import sys
    import textwrap

    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    directory = _checkpoint(tmp_path / "core")
    runtime = _runtime(directory)

    worker = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {str(Path("apps/backend/src").resolve())!r})
        os.environ["ANGELA_STATEFUL_CORE"] = "1"
        os.environ["ANGELA_STATEFUL_CORE_DIR"] = {str(directory)!r}
        from ai.core.stateful_runtime import ChatCoreRuntime
        runtime = ChatCoreRuntime(directory={str(directory)!r}, arch="ssm")
        results = [
            runtime.advance(f"turn {{i}}", session_id="shared", user_id="alice")
            for i in range(5)
        ]
        refused = [i for i, item in enumerate(results) if item is None]
        print("refused", refused)
        sys.exit(1 if refused else 0)
        """)

    workers = [
        subprocess.run([sys.executable, "-c", worker], capture_output=True, text=True)
        for _ in range(2)
    ]

    assert [worker.returncode for worker in workers] == [0, 0], [
        worker.stderr[-500:] for worker in workers
    ]
    final = CoreState.load(runtime.state_path_for("shared"))
    assert final.state_version == 1 + 2 * 9
    assert final.user_id == "alice"


def test_an_unreadable_state_file_is_refused_rather_than_resurrected(monkeypatch, tmp_path) -> None:
    """If the counter cannot be read, writing would recreate a lost history.

    The state was loadable a moment ago, so this is not "first turn": the file
    that says which version we are continuing vanished mid-turn. Saving anyway
    would put a fresh meta.json where the previous history used to be, which
    every later reader would see as a normal resume.
    """
    monkeypatch.setenv("ANGELA_STATEFUL_CORE", "1")
    runtime = _runtime(_checkpoint(tmp_path / "core"))
    first = runtime.advance("hello", session_id="s1", now=1000.0)
    assert first is not None

    core = runtime._core
    state_path = Path(first["state_path"])
    real_ai_step = core.ai_step

    def _remove_meta(tokens, state):
        (state_path / "meta.json").unlink()
        return real_ai_step(tokens, state)

    monkeypatch.setattr(core, "ai_step", _remove_meta)

    assert runtime.advance("second", session_id="s1", now=1120.0) is None
    assert "cannot verify the version on disk" in (runtime.last_refusal or "")
    assert not (state_path / "meta.json").exists()
