"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Import quality checker — three-dimension scoring for card import quality.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.card.card_types import Card, IntentFlag
from core.card.resolver.text_gravity import _ngram_jaccard_distance

logger = logging.getLogger(__name__)

STRUCTURAL_WEIGHT = 0.3
SEMANTIC_WEIGHT = 0.4
CONFLICT_WEIGHT = 0.3

PASS_THRESHOLD = 0.75
WARN_THRESHOLD = 0.50

ENTITY_PATTERN = re.compile(r"[A-Z\u4e00-\u9fff]{2,}")


class QualityScore:
    def __init__(self, structural: float = 0.0, semantic: float = 0.0,
                 conflict: float = 0.0):
        self.structural = structural
        self.semantic = semantic
        self.conflict = conflict
        self.total = (
            STRUCTURAL_WEIGHT * structural
            + SEMANTIC_WEIGHT * semantic
            + CONFLICT_WEIGHT * conflict
        )
        self.passed = self.total >= PASS_THRESHOLD


class ImportQualityChecker:
    """
    Three-dimension import quality checker.
    """

    def check(self, original_text: str, card: Card) -> QualityScore:
        structural = self._structural_score(card)
        semantic = self._semantic_score(original_text, card)
        conflict = self._conflict_score(card)
        return QualityScore(structural, semantic, conflict)

    def _structural_score(self, card: Card) -> float:
        total = 0
        matched = 0

        fields = [
            ("card_id", bool(card.card_id)),
            ("name", bool(card.name)),
            ("world_line", bool(card.world_line)),
            ("core_trait", bool(card.core_trait)),
        ]
        total += len(fields)
        matched += sum(1 for _, present in fields if present)

        if card.tokens:
            matched += 1
        total += 1

        if card.source_files:
            matched += 1
        total += 1

        return matched / total if total > 0 else 0.0

    def _semantic_score(self, original: str, card: Card) -> float:
        if not original.strip():
            return 1.0 if card.name or card.core_trait else 0.0

        card_text = f"{card.name} {card.core_trait} {' '.join(t.name for t in card.tokens)}"
        if not card_text.strip():
            return 0.0

        ngram_score = 1.0 - _ngram_jaccard_distance(original, card_text, n=4)

        orig_entities = set(ENTITY_PATTERN.findall(original))
        card_entities = set(ENTITY_PATTERN.findall(card_text))
        if orig_entities:
            entity_retention = len(orig_entities & card_entities) / len(orig_entities)
        else:
            entity_retention = 1.0

        return ngram_score * 0.7 + entity_retention * 0.3

    def _conflict_score(self, card: Card) -> float:
        total = len(card.conflicts)
        if total == 0:
            return 1.0

        correctly_resolved = sum(
            1 for c in card.conflicts
            if c.resolution and not c.suppressed
        )
        correctly_kept = sum(
            1 for c in card.conflicts
            if c.suppressed and c.user_intent == IntentFlag.CONFIRMED_KEEP
        )
        return (correctly_resolved + correctly_kept) / total


__all__ = ["ImportQualityChecker", "QualityScore"]
