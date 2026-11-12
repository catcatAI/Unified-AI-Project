# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Turn observation — the (state, answer-structure) pairs the AL questions need.

WHY
---
`H(結構) − H(結構 | 狀態)` (docs/06-project-management/HIERARCHICAL_PLAN_FILL_GENERATION.md
§6.1) cannot be computed from anything the repository holds today: the AL clock
file keeps only `born_at`/`ticks`, the event buffer is in memory, and the stored
conversations carry no state from the moment they were written. This module is
the writer for the missing corpus.

WHAT IS STORED
--------------
One JSONL line per answer, **structure only**::

    {v, turn_id, session, day, state, user_move, source, in_len,
     in_len_bucket, topic, out_len, out_len_bucket, skeleton, skeleton_sig,
     consent}

`user_move` labels the *user* message of that turn (question / request / repair /
statement / empty). Read it as the next action for the *previous* answer, so
continue / repair / end is derivable at analysis time without rewriting an
append-only log.

`in_len_bucket` × `topic` is the stratum §6.1 pre-registers ("輸入長度桶 ×
主題桶") for the conditional entropy. Both fields were added before the first
turn was recorded: the original schema stored only the *answer's* length, so
even 2,000 turns could not have been stratified, and there is no way to backfill
them. `topic` is the coarse bucket of the production `QueryClassifier` label,
not a new classifier — see `topic_bucket()`; when classification fails the field
is `"unknown"` (the label is missing, not invented).

WHAT IS NOT STORED
------------------
Neither the user's text nor the answer's text is written. Two lengths, bucket
labels, skeleton flags and their hash are all the metric needs; a leak of this
file cannot reconstruct a conversation.

DEFAULT OFF
-----------
`ANGELA_TURN_OBSERVATION=1` (true/yes/on) enables it; `ANGELA_TURN_OBSERVATION_DIR`
overrides the directory (default `<data root>/observations`). Off means off:
no directory, no file — probes and benchmarks run with the default and write
nothing into the environment they measure.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)

VERSION = 2

_ENV_ENABLED = "ANGELA_TURN_OBSERVATION"
_ENV_DIR = "ANGELA_TURN_OBSERVATION_DIR"
_TRUTHY = frozenset({"1", "true", "yes", "on"})

# The nine observable AL fields minus the invariants (born_at) and the derived
# ones (drift is rejected by _persist, so it is never available here either).
# Missing values stay None — never 0.0 (D11: an unobserved field is not zero,
# and filling it would let A1 "win" on a fabricated signal).
STATE_FIELDS = (
    "life_phase",
    "life_cycle_state",
    "health",
    "intensity",
    "emotion",
    "tendency",
    "rhythm",
    "ticks",
)

_BULLET = re.compile(r"^\s*[-*•]\s+")
_NUMBERED = re.compile(r"^\s*\d+[.)、]\s+")
_SENTENCE_SPLIT = re.compile(r"[。！？!?]+|(?<=[.])\s+|\n+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")

# Deliberately tight: a false "repair" is worse than calling it a question, and
# the log is append-only, so a mislabel cannot be fixed later.
_REPAIR_MARKERS = (
    "我是說",
    "我是说",
    "你搞錯",
    "你搞错",
    "答錯了",
    "答错了",
    "錯了，",
    "错了，",
    "不對，",
    "不对，",
    "不是，",
    "重答",
    "再答一次",
    "i meant",
    "you're wrong",
    "youre wrong",
    "that's wrong",
    "thats wrong",
)
_REQUEST_MARKERS = ("幫我", "帮我", "告訴我", "告诉我", "請你", "请你", "解釋", "解释", "查一下")
_QUESTION_MARKERS = (
    "什麼",
    "什么",
    "為什麼",
    "为什么",
    "怎麼",
    "怎么",
    "哪",
    "誰",
    "谁",
    "多少",
    "幾個",
    "几个",
    "是不是",
    "能不能",
    "有沒有",
    "有没有",
    "what",
    "why",
    "how",
    "which",
    "who",
    "when",
    "where",
)


def observation_enabled(environ: Optional[Mapping[str, str]] = None) -> bool:
    """Is turn observation switched on for this process?"""
    env = os.environ if environ is None else environ
    return str(env.get(_ENV_ENABLED, "")).strip().lower() in _TRUTHY


def observation_dir(environ: Optional[Mapping[str, str]] = None) -> Path:
    """Where the JSONL files go (created lazily, only when a turn is written)."""
    env = os.environ if environ is None else environ
    override = str(env.get(_ENV_DIR, "")).strip()
    if override:
        return Path(override).expanduser()
    from core.data_config import get_data_root

    return get_data_root() / "observations"


def length_bucket(chars: int) -> str:
    """Bucket a stripped character count (1, 2-4, 5-8, 9-16, 17+)."""
    if chars <= 0:
        return "0"
    if chars == 1:
        return "1"
    if chars <= 4:
        return "2-4"
    if chars <= 8:
        return "5-8"
    if chars <= 16:
        return "9-16"
    return "17+"


def structure_signature(text: str) -> Dict[str, Any]:
    """Length + skeleton of an answer, with no readable content in it."""
    stripped = (text or "").strip()
    lines = [line for line in stripped.splitlines() if line.strip()]
    paragraphs = [p for p in _PARAGRAPH_SPLIT.split(stripped) if p.strip()]
    sentences = [s for s in _SENTENCE_SPLIT.split(stripped) if s.strip()]
    skeleton: Dict[str, Any] = {
        "lines": len(lines),
        "paragraphs": len(paragraphs),
        "sentences": len(sentences),
        "bullets": any(_BULLET.match(line) for line in lines),
        "numbered": any(_NUMBERED.match(line) for line in lines),
        "code_fence": "```" in stripped,
        "question": ("?" in stripped) or ("？" in stripped),
    }
    digest = hashlib.sha256(
        json.dumps(skeleton, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:12]
    return {
        "chars": len(stripped),
        "bucket": length_bucket(len(stripped)),
        "skeleton": skeleton,
        "signature": digest,
    }


def classify_user_move(text: str) -> str:
    """Label the user's message without keeping it (question/request/repair/...)."""
    lowered = (text or "").strip().lower()
    if not lowered:
        return "empty"
    if any(marker in lowered for marker in _REPAIR_MARKERS):
        return "repair"
    if any(marker in lowered for marker in _REQUEST_MARKERS):
        return "request"
    if lowered.endswith(("?", "？")) or any(marker in lowered for marker in _QUESTION_MARKERS):
        return "question"
    return "statement"


# Coarse stratum labels, not a new taxonomy: each entry is a group of the
# production QueryClassifier's own QueryType values (ai/core/query_classifier.py).
# Kept deliberately few — §6.1 needs every (length × topic) cell to reach 200
# turns, and a finer split only multiplies the corpus that does not exist yet.
_TOPIC_BUCKETS = {
    "math": "math",  # MATH, LOGIC
    "logic": "math",
    "knowledge": "knowledge",  # KNOWLEDGE, SEARCH
    "search": "knowledge",
    "code": "code",  # CODE, EXECUTE, FILE
    "execute": "code",
    "file": "code",
    "task": "task",  # TASK, COMMAND, SYSTEM
    "command": "task",
    "system": "task",
    "creative": "creative",  # CREATIVE, OPINION
    "opinion": "creative",
    "greeting": "social",  # GREETING, REFLEX
    "reflex": "social",
    "vision": "media",  # VISION, AUDIO
    "audio": "media",
    # "civil" stays its own bucket: it is a domain, not a phrasing style.
    "civil": "civil",
}


def topic_bucket(text: str) -> str:
    """The coarse topic of the user's message, or ``"unknown"``.

    Uses the existing deterministic `QueryClassifier` (its ``_ed3n`` attribute is
    stored but never consulted), so this adds no model and no second opinion
    about what the message is. A classifier failure is a missing label: the
    caller writes ``"unknown"`` rather than guessing one from the text.
    """
    stripped = (text or "").strip()
    if not stripped:
        return "unknown"
    try:
        from ai.core.query_classifier import QueryClassifier

        label = QueryClassifier().classify(stripped).primary_type.value
    except Exception as exc:  # a missing label must not cost a served answer
        logger.debug("turn observation: topic unavailable: %s", exc)
        return "unknown"
    return _TOPIC_BUCKETS.get(label, "other")


def state_vector() -> Optional[Dict[str, Any]]:
    """The observable AL state at this moment, or None when it cannot be read.

    Read through `get_al_state()` (the contract's only read path) so the log and
    the prompt can never disagree about what the organism's state was.
    """
    try:
        from core.life.al_state import get_al_state

        snapshot = get_al_state().as_dict()
    except Exception as exc:  # an unreadable state is a missing observation, not a crash
        logger.debug("turn observation: AL state unavailable: %s", exc)
        return None
    return {field: snapshot.get(field) for field in STATE_FIELDS}


def _session_hash(session_id: str) -> str:
    """A stable join key. Not anonymisation: whoever holds the id can recompute it."""
    return hashlib.sha256(f"angela-turn:{session_id}".encode("utf-8")).hexdigest()[:16]


def build_record(
    *,
    session_id: str,
    user_message: str,
    response_text: str,
    source: str,
    state: Optional[Mapping[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """One appendable record. Pure: no I/O, so it can be asserted in tests."""
    moment = now or datetime.now()
    structure = structure_signature(response_text)
    in_len = len((user_message or "").strip())
    return {
        "v": VERSION,
        "turn_id": uuid.uuid4().hex,
        "session": _session_hash(session_id or "unknown"),
        "day": moment.date().isoformat(),
        "state": dict(state) if state is not None else state_vector(),
        "user_move": classify_user_move(user_message),
        "source": source or "unknown",
        "in_len": in_len,
        "in_len_bucket": length_bucket(in_len),
        "topic": topic_bucket(user_message),
        "out_len": structure["chars"],
        "out_len_bucket": structure["bucket"],
        "skeleton": structure["skeleton"],
        "skeleton_sig": structure["signature"],
        "consent": 1,
    }


def record_turn(
    *,
    session_id: str,
    user_message: str,
    response_text: str,
    source: str,
    state: Optional[Mapping[str, Any]] = None,
    path: Optional[Path] = None,
    now: Optional[datetime] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[Path]:
    """Append one observation. Returns the file written, or None when disabled.

    Off by default, and a failure here must never break the answer that was
    already produced — callers may treat the return value as advisory.
    """
    if not observation_enabled(environ):
        return None
    record = build_record(
        session_id=session_id,
        user_message=user_message,
        response_text=response_text,
        source=source,
        state=state,
        now=now,
    )
    target = path or (observation_dir(environ) / f"turns-{record['day']}.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return target
