"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Timeline resolver — auto-override logic based on file timestamps.
"""

import logging
from typing import Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class TimelineResolver:
    """
    Resolves which version of a card wins based on source file timestamps.
    """

    def resolve(self, cards: list) -> Card:
        """Pick the card with the most recent source_file timestamp."""
        if not cards:
            raise ValueError("No cards to resolve")

        best = cards[0]
        best_time: Optional[float] = None
        if best.source_files:
            best_time = max(sf.last_write_time.timestamp() for sf in best.source_files)

        for card in cards[1:]:
            if not card.source_files:
                continue
            card_time = max(sf.last_write_time.timestamp() for sf in card.source_files)
            if best_time is None or card_time > best_time:
                best = card
                best_time = card_time

        return best


__all__ = ["TimelineResolver"]
