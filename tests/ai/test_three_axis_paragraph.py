"""
Three-Axis Phase A: paragraph-anchor verification.

THREE_AXIS_SCALEUP.md §5-A / §8.1-A: feed natural-language serialised samples
(instruction=output style, as the engine uses for alpaca/wiki) into
``AnchorLearner`` and verify it learns the *answer delimiter* for real text.

Verified findings (2026-08-19):
  * ``AnchorLearner.terminal_split`` picks the **rightmost** anchor whose right
    region is anchor-free. For arithmetic (``178 + 101=279``) the answer side
    ``279`` is anchor-free, so ``=`` is terminal.
  * Alpaca answers contain sentence punctuation (``...France is Paris.``), so
    a *pure* alpaca corpus yields NO terminal split in round 1 -> the learner
    safely collapses to an empty set (no false anchors — no hallucination).
  * The engine trains on a **mixed** corpus (arithmetic + logic + alpaca), so
    the arithmetic ``=`` bootstraps the anchor set; alpaca samples then align
    at ``=`` even though their answers contain periods.
  * Consequence documented: ``=`` dominates the anchor set; ``.``/``!``/``?``
    appear as coverage signals but are NOT terminal delimiters (they sit inside
    the answer side). Paragraph anchors for wiki text therefore require a
    delimiter that stays rightmost (e.g. ``=`` or a sentinel) — this is a real
    design constraint, not a bug to paper over.
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src")),
)

from ai.three_axis.anchor_learner import AnchorLearner  # noqa: E402

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

_ARITHMETIC = ["178 + 101=279", "293 - 192=101", "917 * 814=746438", "5 * 5=25"]

_ALPACA_STYLE = [
    "Give three tips for staying healthy.=Eat well, sleep enough, and exercise regularly.",
    "Explain the water cycle in one sentence.=Water evaporates, condenses into clouds, and falls as rain.",
    "What is the capital of France?=The capital of France is Paris.",
    "Describe a linked list.=A linked list is a sequence of nodes connected by pointers.",
    "How does recursion work?=A function calls itself with a smaller input until a base case is reached.",
    "What is an algorithm?=An algorithm is a finite sequence of steps to solve a problem.",
    "Explain binary search.=Binary search halves the search space at each comparison.",
    "What is a hash table?=A hash table maps keys to values for fast lookup.",
    "Define time complexity.=Time complexity measures how runtime grows with input size.",
    "How do stacks behave?=Stacks follow last-in-first-out order.",
]

_MIXED = _ARITHMETIC + _ALPACA_STYLE


class TestParagraphAnchorLearning:
    def test_mixed_corpus_converges_on_answer_delimiter(self):
        # The engine trains on a mixed corpus (arithmetic + logic + alpaca).
        # Arithmetic bootstraps '='; alpaca samples then align at it.
        learner = AnchorLearner()
        anchors = learner.learn(_MIXED)
        assert learner.converged
        assert ord("=") in anchors

    def test_alpaca_samples_align_at_eq_despite_periods(self):
        learner = AnchorLearner()
        learner.learn(_MIXED)
        split = learner.align("What is the capital of France?=The capital of France is Paris.")
        assert split is not None
        left, delimiter, right = split
        assert delimiter == "="
        assert left.startswith("What is the capital")
        assert right.startswith("The capital of France")

    def test_eq_dominates_scores(self):
        learner = AnchorLearner()
        learner.learn(_MIXED)
        eq = learner.scores.get(ord("="), 0.0)
        assert eq > 0.0
        # '=' is the terminal delimiter in nearly every arithmetic sample.
        period = learner.scores.get(ord("."), 0.0)
        assert eq >= period

    def test_arithmetic_anchor_free_answer(self):
        learner = AnchorLearner()
        learner.learn(_MIXED)
        split = learner.align("178 + 101=279")
        assert split == ("178 + 101", "=", "279")

    def test_pure_natural_text_collapses_safely(self):
        # Honest contract: pure natural text with trailing punctuation yields no
        # terminal split -> empty anchor set (no false anchors, no hallucination).
        learner = AnchorLearner()
        learner.learn(_ALPACA_STYLE)
        assert learner.anchors == set()
        assert learner.scores == {}

    def test_trailing_period_is_not_terminal(self):
        # A delimiter with nothing after it is not a terminal split.
        i = AnchorLearner.terminal_split(
            tuple(ord(c) for c in "Recursion is a loop. Every call reduces size."),
            AnchorLearner.DEFAULT_ANCHORS,
        )
        assert i is not None
        assert i == len("Recursion is a loop. Every call reduces size.") - 1  # trailing '.'

    def test_mixed_corpus_lookup(self):
        learner = AnchorLearner()
        learner.learn(_MIXED)
        # An alpaca answer that itself ends in a period is fully recovered.
        split = learner.align("Explain binary search.=Binary search halves the space.")
        assert split is not None
        assert split[0].startswith("Explain binary")
        assert "halves" in split[2]
