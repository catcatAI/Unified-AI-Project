"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Memory adapter — stores Card data into HAMMemoryManager.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class MemoryAdapter:
    """
    Adapts Card objects for storage in HAMMemoryManager.
    Converts Card to dict and delegates to store_experience().
    """

    def __init__(self, ham_manager: Optional[Any] = None):
        self._ham = ham_manager

    @property
    def ham(self):
        if self._ham is None:
            raise RuntimeError("HAMMemoryManager not set")
        return self._ham

    @ham.setter
    def ham(self, manager: Any) -> None:
        self._ham = manager

    async def store_card(self, card: Card, is_strategic: bool = False) -> Optional[str]:
        """Store a card."""
        card_dict = self._card_to_dict(card)
        metadata = {
            "world_line": card.world_line,
            "card_type": card.card_type.name if card.card_type else None,
            "core_trait": card.core_trait,
            "qualified_id": card.qualified_id,
            "source": "card_import_pipeline",
        }
        memory_id = await self.ham.store_experience(
            raw_data=card_dict,
            data_type="character_card",
            metadata=metadata,
            is_strategic=is_strategic,
        )
        if memory_id:
            logger.info(f"Stored card {card.qualified_id} as {memory_id}")
        else:
            logger.warning(f"Failed to store card {card.qualified_id}", exc_info=True)
        return memory_id

    async def store_batch(
        self, cards: list, is_strategic: bool = False
    ) -> Dict[str, Optional[str]]:
        """Store a batch."""
        results: Dict[str, Optional[str]] = {}
        for card in cards:
            mid = await self.store_card(card, is_strategic=is_strategic)
            results[card.qualified_id] = mid
        return results

    def _card_to_dict(self, card: Card) -> dict:
        base = asdict(card)
        base["card_type"] = card.card_type.name if card.card_type else None
        base["conflicts"] = [
            {
                "type": c.type.name,
                "dimension": c.dimension,
                "description": c.description,
                "resolution": c.resolution,
                "user_intent": c.user_intent.name,
                "suppressed": c.suppressed,
            }
            for c in card.conflicts
        ]
        return base


__all__ = ["MemoryAdapter"]
