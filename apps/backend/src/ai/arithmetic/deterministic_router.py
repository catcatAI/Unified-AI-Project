# =============================================================================
# ANGELA-MATRIX: [L3] [β] [A] [L3]
# =============================================================================
"""
Single source for all deterministic compute routing.

Before: 3 copies of the same 5-route chain
  - ai/unified_engine/unified_engine.py: _try_math, _try_logic (2 routes)
  - ai/ed3n/ed3n_engine.py: _try_math_eval, _try_logic_eval, _try_knowledge, _try_reasoning (4 routes)
  - ai/garden/garden_engine.py: _try_math, _try_knowledge, _try_reasoning, _try_math_eval (4 routes)
  plus DictionaryLayer.route_math / VectorDictionary.route_math wrappers

After: this file is the single source. All engines delegate here.
The statistical core (FixedSizeCore) is NOT part of this router — it is the
learned model, handled separately.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def try_math(text: str) -> Optional[str]:
    """Deterministic math via MathVerifier + gate-learner fallback.

    Delegates to the project's single source of truth for arithmetic
    (services.math_verifier.evaluate_math) and, on miss, to the
    arithmetic-learner gate router for XNOR / numeric-bit gaps.
    """
    try:
        from services.math_verifier import evaluate_math

        result = evaluate_math(text.rstrip("? ").rstrip("=").rstrip(" "))
        if result is not None:
            return result
    except Exception as _e:
        logger.debug("evaluate_math failed: %s", _e)
    try:
        from ai.arithmetic.gate_router import try_logic_gate

        result = try_logic_gate(text)
        if result is not None:
            # gate_router returns "0"/"1" for N OP M bit forms
            cleaned = text.rstrip("? ").rstrip("=").rstrip(" ")
            return f"{cleaned}={result}"
    except Exception as exc:
        logger.debug("deterministic math gate fallback failed for %r: %s", text, exc)
    return None


def try_logic(text: str) -> Optional[str]:
    """Deterministic boolean logic via evaluate_logic truth tables."""
    try:
        from services.math_verifier import evaluate_logic

        cleaned = text.rstrip("? ").rstrip("=").rstrip(" ")
        result = evaluate_logic(cleaned)
        if result is not None:
            if "=" in str(result):
                return str(result)
            return f"{cleaned}={result}"
    except Exception:
        pass
    return None


def try_knowledge(text: str) -> Optional[str]:
    """Curated factual recall via ai.knowledge_base.route_knowledge."""
    try:
        from ai.knowledge_base import route_knowledge

        return route_knowledge(text)
    except Exception as exc:
        logger.debug("knowledge routing failed for %r: %s", text, exc)
        return None


def try_reasoning(text: str) -> Optional[str]:
    """Symbolic reasoning via ai.symbolic_reasoner.route_reasoning."""
    try:
        from ai.symbolic_reasoner import route_reasoning

        return route_reasoning(text)
    except Exception as exc:
        logger.debug("reasoning routing failed for %r: %s", text, exc)
        return None


def try_deterministic(text: str) -> Optional[str]:
    """Try all deterministic routes in priority order. First hit wins."""
    for fn in (try_math, try_logic, try_knowledge, try_reasoning):
        result = fn(text)
        if result is not None:
            return result
    return None
