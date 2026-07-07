# -*- coding: utf-8 -*-
"""
Memory Integration - Extracted from AngelaLLMService
====================================================
Handles memory retrieval, precompute service management, and memory integration.

ANGELA-MATRIX: L3 [β] [A] [L0-L11]
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.interfaces.protocols import ChatResponse
    from services.llm.router import AngelaLLMService, LLMResponse

logger = logging.getLogger("angela_llm.memory")

# Lazy imports for memory enhancement types
_memory_modules_loaded = False
_MEMORY_ENHANCED = None
AngelaState = None
UserImpression = None
PrecomputeTask = None


def _load_memory_modules() -> str:
    """Lazy load memory enhancement modules on first access."""
    global _memory_modules_loaded, _MEMORY_ENHANCED
    global AngelaState, UserImpression, PrecomputeTask

    if _memory_modules_loaded:
        return _MEMORY_ENHANCED

    _memory_modules_loaded = True

    try:
        from ai.memory.memory_template import AngelaState as _AS
        from ai.memory.memory_template import UserImpression as _UI
        from ai.memory.precompute_service import PrecomputeTask as _PT

        AngelaState = _AS
        UserImpression = _UI
        PrecomputeTask = _PT

        _MEMORY_ENHANCED = True
        logger.info("Memory modules loaded for memory integration")
    except ImportError as e:
        logger.warning(
            "Memory modules not available for memory integration: %s", e, exc_info=True
        )
        _MEMORY_ENHANCED = False

    return _MEMORY_ENHANCED


def is_memory_enhanced():
    """Lazy check if memory enhancement is available."""
    if _MEMORY_ENHANCED is None:
        _load_memory_modules()
    return _MEMORY_ENHANCED


class MemoryIntegration:
    """Memory integration for AngelaLLMService - handles retrieval, precompute, and stats."""

    def __init__(self, service: "AngelaLLMService"):
        self._svc = service
        _load_memory_modules()

    async def try_memory_retrieval(
        self, user_message: str, context: Dict[str, Any]
    ) -> Optional["LLMResponse"]:
        """
        Try to retrieve a response from the memory system.

        Args:
            user_message: User message
            context: Conversation context

        Returns:
            Optional[LLMResponse]: Response if memory hit, None otherwise
        """
        from core.interfaces.protocols import ChatResponse

        try:
            if not hasattr(self._svc, 'memory_manager') or self._svc.memory_manager is None:
                return None

            results = await self._svc.memory_manager.retrieve_response_templates(
                query=user_message,
                limit=5,
                min_score=0.3,
            )

            if results and len(results) > 0:
                best_template, score = results[0]

                template_content = best_template.get("content", "")
                template_id = best_template.get("id", "unknown")

                if not template_content:
                    return None

                return ChatResponse(
                    text=template_content,
                    backend="memory-template",
                    model="template-based",
                    confidence=score,
                    hit_score=score,
                    hit_source="memory",
                    route="MEMORY",
                    metadata={
                        "template_id": template_id,
                        "template_score": score,
                        "memory_hit": True,
                    },
                )

            return None

        except Exception as e:
            logger.warning("Memory retrieval error: %s", e, exc_info=True)
            return None

    async def start_precompute(self) -> None:
        """Start the precompute service."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            await self._svc.precompute_service.start()
            logger.info("Precompute service started")

    async def stop_precompute(self) -> None:
        """Stop the precompute service."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            await self._svc.precompute_service.stop()
            logger.info("Precompute service stopped")

    async def add_precompute_task(self, task: "PrecomputeTask") -> bool:
        """Add a precompute task to the queue."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            return self._svc.precompute_service.add_precompute_task(task)
        return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        stats = {
            "enable_memory_enhancement": self._svc.enable_memory_enhancement,
            "llm_stats": self._svc.stats.copy(),
        }

        if self._svc.enable_memory_enhancement:
            if hasattr(self._svc, "precompute_service"):
                stats["precompute"] = self._svc.precompute_service.get_stats()
            if hasattr(self._svc, "template_library"):
                stats["templates"] = {
                    "total": self._svc.template_library.get_template_count(),
                    "by_category": {
                        cat.value: count
                        for cat, count in self._svc.template_library.get_category_counts().items()
                    },
                }

        if hasattr(self._svc, "template_matcher"):
            stats["template_matcher"] = self._svc.template_matcher.get_stats()

        if hasattr(self._svc, "response_composer"):
            stats["response_composer"] = self._svc.response_composer.get_stats()

        if hasattr(self._svc, "deviation_tracker"):
            stats["deviation_tracker"] = self._svc.deviation_tracker.get_stats()

        return stats

    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status."""
        active_backend_type = getattr(self._svc, "active_backend_type", None)
        if active_backend_type and self._svc.active_backend:
            active_backend_name = active_backend_type.value
        else:
            active_backend_name = None
        return {
            "is_available": self._svc.is_available,
            "active_backend": active_backend_name,
            "available_backends": [b.value for b in self._svc.backends.keys()],
            "backends_health": {},
        }
