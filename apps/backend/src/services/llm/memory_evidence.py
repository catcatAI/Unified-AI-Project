# =============================================================================
# ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
# =============================================================================
"""Memory hits are *evidence* for a generator, not a reply to the user.

A memory layer can say two different things:

1. "this is what the user told me" — a record, with an owner and a time;
2. "here is the answer" — a sentence in the assistant's voice.

Only the second is a reply. When a backend that can generate is registered,
the memory layer must hand over (1) and let the generator write (2): the
reply then carries the model's wording and the memory stays a cited record.
When no generator exists, the extractive answer is the honest degraded mode
(the native path), and it is labelled as memory rather than dressed up as
model output.
"""

# LAYER: surface

from __future__ import annotations

from typing import Any, Dict, List, Optional

MEMORY_EVIDENCE_KEY = "memory_evidence"

# The sources are named so the prompt (and the trace) can say where the
# record came from — a taught fact, a conversation statement, or a RAG hit.
VALID_SOURCES = frozenset({"taught_facts", "conversation", "user_fact"})


def remember(context: Optional[Dict[str, Any]], text: str, source: str) -> None:
    """Publish one memory record for the generator to use.

    The record is the raw statement the user made, never the surface layer's
    formatted reply ("你剛才說過：…"): handing the frame over as evidence
    would make the model repeat the frame instead of answering.
    """
    if context is None:
        return
    clean = (text or "").strip()
    if not clean:
        return
    items = context.get(MEMORY_EVIDENCE_KEY)
    if not isinstance(items, list):
        items = []
        context[MEMORY_EVIDENCE_KEY] = items
    entry = {"text": clean, "source": source if source in VALID_SOURCES else "conversation"}
    if entry not in items:
        items.append(entry)


def collect(context: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """The records published so far (a copy; callers must not mutate ours)."""
    items = (context or {}).get(MEMORY_EVIDENCE_KEY)
    if not isinstance(items, list):
        return []
    return [dict(item) for item in items if isinstance(item, dict) and item.get("text")]


__all__ = ["MEMORY_EVIDENCE_KEY", "VALID_SOURCES", "collect", "remember"]
