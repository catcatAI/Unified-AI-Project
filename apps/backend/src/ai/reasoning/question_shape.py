# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [B] [L3]
# LAYER: surface
# =============================================================================
"""Question-shape predicates: what a question is actually asking for.

A ``why`` question asks for an **explanation**. A bare attribute ("blue")
answers *what colour*, not *why*; a topically retrieved sentence answers
*about what*, not *why*. Both look fluent and both are non-answers.

The three paths that used to disagree about this shared no predicate:

- ``ai.knowledge_base.route_knowledge`` (curated attribute lookup, then the
  offline encyclopedia),
- ``ai.unified_engine.unified_engine._try_semantic_qa`` (learned retrieval),
- ``services.llm.router._try_knowledge`` (generator deferral).

Keeping the predicate in one module means "causal question needs causal
evidence" cannot drift into three slightly different rules. This module only
classifies text; it does not answer anything.
"""

from __future__ import annotations

import re

# Same question shape the router already used to defer causal questions to a
# generator. Kept identical so the native path and the generator path agree.
WHY_QUESTION_RE = re.compile(r"為什麼|为什么|為何|为何|原因|緣故|缘故|\bwhy\b", re.IGNORECASE)

# Explanation markers. Deliberately conservative: "since" and "so" are NOT
# here because they are overwhelmingly temporal ("since 1994") or idiomatic
# ("so blue"), and a false pass re-opens the confident-non-answer hole.
_CAUSAL_ZH = (
    "因為",
    "因为",
    "由於",
    "由于",
    "所以",
    "因此",
    "因而",
    "導致",
    "导致",
    "造成",
    "使得",
    "致使",
    "原因是",
    "主因",
    "緣故",
    "缘故",
    "是由於",
    "是由于",
    "是因為",
    "是因为",
)

_CAUSAL_EN = re.compile(
    r"\b(because|due to|owing to|caused by|causes?|as a result|therefore|thus|"
    r"leads? to|results? in|explains?|explanation|reason)\b",
    re.IGNORECASE,
)


def is_why_question(text: str) -> bool:
    """True when the text asks for a cause/explanation rather than a value."""
    return bool(text) and isinstance(text, str) and WHY_QUESTION_RE.search(text) is not None


def has_causal_evidence(text: str) -> bool:
    """True when the answer states a cause, not merely a related value.

    This checks the answer *sentence*, never the question: a question that
    contains ``why`` must not make its own retrieval look like an explanation.
    """
    if not text or not isinstance(text, str):
        return False
    if any(marker in text for marker in _CAUSAL_ZH):
        return True
    return _CAUSAL_EN.search(text) is not None


__all__ = ["WHY_QUESTION_RE", "is_why_question", "has_causal_evidence"]
