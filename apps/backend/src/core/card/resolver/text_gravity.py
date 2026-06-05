"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Text Gravity Field — computes physics-based attraction of conflict
resolutions toward a card's core trait.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TextGravityField:
    """Computes physics-based gravity attraction between core trait and text candidates.

    Uses a gravitational model where core_trait acts as a mass attracting
    text candidates. Candidates with higher semantic alignment to the
    core trait receive higher gravity scores.
    """

    def __init__(self, g: float = 1.0, softening: float = 0.01, repulsion_decay: float = 0.9):
        self._g = g
        self._softening = softening
        self._repulsion_decay = repulsion_decay
        self._history: List[Dict[str, Any]] = []

    def compute_gravity(self, core_trait: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """Compute gravity scores for each candidate relative to the core trait."""
        if not candidates:
            return []

        results: List[Tuple[str, float]] = []
        for text in candidates:
            score = self._compute_single(core_trait, text)
            results.append((text, score))

        results.sort(key=lambda x: x[1], reverse=True)
        self._history.append({
            "core_trait": core_trait,
            "candidates": candidates,
            "results": results,
        })
        return results

    def _compute_single(self, core_trait: str, text: str) -> float:
        """Compute gravity between core_trait and a single text candidate."""
        overlap = len(set(core_trait) & set(text))
        trait_len = len(core_trait) or 1
        text_len = len(text) or 1
        distance = 1.0 / (overlap + self._softening + 1)
        mass = math.sqrt(trait_len * text_len)
        return (self._g * mass) / (distance + self._softening)

    def reset_history(self) -> None:
        self._history.clear()

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)


__all__ = ["TextGravityField"]
