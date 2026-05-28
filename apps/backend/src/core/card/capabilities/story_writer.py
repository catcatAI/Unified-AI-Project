"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Story writer — builds narrative from Card history_events using DocumentBuilder.
"""

import logging
from typing import Any, Dict, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class StoryWriter:
    """
    Writes stories from Card.history_events.
    Delegates to DocumentBuilder.build() for generation.
    """

    def __init__(self, document_builder: Optional[Any] = None):
        self._builder = document_builder

    @property
    def builder(self):
        if self._builder is None:
            raise RuntimeError("DocumentBuilder not set")
        return self._builder

    @builder.setter
    def builder(self, value: Any) -> None:
        self._builder = value

    async def write(self, card: Card, query: str = "") -> Optional[str]:
        if not card.history_events:
            logger.warning(f"No history events for {card.qualified_id}", exc_info=True)
            return None

        context: Dict[str, Any] = {
            "card_name": card.name,
            "core_trait": card.core_trait,
            "world_line": card.world_line,
            "events": [
                {"time": e.timestamp.isoformat(), "title": e.title, "desc": e.description}
                for e in card.history_events
            ],
            "tokens": {t.name: t.strength for t in card.tokens},
        }
        if not query:
            query = f"Write a story about {card.name} based on their history"
        result = await self.builder.build(query=query, state_context=context)
        return result.full_text if result else None


__all__ = ["StoryWriter"]
