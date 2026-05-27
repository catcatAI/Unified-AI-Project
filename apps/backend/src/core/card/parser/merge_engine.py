"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Merge engine — cross-file merge by qualified_id with timestamp ordering.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class MergeEngine:
    """
    Merges cards sharing the same qualified_id (card_id@world_line).
    Uses last_write_time from source_files to resolve conflicts:
    newer source wins for individual fields, but preserves user-confirmed
    conflicts (CONFIRMED_KEEP) and alternate_selves.
    """

    def merge(self, existing: Optional[Card], incoming: Card) -> Card:
        if existing is None:
            return incoming

        if existing.qualified_id != incoming.qualified_id:
            logger.warning(
                f"qualified_id mismatch: {existing.qualified_id} vs {incoming.qualified_id}"
            )
            return incoming

        merged = Card(
            card_id=existing.card_id or incoming.card_id,
            world_line=existing.world_line or incoming.world_line,
            qualified_id=existing.qualified_id,
            alternate_selves=list(set(existing.alternate_selves + incoming.alternate_selves)),
            card_type=incoming.card_type if incoming.card_type != existing.card_type else existing.card_type,
        )

        existing_time = self._latest_time(existing)
        incoming_time = self._latest_time(incoming)

        newer, older = (incoming, existing) if incoming_time >= existing_time else (existing, incoming)

        merged.name = newer.name or older.name
        merged.core_trait = newer.core_trait or older.core_trait
        merged.meta_data = {**older.meta_data, **newer.meta_data}
        merged.custom_fields = {**older.custom_fields, **newer.custom_fields}
        merged.visual_data = newer.visual_data or older.visual_data

        seen_sources = {(sf.path, sf.doc_id) for sf in existing.source_files}
        merged.source_files = list(existing.source_files)
        for sf in incoming.source_files:
            if (sf.path, sf.doc_id) not in seen_sources:
                merged.source_files.append(sf)
                seen_sources.add((sf.path, sf.doc_id))
        merged.tokens = self._merge_tokens(existing.tokens, incoming.tokens)
        merged.social_distance = self._merge_relations(existing.social_distance, incoming.social_distance)
        merged.history_events = self._merge_events(existing.history_events, incoming.history_events)
        merged.conflicts = self._merge_conflicts(existing.conflicts, incoming.conflicts)

        return merged

    def _latest_time(self, card: Card) -> datetime:
        if not card.source_files:
            return datetime.min
        return max(sf.last_write_time for sf in card.source_files)

    def _merge_tokens(self, existing: list, incoming: list) -> list:
        seen = {t.name for t in existing}
        merged = list(existing)
        for token in incoming:
            if token.name not in seen:
                merged.append(token)
                seen.add(token.name)
        return merged

    def _merge_relations(self, existing: list, incoming: list) -> list:
        seen = {r.target_id for r in existing}
        merged = list(existing)
        for rel in incoming:
            if rel.target_id not in seen:
                merged.append(rel)
                seen.add(rel.target_id)
        return merged

    def _merge_events(self, existing: list, incoming: list) -> list:
        seen = {(e.timestamp.isoformat(), e.title) for e in existing}
        merged = list(existing)
        for event in incoming:
            key = (event.timestamp.isoformat(), event.title)
            if key not in seen:
                merged.append(event)
                seen.add(key)
        return sorted(merged, key=lambda e: e.timestamp)

    def _merge_conflicts(self, existing: list, incoming: list) -> list:
        seen_descriptions = {c.description for c in existing if not c.suppressed}
        merged = [c for c in existing if c.suppressed or c.user_intent.value > 0]
        for conflict in incoming:
            if conflict.description not in seen_descriptions:
                merged.append(conflict)
                seen_descriptions.add(conflict.description)
        return merged


__all__ = ["MergeEngine"]
