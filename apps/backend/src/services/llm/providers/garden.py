# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""GARDEN-1G LLM backend provider for Angela's AngelaLLMService router."""

import logging
import os
import time
from typing import Any, Optional

from core.interfaces.protocols import LLMResponse
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class GARDENBackend(BaseLLMBackend):
    """
    GARDEN-1G 後端 — PyTorch 向量字典 + TensorSNN 輕量推理。
    掛載到 AngelaLLMService 的 LLMBackend 路由系統。
    """

    def __init__(
        self,
        model: str = "garden-1g",
        checkpoint: str = "",
        timeout: float = 30.0,
    ):
        self.model = model
        # When no explicit checkpoint is configured, fall back to the trained
        # checkpoint produced by scripts/train_pipeline.py so inference uses what
        # was actually trained (previously the engine loaded presets only,
        # orphaning the trained garden_checkpoint on disk).
        if not checkpoint:
            # Resolve the real project root (dir containing apps/backend/src)
            # and look for <root>/data/checkpoints/garden_checkpoint.
            here = os.path.abspath(os.path.dirname(__file__))
            root = here
            for _ in range(10):
                if os.path.isdir(os.path.join(root, "apps", "backend", "src")):
                    break
                parent = os.path.dirname(root)
                if parent == root:
                    break
                root = parent
            candidate = os.path.join(root, "data", "checkpoints", "garden_checkpoint")
            if os.path.isdir(candidate):
                checkpoint = candidate
        self.checkpoint = checkpoint
        self.timeout = timeout
        self._engine: Optional[Any] = None

    def _get_engine(self):
        if self._engine is None:
            from ai.garden.garden_engine import GARDENEngine

            engine = GARDENEngine(compatibility_mode=True)
            if self.checkpoint and os.path.isdir(self.checkpoint):
                engine.load(self.checkpoint)
                logger.info("GARDEN backend: loaded checkpoint from %s", self.checkpoint)
            else:
                engine.load_presets()
                logger.info("GARDEN backend: loaded presets")
            self._engine = engine
        return self._engine

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.time()
        try:
            engine = self._get_engine()
            context = kwargs.get("context")
            text = engine.process(prompt, context=context)
            if not text:
                text = "抱歉，我暂时无法理解你的意思。"
            elapsed_ms = (time.time() - start) * 1000
            return LLMResponse(
                text=text,
                backend="garden",
                model=self.model,
                tokens_used=0,
                response_time_ms=elapsed_ms,
                confidence=0.80,
            )
        except Exception as e:
            logger.error("GARDEN backend error: %s", e, exc_info=True)
            return LLMResponse(text="", backend="garden", model=self.model, error=safe_error(e))

    async def check_health(self) -> bool:
        try:
            engine = self._get_engine()
            return engine is not None
        except Exception as e:
            logger.debug("GARDEN health check failed: %s", e)
            return False
