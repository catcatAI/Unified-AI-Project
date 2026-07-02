"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Personality adapter — loads Card traits into PersonalityManager.
"""

import logging
from typing import Any, Dict, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class PersonalityAdapter:
    """
    Adapts Card objects for PersonalityManager.
    Uses apply_personality_adjustment() to inject card traits.
    """

    def __init__(self, personality_manager: Optional[Any] = None):
        self._pm = personality_manager

    @property
    def pm(self):
        if self._pm is None:
            logger.warning("PersonalityManager not set — personality_adapter is disabled")
            return None
        return self._pm

    @pm.setter
    def pm(self, manager: Any) -> None:
        self._pm = manager

    def load_card(self, card: Card, persist: bool = True) -> bool:
        """Load state from storage."""
        if self._pm is None:
            logger.warning("PersonalityManager not set, cannot load card %s", card.qualified_id)
            return False
        if not card.core_trait and not card.tokens:
            logger.warning("No traits to load for %s", card.qualified_id)
            return False

        adjustment: Dict[str, Any] = {}
        if card.name:
            adjustment["display_name"] = card.name
        if card.core_trait:
            adjustment["core_trait"] = card.core_trait
        if card.tokens:
            adjustment["traits"] = {
                t.name: t.strength for t in card.tokens
            }
        if card.meta_data:
            adjustment["meta"] = dict(card.meta_data)

        try:
            self.pm.apply_personality_adjustment(adjustment, persist=persist)
            logger.info("Loaded card %s into PersonalityManager", card.qualified_id)
            return True
        except Exception as e:
            logger.error("Failed to load card %s: %s", card.qualified_id, e, exc_info=True)
            return False


__all__ = ["PersonalityAdapter"]
