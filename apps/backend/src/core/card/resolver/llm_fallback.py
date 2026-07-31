"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
LLM fallback — final adjudicator for conflicts that Stage 1 and Stage 2
cannot resolve.
"""

import asyncio
import concurrent.futures
import inspect
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
                result = self._generate_text(prompt)
                if result:
                    return result
            except Exception:
                # broad except acceptable: LLM calls are unpredictable; fallback on any failure
                logger.warning("LLM resolution failed, using fallback", exc_info=True)
        return f"LLM fallback resolved: {conflict.description}"

    def _generate_text(self, prompt: str) -> str:
        service = self.llm_service
        method = getattr(service, "generate_text", None)
        if method is None:
            method = getattr(service, "generate_response", None)
        if method is None:
            return ""
        try:
            asyncio.get_running_loop()
            in_loop = True
        except RuntimeError:
            in_loop = False

        def _run() -> Any:
            result = method(prompt)
            if inspect.isawaitable(result):
                result = asyncio.run(result)
            return result

        try:
            result = _run() if not in_loop else _run_in_thread(_run)
        except Exception as e:
            logger.warning("LLM text generation failed: %s", e, exc_info=True)
            return ""
        if isinstance(result, str):
            return result
        return getattr(result, "text", "") or (str(result) if result else "")


def _run_in_thread(fn: Any) -> Any:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(fn).result(timeout=60.0)


__all__ = ["LLMFallback"]
