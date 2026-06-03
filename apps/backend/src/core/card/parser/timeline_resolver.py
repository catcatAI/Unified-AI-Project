"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Timeline resolver — auto-override logic based on file timestamps.
"""

import logging
from datetime import datetime
from typing import Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class TimelineResolver:
    """
    Resolves conflicts by preferring the most recent source file timestamp.
    Does NOT override user-confirmed conflicts (CONFIRMED_KEEP).
    """

    def resolve(self, card: Card) -> Card:
        """Resolve the given request."""
        if not card.source_files:
            return card

        latest_time = max(sf.last_write_time for sf in card.source_files)
        resolved = Card(
            card_id=card.card_id,
            world_line=card.world_line,
            qualified_id=card.qualified_id,
            alternate_selves=list(card.alternate_selves),
            card_type=card.card_type,
            name=card.name,
            core_trait=card.core_trait,
            meta_data=dict(card.meta_data),
            custom_fields=dict(card.custom_fields),
            visual_data=card.visual_data,
        )

        resolved.source_files = [sf for sf in card.source_files if sf.last_write_time == latest_time]
        resolved.tokens = list(card.tokens)
        resolved.social_distance = list(card.social_distance)
        resolved.history_events = list(card.history_events)
        resolved.conflicts = [
            c for c in card.conflicts
            if not c.suppressed or c.user_intent.value > 0
        ]

        return resolved


__all__ = ["TimelineResolver"]
