# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""Runtime binding for the single core (contract P4/P5): opt-in, default off.

What this is for
----------------
The contract's rule is that continuity lives in **one state object**, not in the
prompt. In production the state has to be advanced by the turn loop and saved;
that is the plumbing this module provides. It deliberately does **not** write
replies: no core in this repository can yet generate open-domain text
(``CORE_GAP_ANALYSIS.md`` §七), so putting one in the reply path would be the
mirror image of the bug the contract forbids — a surface answer attributed to
the core.

Switched on with ``ANGELA_STATEFUL_CORE=1``; the checkpoint directory is
``ANGELA_STATEFUL_CORE_DIR`` (default ``data/core_state``). Default off means a
chat turn behaves exactly as before. With it on, ``state_for_llm`` stops being
the carrier: ``chat_routes._ctx_state_matrix`` skips publishing it and the
provenance says ``state_source="core"``.

Refusals (contract R5: explicit reset only)
------------------------------------------
* no checkpoint -> :meth:`availability` reports why, :meth:`advance` does
  nothing, and no state directory is created;
* a state that exists but cannot be loaded (corrupt bytes, different weights,
  different arm) is **refused and left untouched** — never overwritten with
  zeros, because a silent reset looks exactly like a successful resume;
* the first turn of a fresh deployment creates the state and says
  ``created=True``: that is a new session, not a reset of an existing one.

The tokeniser is a **placeholder**. With no production checkpoint the text is
hashed into ``token_count`` buckets and the provenance says
``tokenizer="hash-bucket"``, so the state's *content* is meaningless; what is
verified here is the plumbing (one object, one writer, saved across turns).
Replacing it is training work (P2), not a config toggle.

Isolation: **one state directory per session** (a digest of the session id),
sharing one weights set. A single process-wide state file would let one user's
turn advance another user's state, which is the "state that belongs to nobody"
problem the contract exists to prevent.

R3 (one writer) is enforced three ways, because each covers what the others
cannot: a per-session thread lock (stripes, so two sessions never queue behind
each other), an advisory file lock in the session directory (``flock`` on POSIX,
``msvcrt`` on Windows), and a version check immediately before saving. The
version check is not redundant — it is the only one that notices a writer that
took no lock at all. Where neither file-lock primitive exists,
``availability()["multi_writer_safe"]`` is False and the limit is stated rather
than assumed away.
"""

from __future__ import annotations

import calendar
import contextlib
import hashlib
import json
import logging
import os
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from ai.core.core_state import CoreState, CoreStateError

logger = logging.getLogger(__name__)

# LAYER: memory  (the state object is the core's memory; the surfaces read it)

ENABLE_ENV = "ANGELA_STATEFUL_CORE"
STATE_DIR_ENV = "ANGELA_STATEFUL_CORE_DIR"
ARCH_ENV = "ANGELA_STATEFUL_CORE_ARCH"

BACKEND_NAME = "stateful-core"
TOKENIZER_NAME = "hash-bucket"

# A gap longer than this is a machine that was asleep/off, not a conversation
# pause; clamping keeps a month of downtime from being fed to al_step as one
# value. The number is a bound on the input, not a claim about the model.
MAX_DT_S = 24 * 3600.0
MAX_TURN_CHARS = 64

# R3: the lock every writer of this session's state takes. A dotfile inside the
# state directory, so it travels with the state it guards; ``CoreState`` reads
# only meta.json/tensors.npz, so it never sees it.
LOCK_FILENAME = ".lock"
# How long a turn may wait for the lock before giving up. Short on purpose: a
# held lock means another writer is mid-turn on the same session, and this core
# is optional infrastructure — waiting 10 s to attach a state nobody reads yet is
# worse than skipping one turn and recording state_source="none".
LOCK_TIMEOUT_S = 2.0
SESSION_LOCK_STRIPES = 64

_TRUTHY = frozenset({"1", "true", "yes", "on"})

_REPO_ROOT = Path(__file__).resolve().parents[5]


def _flag(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in _TRUTHY


def enabled() -> bool:
    """True when the operator opted in; nothing runs when this is False."""
    return _flag(ENABLE_ENV)


def resolve_directory() -> Path:
    configured = os.environ.get(STATE_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return _REPO_ROOT / "data" / "core_state"


def hash_token_ids(text: str, token_count: int, *, limit: int = MAX_TURN_CHARS) -> list[int]:
    """Deterministic bucket ids for ``text`` (placeholder tokenizer).

    ``crc32`` rather than ``hash()``: the built-in is salted per process, so the
    same text would land in different buckets after a restart and the "state
    survived" check would be measuring the salt.
    """
    if token_count <= 1:
        raise ValueError("token_count must be > 1")
    ids = [1 + (zlib.crc32(ch.encode("utf-8")) % (token_count - 1)) for ch in text[:limit]]
    return ids or [1]


def _parse_stamp(value: str) -> Optional[float]:
    """Parse ``CoreState.last_update`` as the UTC instant it records.

    ``calendar.timegm``, not ``time.mktime``: the stamp is written in UTC, and
    ``mktime`` reads its struct as *local* time, which would silently add the
    host's UTC offset to every gap (8 h here) and turn a two-second pause into
    an eight-hour ``al_step``.
    """
    try:
        return float(calendar.timegm(time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")))
    except (TypeError, ValueError, OverflowError):
        return None


def _lock_backend() -> str:
    """Which cross-process lock this host can actually take.

    Reported verbatim by ``availability()`` so the limit is visible: a host
    with neither ``fcntl`` nor ``msvcrt`` is safe for one worker only, and it
    says so instead of assuming the lock exists.
    """
    if os.name == "nt":
        try:
            import msvcrt  # noqa: F401

            return "msvcrt"
        except ImportError:
            return "none"
    try:
        import fcntl  # noqa: F401

        return "flock"
    except ImportError:
        return "none"


def _windows_lock(fd: int, *, acquire: bool) -> None:  # pragma: no cover - Windows only
    """Take or release the ``msvcrt`` byte lock on ``fd``.

    Isolated, and the constants are read with ``getattr``: on a POSIX host the
    ``msvcrt`` stub has neither ``locking`` nor ``LK_NBLCK``, and a
    ``# type: ignore`` here would spend the project's zero-tolerance ignore
    budget on a branch that can never run there.
    """
    import msvcrt

    locking = getattr(msvcrt, "locking")
    flag = getattr(msvcrt, "LK_NBLCK" if acquire else "LK_UNLCK")
    os.lseek(fd, 0, os.SEEK_SET)
    locking(fd, flag, 1)


@contextlib.contextmanager
def _cross_process_lock(path: Path, timeout: Optional[float] = None) -> Iterator[None]:
    """Hold an exclusive lock on ``path`` for the duration of the block.

    Both primitives are *advisory*: they only stop writers that take the same
    lock. That is why this sits under the per-session thread lock and next to
    the version check — each covers what the others cannot (the thread lock
    cannot see another process, the version check catches a writer that
    bypassed both). A refused wait raises ``TimeoutError``; the caller turns
    that into a refusal rather than a mutation.

    ``LOCK_NB`` in a poll loop, not a blocking call: a blocking ``flock`` has no
    timeout, and a wedged holder would hang a chat turn forever. ``timeout``
    defaults to ``LOCK_TIMEOUT_S`` read at call time, not bound at import, so a
    test (or an operator) can shorten it.
    """
    backend = _lock_backend()
    if backend == "none":
        yield
        return

    wait = LOCK_TIMEOUT_S if timeout is None else float(timeout)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.0, wait)
    flock = None
    if backend == "flock":
        import fcntl

        flock = fcntl
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        while True:
            try:
                if flock is not None:
                    flock.flock(fd, flock.LOCK_EX | flock.LOCK_NB)
                else:
                    _windows_lock(fd, acquire=True)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"{path} is held by another writer")
                time.sleep(0.02)
        try:
            yield
        finally:
            try:
                if flock is not None:
                    flock.flock(fd, flock.LOCK_UN)
                else:
                    _windows_lock(fd, acquire=False)
            except OSError as exc:  # pragma: no cover - closing releases it anyway
                logger.debug("state lock release failed: %s", exc)
    finally:
        os.close(fd)


class _SessionLocks:
    """One lock per session, implemented as a fixed set of stripes.

    A dict keyed by session id would grow without bound, and evicting an entry
    that is currently held would let a second thread make a fresh lock for the
    same session — two writers, silently. Stripes never change size, so a
    session's lock object is stable for the life of the process; collisions only
    add contention between sessions that were never competing anyway.
    """

    def __init__(self, stripes: int = SESSION_LOCK_STRIPES) -> None:
        self._locks = [threading.Lock() for _ in range(max(1, int(stripes)))]

    def for_key(self, key: str) -> threading.Lock:
        index = zlib.crc32(key.encode("utf-8")) % len(self._locks)
        return self._locks[index]


def _disk_version(state_path: Path) -> Optional[int]:
    """The ``state_version`` currently written, or None when there is none.

    Read with a plain ``json.load`` rather than ``CoreState.load``: this is the
    guard that runs immediately before saving, and it only needs the counter.
    A file that cannot be parsed returns None, which the caller treats as
    "cannot verify" — refusal, not overwrite.
    """
    try:
        payload = json.loads((state_path / "meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return int(payload.get("state_version", 0))
    except (TypeError, ValueError):
        return None


class ChatCoreRuntime:
    """One core, one state object, advanced once per turn.

    The instance is process-wide (:func:`get_runtime`) so the checkpoint is
    loaded once and every turn goes through the same object. That is not what
    makes multi-worker safe — R3's file lock and version check do, and they
    hold even across processes that never share this instance.
    """

    def __init__(self, directory: Optional[Path] = None, arch: Optional[str] = None) -> None:
        self._directory = Path(directory) if directory is not None else None
        self._arch = arch
        # Loading the checkpoint is once-per-process; the turn itself is
        # serialised per session (R3), not globally, so two sessions do not
        # queue behind each other.
        self._core_lock = threading.RLock()
        self._session_locks = _SessionLocks()
        self._core: Any = None
        self._load_error: Optional[str] = None
        self._last_refusal: Optional[str] = None

    # -- introspection ------------------------------------------------------

    @property
    def directory(self) -> Path:
        return self._directory if self._directory is not None else resolve_directory()

    @property
    def weights_path(self) -> Path:
        return self.directory / "weights.pt"

    @property
    def state_root(self) -> Path:
        return self.directory / "state"

    def state_path_for(self, session_id: str) -> Path:
        """One state directory per session.

        A single process-wide state file would let one user's turn advance
        another user's state — the exact "state that belongs to nobody"
        problem the contract is about. The directory name is a digest, so an
        arbitrary session id cannot escape the state root.
        """
        key = hashlib.sha256((session_id or "default").encode("utf-8")).hexdigest()[:16]
        return self.state_root / key

    def availability(self) -> Dict[str, Any]:
        """Why the core can or cannot run right now (cheap; no torch import).

        ``lock``/``multi_writer_safe`` describe the writer guarantee: with no
        cross-process primitive the in-process lock is all there is, and more
        than one worker would be more than one writer (R3).
        """
        backend = _lock_backend()
        limits = {"lock": backend, "multi_writer_safe": backend != "none"}
        if not enabled():
            return {
                "enabled": False,
                "available": False,
                "reason": f"{ENABLE_ENV} is not set (opt-in, default off)",
                "directory": str(self.directory),
                **limits,
            }
        if not self.weights_path.is_file():
            return {
                "enabled": True,
                "available": False,
                "reason": f"no checkpoint at {self.weights_path}",
                "directory": str(self.directory),
                **limits,
            }
        if self._load_error:
            return {
                "enabled": True,
                "available": False,
                "reason": self._load_error,
                "directory": str(self.directory),
                **limits,
            }
        return {
            "enabled": True,
            "available": True,
            "reason": "ok",
            "directory": str(self.directory),
            **limits,
        }

    @property
    def last_refusal(self) -> Optional[str]:
        """Why the most recent ``advance()`` refused, or None.

        Kept because "returned None" is the same answer for a missing
        checkpoint, a tampered file and a lost version race, and those need
        different fixes.
        """
        return self._last_refusal

    def carries_continuity(self) -> bool:
        """True when a **loaded** core holds continuity, so the prompt must not.

        Requiring a live core, not just a file on disk: if torch is missing or
        the checkpoint cannot be loaded, suppressing the prompt carrier would
        remove the only continuity there is and put nothing in its place.
        ``advance()`` runs before the pipeline, so by the time this is asked on
        a real turn the core is either loaded or known to be unusable.
        """
        return self._core is not None and bool(self.availability()["available"])

    # -- loading ------------------------------------------------------------

    def _load_core(self) -> Any:
        """Build the arm the checkpoint describes, then load it strictly.

        The arm comes from the file, not from the environment: a checkpoint
        written by ``ssm`` must not be loaded into a ``gru`` just because the
        operator's variable says so.
        """
        torch = self._torch()
        payload = torch.load(self.weights_path, map_location="cpu", weights_only=True)
        config = dict(payload.get("config") or {})
        arch = str(config.get("model_kind") or self._arch or "ssm")
        hidden = int(config.get("hidden", 64))
        emb = int(config.get("emb", 32))
        chunk_seconds = float(config.get("chunk_seconds", 60.0))
        token_count = int(config.get("token_count", 0))
        if token_count <= 1:
            raise ValueError("checkpoint does not declare token_count")

        from ai.core.stateful_decoder import GRUCore, SSMCore, StatefulCore

        core: StatefulCore
        if arch == "gru":
            core = GRUCore(token_count, hidden=hidden, emb=emb, chunk_seconds=chunk_seconds)
        elif arch == "ssm":
            core = SSMCore(token_count, hidden=hidden, emb=emb, chunk_seconds=chunk_seconds)
        else:
            raise ValueError(f"unknown core arm in checkpoint: {arch!r}")
        core.load_weights(str(self.weights_path))
        return core.eval()

    @staticmethod
    def _torch() -> Any:
        import torch

        return torch

    # -- the turn -----------------------------------------------------------

    def advance(
        self,
        text: str,
        *,
        session_id: str = "",
        user_id: str = "",
        now: Optional[float] = None,
        expected_version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Advance the state by this turn; return provenance, or None on refusal.

        Called once per chat turn (``chat_routes._handle_chat_request``). Any
        failure is logged and swallowed: the core is opt-in infrastructure and
        must never take the reply down with it. A refusal always leaves the
        existing state file byte-identical.

        ``user_id`` is recorded on a new state and checked on a resumed one: a
        state that cannot name its owner is the "state belonging to nobody" the
        contract is about, and one whose owner disagrees with the caller belongs
        to somebody else. An existing state with an empty owner (written before
        this field was passed) is accepted — refusing it would retroactively
        invalidate every state written by §41's run.

        ``expected_version`` is the optimistic half of R3: a caller that read a
        snapshot earlier can require that the state has not moved since. The
        locks already stop the writers we control; this catches one that
        bypassed them (a tool, a hand edit, an older build).
        """
        if not enabled():
            self._last_refusal = f"{ENABLE_ENV} is not set"
            return None
        core = self._loaded_core()
        if core is None:
            self._last_refusal = self._load_error or "checkpoint is not loaded"
            return None

        state_path = self.state_path_for(session_id)
        # R3: every mutation of this session is serialised twice over — the
        # stripe stops other threads here, the lock file stops other processes.
        # Held across load → step → save, which is what makes the version check
        # meaningful rather than decorative.
        with self._session_locks.for_key(str(state_path)):
            try:
                with _cross_process_lock(state_path / LOCK_FILENAME):
                    return self._advance_locked(
                        core, state_path, text, session_id, user_id, now, expected_version
                    )
            except TimeoutError as exc:
                self._last_refusal = str(exc)
                logger.warning("stateful core gave up waiting for the state lock: %s", exc)
                return None
            except OSError as exc:
                # The lock file could not even be opened (permissions, a full
                # disk). That is a refusal, not a reason to write without one.
                self._last_refusal = f"cannot lock the state: {exc}"
                logger.warning("stateful core could not lock the state: %s", exc)
                return None

    def _loaded_core(self) -> Any:
        """The loaded checkpoint, or None with ``_load_error`` set.

        Double-checked under ``_core_lock`` so concurrent first turns do not
        build the arm twice; the arm itself is immutable afterwards.
        """
        with self._core_lock:
            if self._core is not None:
                return self._core
            try:
                self._core = self._load_core()
                self._load_error = None
                if _lock_backend() == "none":  # pragma: no cover - exotic host
                    # Once per load, not per turn: the limit is a configuration
                    # fact, and repeating it every turn would bury the noise.
                    logger.warning(
                        "stateful core has no cross-process lock on this host; "
                        "run exactly one worker until it does"
                    )
            except Exception as exc:  # noqa: BLE001 - reported, never raised
                self._load_error = f"cannot load {self.weights_path}: {exc}"
                logger.warning("stateful core unavailable: %s", self._load_error)
                return None
            return self._core

    def _advance_locked(
        self,
        core: Any,
        state_path: Path,
        text: str,
        session_id: str,
        user_id: str,
        now: Optional[float],
        expected_version: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """The load → al_step → ai_step → save body; caller holds both locks."""
        stamp_now = float(now if now is not None else time.time())
        created = False
        try:
            if (state_path / "meta.json").is_file():
                state = CoreState.load(state_path, expected_weights_hash=core.weights_hash())
                # load() hands back numpy; the cell steps on tensors. The
                # attach also re-checks model_kind/weights_hash, so a state
                # written by another arm is refused here, not silently used.
                state = core.attach_state(state)
                if user_id and state.user_id and state.user_id != user_id:
                    self._last_refusal = f"state belongs to {state.user_id!r}, not {user_id!r}"
                    logger.warning("stateful core %s", self._last_refusal)
                    return None
            else:
                state = core.init_state(1, user_id=user_id, session_id=session_id or "chat")
                created = True
        except CoreStateError as exc:
            # Refuse, and do not touch the file: a reset here would look like
            # a successful resume to every later reader.
            self._last_refusal = f"refused the saved state: {exc}"
            logger.warning("stateful core refused the saved state: %s", exc)
            return None

        loaded_version = int(state.state_version)
        if expected_version is not None and loaded_version != int(expected_version):
            self._last_refusal = (
                f"state moved: expected version {expected_version}, found {loaded_version}"
            )
            logger.warning("stateful core %s", self._last_refusal)
            return None

        dt = 0.0 if created else self._elapsed_seconds(state, stamp_now)
        if dt > 0.0:
            state = core.al_step(dt, state)

        torch = self._torch()
        tokens = torch.tensor(
            [hash_token_ids(text, int(getattr(core, "token_count")))], dtype=torch.long
        )
        with torch.no_grad():
            core.ai_step(tokens, state)

        if not created:
            # R3's version check: the counter we read must still be the one on
            # disk. Inside the locks this should always hold, which is exactly
            # why it is worth checking — a writer that bypassed them (tool,
            # hand edit, older build) lands here instead of being overwritten.
            # An unreadable file is the same answer: refusing beats resurrecting
            # a state whose history we can no longer see.
            on_disk = _disk_version(state_path)
            if on_disk is None:
                self._last_refusal = (
                    f"cannot verify the version on disk (read {loaded_version}); refusing to write"
                )
                logger.warning("stateful core %s", self._last_refusal)
                return None
            if on_disk != loaded_version:
                self._last_refusal = f"version conflict: read {loaded_version}, disk has {on_disk}"
                logger.warning("stateful core %s; refusing to overwrite", self._last_refusal)
                return None

        try:
            core.export_state(state).save(state_path)
        except (CoreStateError, OSError) as exc:
            self._last_refusal = f"could not save the state: {exc}"
            logger.warning("stateful core could not save the state: %s", exc)
            return None

        self._last_refusal = None
        return {
            "backend": BACKEND_NAME,
            "arch": getattr(core, "model_kind", "unknown"),
            "tokenizer": TOKENIZER_NAME,
            "user_id": str(state.user_id),
            "ticks": int(state.ticks),
            "state_version": int(state.state_version),
            "dt_s": round(dt, 3),
            "created": created,
            "weights_hash": core.weights_hash(),
            "state_path": str(state_path),
        }

    @staticmethod
    def _elapsed_seconds(state: CoreState, now: float) -> float:
        stamp = _parse_stamp(str(state.last_update or ""))
        if stamp is None:
            return 0.0
        return max(0.0, min(float(now) - stamp, MAX_DT_S))


_runtime: Optional[ChatCoreRuntime] = None
_runtime_lock = threading.Lock()


def get_runtime() -> ChatCoreRuntime:
    """The process-wide runtime, so one checkpoint is loaded once per process.

    This is not the writer guarantee — that is R3's locks and version check,
    which also hold against processes that never share this object.
    """
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                _runtime = ChatCoreRuntime(
                    arch=(os.environ.get(ARCH_ENV) or None),
                )
    return _runtime


def reset_runtime_for_tests() -> None:
    """Drop the cached runtime (tests only; never called by production code)."""
    global _runtime
    with _runtime_lock:
        _runtime = None


__all__ = [
    "BACKEND_NAME",
    "ChatCoreRuntime",
    "ENABLE_ENV",
    "MAX_DT_S",
    "STATE_DIR_ENV",
    "TOKENIZER_NAME",
    "enabled",
    "get_runtime",
    "hash_token_ids",
    "reset_runtime_for_tests",
    "resolve_directory",
]
