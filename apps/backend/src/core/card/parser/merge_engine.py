"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Merge engine — cross-file merge by qualified_id with timestamp ordering.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from core.card.card_types import Card, SourceFile, Token

logger = logging.getLogger(__name__)


class MergeEngine:
    """
    Merges two Card objects by qualified_id, with newer source_files
    taking priority for name/core_trait and tokens/source_files combined.
    """

    def merge(self, existing: Optional[Card], incoming: Card) -> Card:
        """Merge incoming card into existing (or create new)."""
        if existing is None:
            return incoming

        result = Card(
            card_id=incoming.card_id or existing.card_id,
            world_line=incoming.world_line or existing.world_line,
            qualified_id=incoming.qualified_id or existing.qualified_id,
            name=self._pick_name(existing, incoming),
            core_trait=self._pick_core_trait(existing, incoming),
            tokens=self._combine_tokens(existing, incoming),
            source_files=self._combine_source_files(existing, incoming),
            alternate_selves=list(set(existing.alternate_selves + incoming.alternate_selves)),
            meta_data={**existing.meta_data, **incoming.meta_data},
        )
        return result

    def _pick_name(self, existing: Card, incoming: Card) -> str:
        if not incoming.name:
            return existing.name
        if not existing.name:
            return incoming.name
        return incoming.name

    def _pick_core_trait(self, existing: Card, incoming: Card) -> str:
        if not incoming.core_trait:
            return existing.core_trait
        if not existing.core_trait:
            return incoming.core_trait
        return incoming.core_trait

    def _combine_tokens(self, existing: Card, incoming: Card) -> list:
        seen: Dict[str, Token] = {}
        for t in existing.tokens:
            seen[t.name] = t
        for t in incoming.tokens:
            if t.name in seen:
                if t.strength > seen[t.name].strength:
                    seen[t.name] = t
            else:
                seen[t.name] = t
        return list(seen.values())

    def _combine_source_files(self, existing: Card, incoming: Card) -> list:
        seen: Dict[str, SourceFile] = {}
        for sf in existing.source_files:
            seen[sf.doc_id] = sf
        for sf in incoming.source_files:
            if sf.doc_id not in seen:
                seen[sf.doc_id] = sf
        return list(seen.values())


__all__ = ["MergeEngine"]
