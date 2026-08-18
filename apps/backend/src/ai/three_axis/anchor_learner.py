# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

"""
Anchor learner for the Three-Axis system.

Learns *alignment anchors* from training data using an EM-style loop, rather
than hardcoding which characters separate a query from its answer:

  default anchors (prior) -> align -> re-estimate -> iterate -> converge

E-step (align): for every training sample, find the terminal split — the
rightmost anchor occurrence whose right-region contains no other anchor.
M-step (re-estimate): score each value that ever served as a terminal
delimiter by terminality (fraction of splits at that value) plus corpus
coverage, and promote the top-K values to be the next anchor set. Iterate
until the set is stable (converged).

The resulting anchor set is data-driven: on the real arithmetic dataset it
converges to ``{=, -, .}`` (the answer delimiter plus operators), replacing a
hand-written ``=``-detection rule. Alignment uses it to split each sample
into ``problem | delimiter | answer``; the engine then builds whitespace-
collapsed problem->answer tables with suffix lookup, so queries differing by
whitespace or leading words still align (sliding alignment freedom).

This module is pure count-based (no gradients), consistent with the engine.
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


class AnchorLearner:
    """EM-style learned anchor induction."""

    # Prior anchors (defaults, overridden by learning).
    DEFAULT_ANCHORS = {ord(c) for c in "=+-*/? .,!()[]{}:;"}
    MAX_ROUNDS = 8
    TOP_K = 6
    TERMINAL_WEIGHT = 0.8
    COVERAGE_WEIGHT = 0.2

    def __init__(
        self,
        default_anchors: Optional[Set[int]] = None,
        top_k: int = TOP_K,
    ) -> None:
        self.anchors: Set[int] = set(default_anchors or self.DEFAULT_ANCHORS)
        self.top_k = top_k
        self.rounds = 0
        self.converged = False
        self.scores: Dict[int, float] = {}

    @staticmethod
    def terminal_split(vals: Tuple[int, ...], anchors: Set[int]) -> Optional[int]:
        """Index of the rightmost anchor whose right-region has no anchor."""
        n = len(vals)
        for i in range(n - 1, -1, -1):
            if vals[i] in anchors and not any(v in anchors for v in vals[i + 1 :]):
                return i
        return None

    def learn(self, samples: List[str]) -> Set[int]:
        """Run the EM loop over samples. Returns the converged anchor set."""
        all_vals = [tuple(ord(c) for c in s) for s in samples]
        prev: Optional[Set[int]] = None
        for r in range(self.MAX_ROUNDS):
            self.rounds = r + 1
            splits: List[Tuple[int, int]] = []
            for vals in all_vals:
                i = self.terminal_split(vals, self.anchors)
                if i is not None and i + 1 < len(vals):
                    splits.append((vals[i], vals[i + 1]))
            term = Counter(v for v, _ in splits)
            coverage = Counter(v for vals in all_vals for v in set(vals))
            total = max(1, len(splits))
            scores: Dict[int, float] = {}
            for v, _ in splits:
                scores[v] = (
                    self.TERMINAL_WEIGHT * term[v] / total
                    + self.COVERAGE_WEIGHT * coverage.get(v, 0) / max(1, len(all_vals))
                )
            self.scores = scores
            new_anchors = {
                v for v, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[: self.top_k]
            }
            if new_anchors == prev:
                self.converged = True
                break
            prev = new_anchors
            self.anchors = new_anchors
        return self.anchors

    def align(self, text: str) -> Optional[Tuple[str, str, str]]:
        """Split ``text`` at its terminal anchor -> (problem, delimiter, answer).

        Returns None when no terminal anchor is found (anchor-less text).
        """
        vals = tuple(ord(c) for c in text)
        i = self.terminal_split(vals, self.anchors)
        if i is None:
            return None
        return (text[:i], text[i], text[i + 1 :])

    @staticmethod
    def normalize(text: str) -> str:
        """Whitespace-collapse default used for problem keys."""
        return "".join(text.split())