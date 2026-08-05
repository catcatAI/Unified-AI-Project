# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [B] [L5]
# =============================================================================
"""Runtime bridge: let the learned logic-gate capability reach the dict layer.

The ED3N/GARDEN dictionary ``route_math`` hook is the canonical "compute"
entry point that dialogue reaches. It delegates arithmetic to
``MathVerifier.evaluate_math`` (the exact deterministic single source of truth)
— so the learner must NEVER duplicate the engine's in-scope arithmetic.

This module is the *only* sanctioned place the learned capability is consulted
at runtime: it is a last-resort fallback that fires strictly when BOTH of the
deterministic engine's evaluators return ``None`` (i.e. genuinely out of the
engine's scope). Today that means **XNOR** — the one boolean gate
``evaluate_logic`` cannot express — plus the numeric ``N OP M`` bit forms the
engine's boolean-language path does not own (it answers ``1 AND 1`` as the
boolean ``"true"`` rather than the bit ``1``).

The learner is not hard-wired into any engine constructor; it is registered
into a module-level holder (by the offline training pipeline, or a runtime
boot loader). With no learner registered, every call is a no-op preserving the
exact engine-only behaviour.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Sparse ``N OP M`` numeric-bitwise form (allow optional trailing =/？). The
# gate words are the ones the learner supports; XNOR is the engine gap.
_NUM_GATE_RE = re.compile(
    r"(?P<a>\d+)\s*" r"(?P<op>AND|OR|XOR|NAND|NOR|XNOR|NOT)\b" r"(?:\s*(?P<b>\d+))?\s*=?\s*[？?]?"
)

_LEARNER: Optional[Any] = None


def set_arithmetic_learner(learner: Optional[Any]) -> None:
    """Register (or clear) the ArithmeticLearner the router may consult."""
    global _LEARNER
    _LEARNER = learner


def get_arithmetic_learner() -> Optional[Any]:
    """Return the registered ArithmeticLearner, or None."""
    return _LEARNER


def try_logic_gate(text: str) -> Optional[str]:
    """Answer a numeric bitwise gate with the learned gates, engine-first.

    Fires only when the text parses as ``N OP M`` AND neither the arithmetic
    nor the boolean evaluator answers it — so the learner fills genuine
    engine-scope gaps (XNOR, numeric bit forms) and never shadows or duplicates
    the deterministic engine's explicit math. Returns a ``"0"``/``"1"`` string,
    or None when not applicable / no learner registered / untrained.
    """
    learner = _LEARNER
    if learner is None:
        return None
    m = _NUM_GATE_RE.search(text.strip())
    if not m:
        return None
    op = m.group("op")
    a = int(m.group("a"))
    b = int(m.group("b")) if m.group("b") else 0

    from services.math_verifier import evaluate_logic, evaluate_math

    # Engine-first, always: never compete with the exact deterministic sources.
    if evaluate_math(text) is not None:
        return None
    if evaluate_logic(text) is not None:
        return None

    try:
        bit = learner.predict_logic_gate(op, a, b)
    except Exception as e:  # noqa: BLE001 - defensive last resort
        logger.debug("logic-gate fallback failed for %r: %s", text, e)
        return None
    return str(int(bit))
