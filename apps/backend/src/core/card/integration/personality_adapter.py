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
            raise RuntimeError("PersonalityManager not set")
        return self._pm

    @pm.setter
    def pm(self, manager: Any) -> None:
        self._pm = manager

    def load_card(self, card: Card, persist: bool = True) -> bool:
        if not card.core_trait and not card.tokens:
            logger.warning(f"No traits to load for {card.qualified_id}")
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
            logger.info(f"Loaded card {card.qualified_id} into PersonalityManager")
            return True
        except Exception as e:
            logger.error(f"Failed to load card {card.qualified_id}: {e}")
            return False


__all__ = ["PersonalityAdapter"]
