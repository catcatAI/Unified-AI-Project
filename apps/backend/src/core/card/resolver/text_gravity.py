"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Text Gravity Field — computes physics-based attraction of conflict
resolutions toward a card's core trait.
"""

import logging
import math
from collections import Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

GRAVITATIONAL_CONSTANT = 1.0
SOFTENING = 0.01
REPULSION_DECAY = 0.9
ENTROPY_STRENGTH = 0.05


def _ngram_jaccard_distance(a: str, b: str, n: int = 3) -> float:
    """Ngram jaccard distance."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    a_ngrams = {a[i:i + n] for i in range(len(a) - n + 1)}
    b_ngrams = {b[i:i + n] for i in range(len(b) - n + 1)}
    if not a_ngrams and not b_ngrams:
        return 0.0
    intersection = a_ngrams & b_ngrams
    union = a_ngrams | b_ngrams
    jaccard = len(intersection) / len(union) if union else 0.0
    return 1.0 - jaccard


class TextGravityField:
    """
    Text Gravity Field — uses physics-based attraction to naturally pull
    conflict resolutions toward a card's core trait.

    Gravity score = G * trait_mass / (semantic_distance^2 + softening)
    """

    def __init__(self, g: float = GRAVITATIONAL_CONSTANT, softening: float = SOFTENING):
        self.g = g
        self.softening = softening
        self._recent_choices: Counter = Counter()

    def compute_gravity(
        self,
        core_trait: str,
        candidates: List[str],
        trait_mass: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """Compute gravity."""
        if not core_trait or not candidates:
            return [(c, 0.0) for c in candidates]

        mass = trait_mass if trait_mass is not None else len(core_trait) / 10.0
        scored: List[Tuple[str, float]] = []

        for candidate in candidates:
            distance = _ngram_jaccard_distance(core_trait, candidate)
            gravity = self.g * mass / ((distance ** 2) + self.softening)
            repulsion = self._repulsion_factor(candidate)
            entropy = self._entropy_bonus(candidate, candidates)
            score = gravity - repulsion + entropy
            scored.append((candidate, max(0.0, score)))

        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            self._recent_choices[scored[0][0]] += 1
        return scored

    def _repulsion_factor(self, candidate: str) -> float:
        """Repulsion factor."""
        count = self._recent_choices.get(candidate, 0)
        if count == 0:
            return 0.0
        return (REPULSION_DECAY ** count) * count * 0.1

    def _entropy_bonus(self, candidate: str, candidates: List[str]) -> float:
        """Entropy bonus."""
        if len(candidates) <= 1:
            return 0.0
        total = sum(self._recent_choices.values()) + 1
        candidate_count = self._recent_choices.get(candidate, 0) + 1
        p = candidate_count / total
        entropy = -p * math.log2(p) if p > 0 else 0.0
        return entropy * ENTROPY_STRENGTH

    def reset_history(self) -> None:
        """Execute the reset history operation."""
        self._recent_choices.clear()


__all__ = ["TextGravityField", "_ngram_jaccard_distance"]
