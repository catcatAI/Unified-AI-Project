# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [B] [L5]
# =============================================================================
"""Arithmetic learning package.

Implements the counting-based digit representation (research §3.1/§3.3) and an
autonomous arithmetic-learning loop that generates its own data when samples
are insufficient, stops when learned or unconvergeable, and can resume.

The deterministic engine (``services.math_verifier.evaluate_math``) remains the
single source of truth for numeric labels. The SNN-style learned digit module
only learns the ``digit x digit x carry_in -> (digit, carry_out)`` mapping so it
can expose the arithmetic capability learned from the deterministic truth.

Four op cells share the same proven L-BFGS-B readout: addition
(carry cell), subtraction (borrow cell), multiplication (single-digit lattice),
and boolean logic gates (closed ``{0,1}`` truth tables for
AND/OR/XOR/NAND/NOR/XNOR/NOT).
"""

from .arithmetic_learner import (
    ArithmeticLearner,
    CellSample,
    DigitRepresentation,
    LogicSample,
    LoopSnapshot,
    MulCellSample,
    SubCellSample,
    _label_add,
    _label_mul,
    _label_sub,
)

__all__ = [
    "ArithmeticLearner",
    "CellSample",
    "DigitRepresentation",
    "LogicSample",
    "LoopSnapshot",
    "MulCellSample",
    "SubCellSample",
    "_label_add",
    "_label_mul",
    "_label_sub",
]
