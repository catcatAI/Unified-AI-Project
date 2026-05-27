"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
CardRegistry — manages card instances and integrates with ServiceRegistry.
"""

import logging
from typing import Dict, List, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class CardRegistry:
    """
    Registry for Card objects keyed by qualified_id (card_id@world_line).
    """

    def __init__(self):
        self._cards: Dict[str, Card] = {}

    def add(self, card: Card) -> None:
        key = card.qualified_id or f"{card.card_id}@{card.world_line}"
        self._cards[key] = card
        logger.info(f"CardRegistry: added {key}")

    def get(self, qualified_id: str) -> Optional[Card]:
        return self._cards.get(qualified_id)

    def get_by_card_id(self, card_id: str, world_line: str) -> Optional[Card]:
        return self._cards.get(f"{card_id}@{world_line}")

    def remove(self, qualified_id: str) -> bool:
        return self._cards.pop(qualified_id, None) is not None

    def list_all(self) -> List[Card]:
        return list(self._cards.values())

    def list_by_world_line(self, world_line: str) -> List[Card]:
        return [
            card for card in self._cards.values()
            if card.world_line == world_line
        ]

    def clear(self) -> None:
        self._cards.clear()

    @property
    def count(self) -> int:
        return len(self._cards)


__all__ = ["CardRegistry"]
