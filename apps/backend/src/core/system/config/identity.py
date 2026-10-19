"""Angela's name, from configuration rather than scattered literals.

WHY this module exists
----------------------
`system/core.default.yaml` declared `ai_name` and no code ever read it, while the
name itself was hardcoded in several places. Two of those literals were also
traps: `create_soul_core(name=...)` accepted a name and then ignored it, and
`angela_agent.py` uses the string "Angela" as a *game player* name, which has
nothing to do with identity.

So the identity name lives here, reads the declared config, and keeps a default
that matches the code's historical behaviour.

WHY the per-user store
----------------------
A rename is a *user* act: every user names their own Angela, so the name
cannot live in a process-global config value. `system/core.default.yaml` stays
the authority for the *default* name (what an unnamed instance is called), and
each `user_id` may override it. Without this, renaming one user's AI would
rename everybody's — the classic "old implementation" bug where the name lives
in a hardcoded literal, a global config, or a prompt string that nobody
touches.

Read path:  `get_ai_name(user_id)` → user override → config `ai_name` →
`DEFAULT_AI_NAME`.
Write path: `set_ai_name(name, user_id)` → validated, persisted to
`data/identities.json`, and the in-process cache is dropped so the next read
sees it.

ANGELA-MATRIX: [L2] [β] [B] [L4]
"""

import json
import logging
import os
import re
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger(__name__)

# The historical hardcoded value. Also the effective default, so a missing or
# broken config can never leave the system nameless.
DEFAULT_AI_NAME = "Angela"

# A user-chosen name is shown in prompts, subtitles and TTS: keep it short
# and free of control characters so it cannot break prompt assembly or
# terminal output.
MAX_AI_NAME_LENGTH = 32
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

# In-process cache of the *config* value and the per-user store.
_CACHE: Optional[str] = None
_STORE_LOCK = threading.RLock()
_STORE_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

# The user the current request belongs to.
#
# Most call sites (the reflex engines, the TTS layer, the offline fallback
# chain) are process-global singletons with no request object, yet they still
# have to answer with the *right* user's name. A context variable carries the
# user through the async request without changing every signature; it is set
# by the chat route and the identity API, and copied into child tasks by
# asyncio — so a background task spawned from a request keeps that user's
# name, which is the intended behaviour.
_CURRENT_USER_ID: ContextVar[Optional[str]] = ContextVar("angela_current_user_id", default=None)


def _repo_root_store_path() -> str:
    """Path of the per-user identity store, anchored to the repo root.

    Anchoring (rather than a cwd-relative path) keeps the file in one place no
    matter where the server is started from — the same rule the lifecycle
    state file follows.
    """
    try:
        return str(Path(__file__).resolve().parents[6] / "data" / "identities.json")
    except Exception:  # pragma: no cover - path resolution failure
        logger.warning(
            "Cannot resolve repo-root identity store path; falling back to "
            "cwd-relative path (per-user names may diverge between processes)",
            exc_info=True,
        )
        return os.path.join("data", "identities.json")


IDENTITY_STORE_PATH = _repo_root_store_path()


# --------------------------------------------------------------------------- #
# Config-backed default name
# --------------------------------------------------------------------------- #
def get_default_ai_name(refresh: bool = False) -> str:
    """The configured default name (what an unnamed instance is called).

    Independent of any per-user override: this is the authority value that
    `set_ai_name` compares against to decide whether an override is needed.
    """
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE

    name = DEFAULT_AI_NAME
    try:
        from core.system.config.tiered_loader import get_config

        config = get_config("system/core") or {}
        raw = config.get("ai_name")
        if isinstance(raw, str) and raw.strip():
            name = raw.strip()
        elif raw is not None:
            logger.warning(
                "ai_name in system/core is not a usable string (%r); using %s", raw, name
            )
    except Exception as exc:  # pragma: no cover - config unavailable
        logger.warning("Could not read ai_name from config (%s); using %s", exc, name)

    _CACHE = name
    return name


def get_ai_name(user_id: Optional[str] = None, refresh: bool = False) -> str:
    """Return the name for *user_id* (or the current user, or the default).

    Resolution order: the user's own override → the configured `ai_name` →
    `DEFAULT_AI_NAME`. A malformed or empty `ai_name` is reported and ignored
    rather than allowed to propagate: an unnamed self-model would be worse than
    a misnamed one.
    """
    resolved_user = user_id if user_id else _CURRENT_USER_ID.get()
    override = _read_override(resolved_user)
    if override:
        return override
    return get_default_ai_name(refresh=refresh)


def current_user_id() -> Optional[str]:
    """The user id of the request currently being served (if any)."""
    return _CURRENT_USER_ID.get()


def set_current_user(user_id: Optional[str]) -> Any:
    """Bind *user_id* as the current user; returns a token for the reset.

    Use this when the request handler already owns a try/finally block
    (the `current_user` context manager is the tidier form otherwise).
    """
    return _CURRENT_USER_ID.set(str(user_id).strip() if user_id else None)


def reset_current_user(token: Any) -> None:
    """Undo a `set_current_user` binding."""
    try:
        _CURRENT_USER_ID.reset(token)
    except Exception as exc:  # pragma: no cover - token from another context
        logger.debug("Could not reset current user binding: %s", exc)


@contextmanager
def current_user(user_id: Optional[str]) -> Iterator[None]:
    """Bind *user_id* as the current user for the duration of the block.

    Used by the request handlers so that every downstream consumer — the
    prompt builder, the reflex engines, the subtitle/TTS layer — resolves the
    same name without having to be handed a user id.
    """
    token = _CURRENT_USER_ID.set(str(user_id).strip() if user_id else None)
    try:
        yield
    finally:
        _CURRENT_USER_ID.reset(token)


def clear_cache() -> None:
    """Drop the memoised name and store (config reload / tests)."""
    global _CACHE, _STORE_CACHE
    _CACHE = None
    with _STORE_LOCK:
        _STORE_CACHE = None


# --------------------------------------------------------------------------- #
# Per-user store
# --------------------------------------------------------------------------- #
def _load_store() -> Dict[str, Dict[str, Any]]:
    """Read the per-user identity store (cached; the file is small)."""
    global _STORE_CACHE
    with _STORE_LOCK:
        if _STORE_CACHE is not None:
            return _STORE_CACHE
        store: Dict[str, Dict[str, Any]] = {}
        try:
            if os.path.exists(IDENTITY_STORE_PATH):
                with open(IDENTITY_STORE_PATH, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                users = raw.get("users") if isinstance(raw, dict) else None
                if isinstance(users, dict):
                    for key, value in users.items():
                        if isinstance(value, dict):
                            store[str(key)] = value
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read identity store %s: %s", IDENTITY_STORE_PATH, exc)
        _STORE_CACHE = store
        return store


def _save_store(store: Dict[str, Dict[str, Any]]) -> None:
    """Persist the per-user store atomically (write temp + replace)."""
    global _STORE_CACHE
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "users": store,
    }
    directory = os.path.dirname(IDENTITY_STORE_PATH)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = f"{IDENTITY_STORE_PATH}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, IDENTITY_STORE_PATH)
    except OSError as exc:
        logger.warning("Could not persist identity store %s: %s", IDENTITY_STORE_PATH, exc)
        return
    with _STORE_LOCK:
        _STORE_CACHE = store


def _read_override(user_id: Optional[str]) -> Optional[str]:
    """The user's own name, if they set one."""
    if not user_id:
        return None
    record = _load_store().get(str(user_id))
    if not record:
        return None
    name = record.get("ai_name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _normalize_user_id(user_id: Optional[str]) -> str:
    return str(user_id).strip() if user_id else ""


def validate_ai_name(name: Any) -> str:
    """Validate a user-chosen name and return its normalised form.

    Raises `ValueError` with a human-readable reason when the name cannot be
    used: a name that is not text, empty, too long, or carrying control
    characters would break prompt assembly, subtitles and TTS.
    """
    if not isinstance(name, str):
        raise ValueError("ai_name must be a string")
    cleaned = _CONTROL_CHARS_RE.sub(" ", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        raise ValueError("ai_name must not be empty")
    if len(cleaned) > MAX_AI_NAME_LENGTH:
        raise ValueError(f"ai_name must be at most {MAX_AI_NAME_LENGTH} characters")
    return cleaned


def set_ai_name(name: Any, user_id: Optional[str] = None) -> str:
    """Set (or clear) the name of *user_id*'s Angela and return the new name.

    Naming the instance back to the configured default removes the override
    instead of storing a redundant copy, so the config stays authoritative for
    that user. `user_id` is required to target a specific user; without it the
    call is rejected, because a global rename would silently rename every
    user's AI.
    """
    key = _normalize_user_id(user_id)
    if not key:
        raise ValueError("user_id is required to name an AI instance")

    cleaned = validate_ai_name(name)
    default = get_default_ai_name()
    with _STORE_LOCK:
        store = _load_store()
        record = dict(store.get(key) or {})
        if cleaned == default:
            record.pop("ai_name", None)
        else:
            record["ai_name"] = cleaned
        record["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if record.get("ai_name") or any(k != "updated_at" for k in record):
            # Keep the record while it carries a name or other state
            # (e.g. the persona state); otherwise drop it entirely.
            store[key] = record
        else:
            store.pop(key, None)
        _save_store(store)
    logger.info("AI name for user %s set to %r", key, cleaned)
    return cleaned


def clear_ai_name(user_id: Optional[str] = None) -> None:
    """Drop the user's name override (back to the configured default)."""
    key = _normalize_user_id(user_id)
    if not key:
        return
    with _STORE_LOCK:
        store = _load_store()
        record = dict(store.get(key) or {})
        if "ai_name" not in record:
            return
        record.pop("ai_name", None)
        if any(k != "updated_at" for k in record):
            store[key] = record
        else:
            store.pop(key, None)
        _save_store(store)


def get_identity_profile(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Describe the identity of *user_id*'s AI instance.

    `source` is "user" when the user has named their AI, "config" when the
    instance still carries the configured default.
    """
    key = _normalize_user_id(user_id)
    override = _read_override(key)
    default = get_default_ai_name()
    record = _load_store().get(key) or {}
    return {
        "ai_name": override or default,
        "default_name": default,
        "source": "user" if override else "config",
        "customized": bool(override),
        "user_id": key or None,
        "updated_at": record.get("updated_at"),
    }


def update_user_profile(user_id: Optional[str], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge *updates* into the user's identity record and return it.

    Used by the persona layer to keep its own state (handover, role) next to
    the name, so one file holds everything about "who this user's AI is".
    """
    key = _normalize_user_id(user_id)
    if not key:
        raise ValueError("user_id is required to update an identity profile")
    with _STORE_LOCK:
        store = _load_store()
        record = dict(store.get(key) or {})
        record.update(updates)
        record["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        store[key] = record
        _save_store(store)
        return dict(record)


def list_identity_profiles() -> Dict[str, Dict[str, Any]]:
    """All known per-user identity records (diagnostics / admin UI)."""
    return {key: dict(value) for key, value in _load_store().items()}
