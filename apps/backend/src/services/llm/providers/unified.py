# ANGELA-MATRIX: L3 [βγ] [B] [L2]
"""Unified Engine LLM backend provider — the single text-inference core.

Routes queries through the UnifiedEngine: deterministic math/logic (real
capabilities) first, then the fixed-size statistical core (real learned
generalisation). Replaces ED3N/GARDEN as the *text* inference entry point;
their multimodal branches (image/audio encoders) are untouched.
"""

import logging
import os
import re
import time
from typing import Any, Optional

from core.interfaces.protocols import LLMResponse
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class UnifiedBackend(BaseLLMBackend):
    """Unified Engine 後端 — fixed-size statistical core + deterministic layers."""

    def __init__(
        self,
        model: str = "unified-1g",
        checkpoint: str = "",
        timeout: float = 30.0,
    ):
        self.model = model
        self.checkpoint = checkpoint or self._resolve_default_checkpoint()
        self.timeout = timeout
        self._engine: Optional[Any] = None

    @staticmethod
    def _resolve_default_checkpoint() -> str:
        """Locate the trained ``data/checkpoints/unified/unified.json``.

        Resolution order:
          1. ``ANGELA_PROJECT_ROOT`` env override (explicit, unambiguous).
          2. Walk up from this module's dir to the dir containing
             ``apps/backend/src`` (bounded — this file lives at
             apps/backend/src/services/llm/providers/, 6 levels below root).
        """
        env_root = os.environ.get("ANGELA_PROJECT_ROOT", "").strip()
        if env_root:
            candidate = os.path.join(env_root, "data", "checkpoints", "unified", "unified.json")
            if os.path.isfile(candidate):
                return candidate
        here = os.path.abspath(os.path.dirname(__file__))
        root = here
        for _ in range(8):
            if os.path.isdir(os.path.join(root, "apps", "backend", "src")):
                break
            parent = os.path.dirname(root)
            if parent == root:
                break
            root = parent
        candidate = os.path.join(root, "data", "checkpoints", "unified", "unified.json")
        if os.path.isfile(candidate):
            return candidate
        return ""

    def _get_engine(self) -> Any:
        if self._engine is None:
            from ai.unified_engine.unified_engine import UnifiedEngine

            engine = UnifiedEngine(memory_cap_mb=2048)
            if self.checkpoint and os.path.isfile(self.checkpoint):
                engine.load(self.checkpoint)
                logger.info("unified backend: loaded checkpoint from %s", self.checkpoint)
            self._engine = engine
        return self._engine

    @staticmethod
    def _strip_wrapper(prompt: str) -> str:
        """Strip the <user_message>…</user_message> XML wrapper the shared
        prompt builder adds for LLM backends, so the statistical core matches
        against the user's real text (same issue ED3N had)."""
        m = re.search(r"<user_message>(.*?)</user_message>", prompt, re.DOTALL)
        if m:
            return m.group(1)
        return prompt

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.time()
        try:
            engine = self._get_engine()
            user_text = self._strip_wrapper(prompt)
            text = await self._run_in_thread(engine, user_text)
            if not text or text == user_text:
                # No deterministic rule matched and the statistical core had
                # nothing to say — let the caller fall through to a real LLM.
                return LLMResponse(
                    text="",
                    backend="unified",
                    model=self.model,
                    response_time_ms=(time.time() - start) * 1000,
                )
            elapsed_ms = (time.time() - start) * 1000
            return LLMResponse(
                text=text,
                backend="unified",
                model=self.model,
                tokens_used=0,
                response_time_ms=elapsed_ms,
                confidence=float(getattr(engine, "_last_confidence", 0.0) or 0.5),
                metadata={"route": engine._last_route},
            )
        except Exception as e:
            logger.error("unified backend error: %s", e, exc_info=True)
            return LLMResponse(text="", backend="unified", model=self.model, error=safe_error(e))

    async def _run_in_thread(self, engine: Any, user_text: str) -> str:
        import asyncio

        return await asyncio.to_thread(engine.process, user_text)

    async def check_health(self) -> bool:
        try:
            engine = self._get_engine()
            return engine is not None
        except Exception as e:
            logger.warning("unified health check failed: %s", e, exc_info=True)
            return False