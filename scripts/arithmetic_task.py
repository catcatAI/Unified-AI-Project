#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""One definition of the arithmetic task, shared by every trainer and probe.

Why this module exists
----------------------
The raw arithmetic corpus and the frozen test CSV do not agree on three things,
and each disagreement silently corrupts a run:

1. **Labels.** The test labels division as ``str(round(a / b, 4))``, so an
   exact division is ``"70.0"``. The raw corpus writes ``"70"``. A model
   trained on the corpus is asked for a surface form it was never shown, and
   the "failure" is the label mismatch, not the arithmetic.
2. **Prompt format.** The test set is all plain ``"a op b"``. The corpus is
   ~54% plain and ~46% decorated (``"a op b ="``, ``"… equals"``,
   ``"calculate …"``, ``"what is …"``). Training on the mixture while
   measuring on plain only conflates format with algorithm.
3. **Leakage.** Sixteen test problems appear verbatim in the corpus, and four
   more appear with the operands swapped for ``+``/``*``. Those rows buy
   score on the held-out distribution without teaching anything.

The rule here is single-sourced so a trainer cannot quietly use a weaker one:
``canonical_answer`` is the only label function, ``problem_key`` is the only
leak key (commutative for ``+``/``*``), and ``parse_plain``/``parse_problem``
are the only prompt parsers. Tests pin each against the frozen CSV.

This module does not read or write anything; :mod:`scripts.prepare_arithmetic_task`
owns the files.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Set, Tuple

# ``-?\d+`` for both operands, a single operator, optional whitespace, and
# nothing else. Decorated prompts deliberately do not match.
PLAIN_RE = re.compile(r"^\s*(-?\d+)\s*([+\-*/])\s*(-?\d+)\s*$")
# The two decorations that exist in the corpus. Both are *surface* variants of
# the same exercise, so they are re-expressed as a plain prompt rather than
# dropped: dropping them loses problem coverage the test set still uses (the
# two-digit-minus-one-digit shape exists only in decorated rows).
SUFFIX_RE = re.compile(r"^\s*(-?\d+)\s*([+\-*/])\s*(-?\d+)\s*(?:=|equals)\s*$", re.IGNORECASE)
PREFIX_RE = re.compile(
    r"^\s*(?:calculate|what\s+is)\s+(-?\d+)\s*([+\-*/])\s*(-?\d+)\s*$", re.IGNORECASE
)

Problem = Tuple[int, str, int]
Key = Tuple[int, str, int]


def parse_plain(prompt: str) -> Optional[Problem]:
    """Return ``(a, op, b)`` for a plain prompt, ``None`` for anything else."""
    match = PLAIN_RE.match(str(prompt or ""))
    if not match:
        return None
    return int(match.group(1)), match.group(2), int(match.group(3))


def parse_problem(prompt: str) -> Optional[Tuple[Problem, str]]:
    """Return ``((a, op, b), surface)`` for a supported prompt.

    ``surface`` is ``"plain"``, ``"suffix"`` (``… =`` / ``… equals``) or
    ``"prefix"`` (``calculate …`` / ``what is …``). Anything else — including a
    decorated prompt that hides two expressions or unrelated prose — returns
    ``None`` and is counted as unsupported by the caller. Guessing here would
    train on an expression the row does not actually ask about.
    """
    text = str(prompt or "")
    for surface, pattern in (("plain", PLAIN_RE), ("suffix", SUFFIX_RE), ("prefix", PREFIX_RE)):
        match = pattern.match(text)
        if match:
            return (int(match.group(1)), match.group(2), int(match.group(3))), surface
    return None


def canonical_prompt(problem: Problem) -> str:
    """The single surface form the clean task trains and evaluates on."""
    a, op, b = problem
    return f"{a} {op} {b}"


def canonical_answer(a: int, op: str, b: int) -> Optional[str]:
    """The label rule the **frozen test set already uses**.

    ``str(round(a / b, 4))`` is not a choice made here; it is what
    ``arithmetic_test_dataset.csv`` contains (2,000/2,000 rows agree). Division
    by zero has no label and is rejected rather than given a sentinel.
    """
    if op == "+":
        return str(a + b)
    if op == "-":
        return str(a - b)
    if op == "*":
        return str(a * b)
    if op == "/":
        if b == 0:
            return None
        return str(round(a / b, 4))
    return None


def problem_key(problem: Problem) -> Key:
    """Leak key: order-insensitive for ``+``/``*``, exact otherwise.

    ``3 + 4`` and ``4 + 3`` are the same exercise, so a test problem that
    appears in the corpus with the operands swapped is still a leak.
    """
    a, op, b = problem
    if op in "+*":
        a, b = min(a, b), max(a, b)
    return a, op, b


def test_keys(rows: Iterable[dict]) -> Set[Key]:
    """Leak keys for a frozen test split (CSV/JSON rows with ``problem``)."""
    keys: Set[Key] = set()
    for row in rows:
        problem = parse_plain(str(row.get("problem") or row.get("input") or ""))
        if problem is not None:
            keys.add(problem_key(problem))
    return keys


def leaks(problem: Problem, keys: Set[Key]) -> bool:
    return problem_key(problem) in keys


def digit_span(value: int) -> int:
    """Digits in the absolute value (``-54`` -> 2)."""
    return len(str(abs(int(value))))


def span_pairs(problems: Sequence[Problem], op: str) -> List[Tuple[int, int]]:
    """Sorted distinct ``(digits(a), digits(b))`` shapes seen for one operator."""
    return sorted({(digit_span(a), digit_span(b)) for a, o, b in problems if o == op})
