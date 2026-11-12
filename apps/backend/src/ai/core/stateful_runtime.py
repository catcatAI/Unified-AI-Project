# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""Runtime binding for the single core (contract P4): opt-in, default off.

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
Replacing it is P2/P5 work, not a config toggle.

Isolation: **one state directory per session** (a digest of the session id),
sharing one weights set. A single process-wide state file would let one user's
turn advance another user's state, which is the "state that belongs to nobody"
problem the contract exists to prevent.
"""

from __future__ import annotations

import calendar
import hashlib
import logging
import os
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Dict, Optional

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


class ChatCoreRuntime:
    """One core, one state object, advanced once per turn.

    The instance is process-wide (:func:`get_runtime`) because the contract's
    R1/R3 allow exactly one writer: two runtimes would be two writers of one
    state file.
    """

    def __init__(self, directory: Optional[Path] = None, arch: Optional[str] = None) -> None:
        self._directory = Path(directory) if directory is not None else None
        self._arch = arch
        self._lock = threading.RLock()
        self._core: Any = None
        self._load_error: Optional[str] = None

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
        """Why the core can or cannot run right now (cheap; no torch import)."""
        if not enabled():
            return {
                "enabled": False,
                "available": False,
                "reason": f"{ENABLE_ENV} is not set (opt-in, default off)",
                "directory": str(self.directory),
            }
        if not self.weights_path.is_file():
            return {
                "enabled": True,
                "available": False,
                "reason": f"no checkpoint at {self.weights_path}",
                "directory": str(self.directory),
            }
        if self._load_error:
            return {
                "enabled": True,
                "available": False,
                "reason": self._load_error,
                "directory": str(self.directory),
            }
        return {
            "enabled": True,
            "available": True,
            "reason": "ok",
            "directory": str(self.directory),
        }

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
        now: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Advance the state by this turn; return provenance, or None on refusal.

        Called once per chat turn (``chat_routes._handle_chat_request``). Any
        failure is logged and swallowed: the core is opt-in infrastructure and
        must never take the reply down with it. A refusal always leaves the
        existing state file byte-identical.
        """
        if not enabled():
            return None
        with self._lock:
            if self._core is None:
                try:
                    self._core = self._load_core()
                    self._load_error = None
                except Exception as exc:  # noqa: BLE001 - reported, never raised
                    self._load_error = f"cannot load {self.weights_path}: {exc}"
                    logger.warning("stateful core unavailable: %s", self._load_error)
                    return None
            core = self._core

            state_path = self.state_path_for(session_id)
            stamp_now = float(now if now is not None else time.time())
            created = False
            try:
                if (state_path / "meta.json").is_file():
                    state = CoreState.load(state_path, expected_weights_hash=core.weights_hash())
                    # load() hands back numpy; the cell steps on tensors. The
                    # attach also re-checks model_kind/weights_hash, so a state
                    # written by another arm is refused here, not silently used.
                    state = core.attach_state(state)
                else:
                    state = core.init_state(1, session_id=session_id or "chat")
                    created = True
            except CoreStateError as exc:
                # Refuse, and do not touch the file: a reset here would look
                # like a successful resume to every later reader.
                logger.warning("stateful core refused the saved state: %s", exc)
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

            try:
                core.export_state(state).save(state_path)
            except (CoreStateError, OSError) as exc:
                logger.warning("stateful core could not save the state: %s", exc)
                return None

            return {
                "backend": BACKEND_NAME,
                "arch": getattr(core, "model_kind", "unknown"),
                "tokenizer": TOKENIZER_NAME,
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
    """The process-wide runtime (R3: one writer for one state file)."""
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
