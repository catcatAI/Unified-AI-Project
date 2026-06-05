"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Import quality checker — three-dimension scoring for card import quality.
"""

import logging
from dataclasses import dataclass
from typing import List

from core.card.card_types import Card, ConflictType, IntentFlag

logger = logging.getLogger(__name__)

WEIGHT_STRUCTURAL = 0.3
WEIGHT_SEMANTIC = 0.4
WEIGHT_CONFLICT = 0.3
PASS_THRESHOLD = 0.7

STRUCTURAL_FIELDS = ["card_id", "name", "world_line", "core_trait"]


@dataclass
class QualityScore:
    """Three-dimension quality score for an imported card."""

    structural: float = 0.0
    semantic: float = 0.0
    conflict: float = 0.0

    @property
    def total(self) -> float:
        """Weighted total score."""
        return (
            WEIGHT_STRUCTURAL * self.structural
            + WEIGHT_SEMANTIC * self.semantic
            + WEIGHT_CONFLICT * self.conflict
        )

    @property
    def passed(self) -> bool:
        """Whether the total score meets the pass threshold."""
        return self.total >= PASS_THRESHOLD


class ImportQualityChecker:
    """
    Scores card import quality across three dimensions:
    - Structural: how many fields are populated
    - Semantic: entity retention from original text
    - Conflict: resolution status of conflicts
    """

    def check(self, original_text: str, card: Card) -> QualityScore:
        """Compute quality scores for the given card against original text."""
        structural = self._score_structural(card)
        semantic = self._score_semantic(original_text, card)
        conflict = self._score_conflict(card)
        return QualityScore(structural=structural, semantic=semantic, conflict=conflict)

    def _score_structural(self, card: Card) -> float:
        """Score based on how many core fields are populated."""
        filled = 0
        for field in STRUCTURAL_FIELDS:
            val = getattr(card, field, None)
            if val:
                filled += 1
        if card.tokens:
            filled += 1
        total_fields = len(STRUCTURAL_FIELDS) + 1
        return filled / total_fields

    def _score_semantic(self, original_text: str, card: Card) -> float:
        """Score based on entity retention from original text."""
        if not original_text:
            if card.name or card.core_trait or card.tokens:
                return 1.0
            return 0.0

        text_lower = original_text.lower()
        found = 0
        total = 0

        entities = []
        if card.name:
            entities.append(card.name)
        if card.core_trait:
            entities.append(card.core_trait)
        for t in card.tokens:
            entities.append(t.name)

        for entity in entities:
            total += 1
            if entity.lower() in text_lower:
                found += 1

        if total == 0:
            return 0.0
        return found / total

    def _score_conflict(self, card: Card) -> float:
        """Score based on conflict resolution status."""
        if not card.conflicts:
            return 1.0

        resolved = 0
        for c in card.conflicts:
            if c.resolution is not None:
                resolved += 1
            elif c.suppressed and c.user_intent == IntentFlag.CONFIRMED_KEEP:
                resolved += 1

        return resolved / len(card.conflicts)


__all__ = ["ImportQualityChecker", "QualityScore"]
