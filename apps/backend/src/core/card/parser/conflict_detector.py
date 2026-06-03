"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Conflict detector — detects physical, numerical, and tone conflicts across cards.
"""

import logging
from typing import List, Tuple

from core.card.card_types import Card, Conflict, ConflictType, IntentFlag

logger = logging.getLogger(__name__)


class ConflictDetector:
    """
    Three-dimensional conflict detection:
    1. Physical — incompatible world_line or card_type
    2. Numerical — token strength out of range
    3. Tone — core_trait mismatch across sources
    """

    def detect(self, card: Card) -> List[Conflict]:
        """Detect patterns in the input."""
        conflicts: List[Conflict] = []
        conflicts.extend(self._detect_physical(card))
        conflicts.extend(self._detect_numerical(card))
        conflicts.extend(self._detect_tone(card))
        return conflicts

    def detect_between(self, cards: List[Card]) -> List[Tuple[str, str, Conflict]]:
        """Execute the detect between operation."""
        cross_conflicts: List[Tuple[str, str, Conflict]] = []
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                a, b = cards[i], cards[j]
                if a.world_line == b.world_line and a.card_id == b.card_id:
                    continue
                if a.card_type != b.card_type:
                    continue
                if a.core_trait and b.core_trait and a.core_trait != b.core_trait:
                    cross_conflicts.append((
                        a.qualified_id, b.qualified_id,
                        Conflict(
                            type=ConflictType.MULTIVERSE,
                            dimension="tone",
                            description=f"Core trait differs: '{a.core_trait}' vs '{b.core_trait}'",
                        )
                    ))
        return cross_conflicts

    def _detect_physical(self, card: Card) -> List[Conflict]:
        conflicts = []
        for sf in card.source_files:
            if not sf.path.endswith(".gdoc") and not sf.path.endswith(".txt"):
                conflicts.append(Conflict(
                    type=ConflictType.HARD_ERROR,
                    dimension="format",
                    description=f"Unsupported source format: {sf.path}",
                ))
        return conflicts

    def _detect_numerical(self, card: Card) -> List[Conflict]:
        conflicts = []
        for token in card.tokens:
            if token.strength < 0.0 or token.strength > 10.0:
                conflicts.append(Conflict(
                    type=ConflictType.HARD_ERROR,
                    dimension="numerical",
                    description=f"Token '{token.name}' strength {token.strength} out of range [0, 10]",
                ))
        return conflicts

    def _detect_tone(self, card: Card) -> List[Conflict]:
        conflicts = []
        if card.source_files and len(card.source_files) > 1:
            core_traits = set()
            if card.core_trait:
                core_traits.add(card.core_trait)
            if len(core_traits) > 1:
                conflicts.append(Conflict(
                    type=ConflictType.NARRATIVE_DEVICE,
                    dimension="tone",
                    description=f"Multiple core traits across sources: {core_traits}",
                ))
        return conflicts


__all__ = ["ConflictDetector"]
