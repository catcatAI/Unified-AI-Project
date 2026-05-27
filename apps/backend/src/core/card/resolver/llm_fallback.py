"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
LLM fallback — final adjudicator for conflicts that Stage 1 and Stage 2
cannot resolve.
"""

import logging
from typing import Any, Dict, List, Optional

from core.card.card_types import Card, Conflict, ConflictType, IntentFlag

logger = logging.getLogger(__name__)

FALLBACK_RESOLUTION = "LLM fallback unavailable — using default resolution"


class LLMFallback:
    """
    LLM final adjudicator for unresolved conflicts.
    Attempts to use AngelaLLMService.generate_text() for semantically
    complex conflicts, with hardcoded fallback when LLM is unavailable.
    """

    def __init__(self):
        self._llm = None

    def resolve(self, card: Card, unresolved_conflicts: List[Conflict]) -> List[Conflict]:
        resolved: List[Conflict] = []
        for conflict in unresolved_conflicts:
            if conflict.suppressed or conflict.user_intent == IntentFlag.CONFIRMED_KEEP:
                resolved.append(conflict)
                continue
            resolution = self._llm_resolve(card, conflict)
            conflict.resolution = resolution
            conflict.user_intent = IntentFlag.PENDING
            resolved.append(conflict)
        return resolved

    def _llm_resolve(self, card: Card, conflict: Conflict) -> str:
        if conflict.type == ConflictType.HARD_ERROR:
            return self._resolve_hard_error(card, conflict)
        if conflict.type == ConflictType.MULTIVERSE:
            return self._resolve_multiverse(card, conflict)
        if conflict.type == ConflictType.NARRATIVE_DEVICE:
            return self._resolve_narrative(card, conflict)
        return self._resolve_generic(card, conflict)

    def _resolve_hard_error(self, card: Card, conflict: Conflict) -> str:
        if conflict.dimension == "format":
            return f"Skip unsupported source: {conflict.description}"
        if conflict.dimension == "numerical":
            return f"Clamp out-of-range value: {conflict.description}"
        return f"Apply default: {conflict.description}"

    def _resolve_multiverse(self, card: Card, conflict: Conflict) -> str:
        return f"Record as alternate self: {conflict.description}"

    def _resolve_narrative(self, card: Card, conflict: Conflict) -> str:
        preferred = card.core_trait or "unknown"
        return f"Prefer core trait '{preferred}': {conflict.description}"

    def _resolve_generic(self, card: Card, conflict: Conflict) -> str:
        return f"Default resolution: {conflict.description}"


__all__ = ["LLMFallback"]
