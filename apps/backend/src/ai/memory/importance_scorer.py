# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

"""Unified importance scorer (synchronous entry point).

Restored module (merge omission). Exposes :class:`ImportanceScorer` with a
synchronous ``calculate(content, metadata) -> float`` contract in ``[0, 1]``
that accepts arbitrary content types (str / int / list / dict).

The genuine multi-dimensional scoring logic lives in
``ai.memory.ham_memory.ham_importance_scorer``; this module is a thin,
synchronous facade over it so callers that need a plain ``float`` (no
``await``) can use the same engine.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

from ai.memory.ham_memory.ham_importance_scorer import (
    ImportanceScorer as _HamImportanceScorer,
)


class ImportanceScorer:
    """Synchronous importance scorer facade."""

    def __init__(self) -> None:
        self._scorer = _HamImportanceScorer()

    @staticmethod
    def _coerce(content: Any) -> str:
        """Normalize arbitrary content into a single searchable string."""
        if isinstance(content, str):
            return content
        if isinstance(content, (bool, int, float)):
            return str(content)
        if isinstance(content, (list, tuple, set)):
            return " ".join(ImportanceScorer._coerce(item) for item in content)
        if isinstance(content, dict):
            return " ".join(
                ImportanceScorer._coerce(value) for value in content.values()
            )
        return str(content)

    def calculate(self, content: Any, metadata: Dict[str, Any] = None) -> float:
        """Return importance score in ``[0, 1]`` for ``content`` + ``metadata``."""
        text = self._coerce(content)
        try:
            result = self._scorer.calculate(text, metadata or {})
            if hasattr(result, "__await__"):
                result = asyncio.run(result)
            score = float(result)
        except Exception as e:
            logger.debug(f"ImportanceScorer calculate failed: {e}", exc_info=True)
            return 0.0
        if score < 0.0:
            return 0.0
        if score > 1.0:
            return 1.0
        return score


__all__ = ["ImportanceScorer"]
