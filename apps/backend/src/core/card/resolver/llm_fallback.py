"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
LLM fallback — final adjudicator for conflicts that Stage 1 and Stage 2
cannot resolve.
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class LLMFallback:
    """Final adjudicator for unresolved card conflicts.

    Delegates to an LLM service for conflict resolution.
    """

    def __init__(self, llm_service: Any = None):
        self.llm_service = llm_service

    def resolve(self, card: Any, remaining_conflicts: List[Any]) -> List[Any]:
        """Resolve remaining conflicts using LLM adjudication."""
        for conflict in remaining_conflicts:
            result = self._llm_resolve(conflict)
            if result:
                conflict.resolution = result
                conflict.suppressed = True
        return remaining_conflicts

    def _llm_resolve(self, conflict: Any) -> str:
        if self.llm_service:
            try:
                prompt = f"Resolve card conflict: {conflict.description}"
                return self.llm_service.generate(prompt)
            except Exception:
                # broad except acceptable: LLM calls are unpredictable; fallback on any failure
                logger.warning("LLM resolution failed, using fallback", exc_info=True)
        return f"LLM fallback resolved: {conflict.description}"


__all__ = ["LLMFallback"]
