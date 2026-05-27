"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Roleplay engine — loads Card persona and enables roleplay via PersonalityManager.
"""

import logging
from typing import Optional

from core.card.card_types import Card
from core.card.integration.personality_adapter import PersonalityAdapter

logger = logging.getLogger(__name__)


class RoleplayEngine:
    """
    Enables roleplay by loading a Card into PersonalityManager.
    The personality is set once, then all subsequent dialogue naturally
    reflects the card's persona through TextGravityField attraction.
    """

    def __init__(self, adapter: Optional[PersonalityAdapter] = None):
        self.adapter = adapter or PersonalityAdapter()
        self._active_card: Optional[Card] = None

    @property
    def active_card(self) -> Optional[Card]:
        return self._active_card

    def activate(self, card: Card, persist: bool = True) -> bool:
        ok = self.adapter.load_card(card, persist=persist)
        if ok:
            self._active_card = card
            logger.info(f"Roleplay activated: {card.qualified_id}")
        return ok

    def deactivate(self) -> None:
        self._active_card = None
        logger.info("Roleplay deactivated")


__all__ = ["RoleplayEngine"]
